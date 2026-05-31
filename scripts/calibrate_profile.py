"""
calibrate_profile.py – CPU-Profil kalibrieren

Vergleicht Analyzer-Schätzungen mit echten Hardware-Messwerten
und passt Latenzen im Profil proportional an.

Verwendung:
    python scripts/calibrate_profile.py --profile S7-300-CPU315-2DP \\
        --measurements measurements.json [--output adjusted_profile.json]
"""

import json
import sys
from pathlib import Path


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="CPU-Profil mit realen Hardware-Messungen kalibrieren"
    )
    parser.add_argument(
        "--profile", required=True, help="CPU-Profilname (z.B. S7-300-CPU315-2DP)"
    )
    parser.add_argument(
        "--measurements",
        required=True,
        type=Path,
        help="JSON-Datei mit [{fb_name, measured_ms}] Paaren",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Ausgabepfad für das kalibrierte Profil (Standard: <profilname>_calibrated.json)",
    )
    args = parser.parse_args()

    # Profil laden
    profiles_dir = Path(__file__).parent.parent / "profiles" / "s7_300"
    profile_path = profiles_dir / f"{args.profile}.json"
    if not profile_path.exists():
        print(f"Fehler: Profil '{args.profile}' nicht gefunden unter {profile_path}")
        sys.exit(1)

    with profile_path.open(encoding="utf-8") as f:
        profile_data = json.load(f)

    # Messungen laden
    measurements = json.loads(args.measurements.read_text(encoding="utf-8"))
    if not measurements:
        print("Fehler: Keine Messwerte in der Messdatei.")
        sys.exit(1)

    # Erwartete Format: [{"fb_name": "FB_Test", "measured_ms": 1.234}, ...]
    if isinstance(measurements, dict):
        # Auch dict-Format {fb_name: measured_ms} unterstützen
        measurements = [
            {"fb_name": k, "measured_ms": v} for k, v in measurements.items()
        ]

    print(f"Kalibriere Profil '{args.profile}' mit {len(measurements)} Messungen...")

    # Jede Messung: Analyzer aufrufen, Schätzung mit Messung vergleichen,
    # Skalierungsfaktor berechnen
    from click.testing import CliRunner

    from src.cli.main import cli as _cli

    runner = CliRunner()
    total_factor = 0.0
    valid_count = 0

    for m in measurements:
        fb_name = m["fb_name"]
        measured_ms = m["measured_ms"]

        # FB-Datei finden (im gleichen Verzeichnis wie measurements oder tests/fixtures)
        fb_path = find_fb_file(fb_name)

        if not fb_path:
            print(f"  [Übersprungen] FB '{fb_name}' nicht gefunden")
            continue

        # Analyzer ausführen
        result = runner.invoke(
            _cli,
            [
                "analyze",
                str(fb_path),
                "--cpu",
                args.profile,
                "--cycle-time",
                "999999ms",  # Große Zykluszeit, damit immer PASS
                "--export",
                "json",
                "--output",
                str(Path("/tmp") / f"_calib_{fb_name}.json"),
            ],
        )

        if result.exit_code != 0:
            print(f"  [Fehler] Analyse von '{fb_name}' fehlgeschlagen")
            continue

        # Geschätzte WCET aus dem JSON-Export lesen
        output_file = Path("/tmp") / f"_calib_{fb_name}.json"
        if output_file.exists():
            est = json.loads(output_file.read_text(encoding="utf-8"))
            estimated_ms = est.get("wcet_ms", 0.0)
            output_file.unlink()  # Aufräumen
        else:
            print(f"  [Fehler] Kein Analyse-Output für '{fb_name}'")
            continue

        if estimated_ms <= 0 or measured_ms <= 0:
            print(
                f"  [Übersprungen] FB '{fb_name}': ungültige Werte (est={estimated_ms}, meas={measured_ms})"
            )
            continue

        factor = measured_ms / estimated_ms
        total_factor += factor
        valid_count += 1
        print(
            f"  FB '{fb_name}': {estimated_ms:.4f}ms (geschätzt) vs {measured_ms:.4f}ms (gemessen) → Faktor {factor:.4f}"
        )

    if valid_count == 0:
        print("Fehler: Keine gültigen Messungen zur Kalibrierung.")
        sys.exit(1)

    # Durchschnittlichen Skalierungsfaktor berechnen
    avg_factor = total_factor / valid_count
    print(f"\nDurchschnittlicher Skalierungsfaktor: {avg_factor:.4f}")

    # Alle Latenzen im Profil mit dem Faktor multiplizieren
    for instr in profile_data["instructions"]:
        instr["latency_ns"] = round(instr["latency_ns"] * avg_factor, 1)

    for sa in profile_data["storage_access"]:
        sa["read_ns"] = round(sa["read_ns"] * avg_factor, 1)
        sa["write_ns"] = round(sa["write_ns"] * avg_factor, 1)

    # Optional: Beschreibung ergänzen
    profile_data["description"] = (
        profile_data.get("description", "")
        + f" (kalibriert mit Faktor {avg_factor:.4f}, {valid_count} Messungen)"
    )

    # Ausgabe
    output_path = args.output or (profiles_dir / f"{args.profile}_calibrated.json")
    output_path.write_text(
        json.dumps(profile_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Kalibriertes Profil gespeichert: {output_path}")


def find_fb_file(fb_name: str) -> Path | None:
    """Sucht eine SCL-Datei für den gegebenen FB-Namen."""
    # Suchpfade
    search_dirs = [
        Path.cwd(),
        Path(__file__).parent.parent / "tests" / "fixtures" / "scl_samples",
    ]
    for d in search_dirs:
        candidate = d / f"{fb_name}.scl"
        if candidate.exists():
            return candidate
    return None


if __name__ == "__main__":
    main()
