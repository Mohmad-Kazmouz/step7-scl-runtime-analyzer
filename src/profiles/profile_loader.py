"""
profile_loader.py – Lädt S7-300 CPU-Profile aus JSON-Dateien
"""
from __future__ import annotations
from pathlib import Path
import json
from .cpu_profile import CPUProfile, CPUProfileModel

_DEFAULT_PROFILES_DIR = Path(__file__).parent.parent.parent / "profiles" / "s7_300"


class ProfileLoader:
    """
    Sucht und lädt CPU-Profile aus dem profiles/s7_300/-Verzeichnis.

    Verwendung::

        loader = ProfileLoader()
        profile = loader.load("S7-300-CPU315-2DP")
        print(loader.list_available())
    """

    def __init__(self, profiles_dir: Path | None = None) -> None:
        self._dir = profiles_dir or _DEFAULT_PROFILES_DIR

    def list_available(self) -> list[str]:
        """Gibt Namen aller verfügbaren CPU-Profile zurück."""
        return [p.stem for p in self._dir.glob("*.json")]

    def load(self, name: str) -> CPUProfile:
        """
        Lädt ein CPU-Profil anhand seines Namens.

        :param name: Profilname (z.B. 'S7-300-CPU315-2DP')
        :raises FileNotFoundError: Profil nicht gefunden
        :raises ValueError: JSON-Validierung fehlgeschlagen
        """
        path = self._dir / f"{name}.json"
        if not path.exists():
            available = ", ".join(self.list_available()) or "keine"
            raise FileNotFoundError(
                f"CPU-Profil '{name}' nicht gefunden.\n"
                f"Verfügbare Profile: {available}"
            )
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        model = CPUProfileModel(**data)
        return CPUProfile(model)
