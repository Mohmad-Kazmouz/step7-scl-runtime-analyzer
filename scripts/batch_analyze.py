"""
batch_analyze.py – Batch-Analyse mehrerer SCL-FB-Dateien

Verwendung:
    python scripts/batch_analyze.py ./scl_files/ --cpu S7-300-CPU315-2DP --cycle-time 10ms
"""
import sys
import json
from pathlib import Path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch-WCET-Analyse für SCL-FB-Dateien")
    parser.add_argument("directory", type=Path, help="Verzeichnis mit SCL-Dateien")
    parser.add_argument("--cpu",          required=True)
    parser.add_argument("--cycle-time",   required=True)
    parser.add_argument("--output-dir",   type=Path, default=Path("./batch_results"))
    args = parser.parse_args()

    scl_files = list(args.directory.glob("*.scl"))
    if not scl_files:
        print(f"Keine .scl-Dateien gefunden in: {args.directory}")
        sys.exit(1)

    args.output_dir.mkdir(exist_ok=True)
    summary = []

    for scl_file in sorted(scl_files):
        # Ruft das CLI-Kommando programmatisch auf
        from src.cli.main import cli
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, [
            "analyze", str(scl_file),
            "--cpu", args.cpu,
            "--cycle-time", args.cycle_time,
            "--export", "json",
            "--output", str(args.output_dir / f"{scl_file.stem}.json"),
        ])
        passed = result.exit_code == 0
        summary.append({"fb": scl_file.stem, "passed": passed})
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}]  {scl_file.name}")

    # Zusammenfassung
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    total  = len(summary)
    passed = sum(1 for s in summary if s["passed"])
    print(f"\nErgebnis: {passed}/{total} bestanden")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
