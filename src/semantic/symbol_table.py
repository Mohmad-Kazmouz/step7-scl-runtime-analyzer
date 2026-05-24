"""
symbol_table.py – Symboltabelle für SCL-Funktionsbausteine

Ordnet jeden Bezeichner seinem Typ, seiner Speicherklasse und seiner
Zugriffszeit auf der S7-300-Hardware zu.
Die Zugriffszeit ist entscheidend für die WCET-Berechnung:
  - Lokalstack (L)  : schnellster Zugriff
  - Merker (M)      : mittel
  - Datenbaustein DB: am langsamsten
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto


class SymbolKind(Enum):
    """Art des Bezeichners."""
    VAR_INPUT   = auto()   # Eingangsparameter
    VAR_OUTPUT  = auto()   # Ausgangsparameter
    VAR_IN_OUT  = auto()   # Durchgangsparameter
    VAR_LOCAL   = auto()   # Lokale Variable (VAR)
    VAR_TEMP    = auto()   # Temporäre Variable (VAR_TEMP)
    CONSTANT    = auto()   # Konstante


class StorageLocation(Enum):
    """
    Speicherort auf der S7-300.
    Bestimmt die Zugriffszeit in Taktzyklen (aus CPU-Profil).
    """
    LOCAL_STACK = auto()   # VAR_TEMP → Lokalstack (L-Bereich)
    INSTANCE_DB = auto()   # VAR, VAR_INPUT, VAR_OUTPUT → Instanz-DB
    SHARED_DB   = auto()   # Expliziter DB-Zugriff (DB1.DBW0)
    MERKER      = auto()   # Merker (M-Bereich)
    INPUT       = auto()   # Prozessabbild Eingang (E/I)
    OUTPUT      = auto()   # Prozessabbild Ausgang (A/Q)


@dataclass
class Symbol:
    """Ein Eintrag in der Symboltabelle."""
    name: str
    type_name: str
    kind: SymbolKind
    storage: StorageLocation
    # Zugriffszeit in Nanosekunden – wird aus dem CPU-Profil befüllt
    read_time_ns: float = 0.0
    write_time_ns: float = 0.0
    line_declared: int = 0


class SymbolTable:
    """
    Verwaltet alle Symbole eines Funktionsbausteins.

    Beispiel::

        table = SymbolTable()
        table.define(Symbol("iSpeed", "INT", SymbolKind.VAR_INPUT,
                            StorageLocation.INSTANCE_DB))
        sym = table.resolve("iSpeed")
    """

    def __init__(self) -> None:
        self._symbols: dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> None:
        """Fügt ein Symbol hinzu. Überschreibt bei gleichem Namen (letzte Deklaration gewinnt)."""
        self._symbols[symbol.name.upper()] = symbol

    def resolve(self, name: str) -> Symbol | None:
        """Sucht ein Symbol nach Namen (case-insensitiv). Gibt None zurück wenn nicht gefunden."""
        return self._symbols.get(name.upper())

    def all_symbols(self) -> list[Symbol]:
        """Gibt alle Symbole als Liste zurück."""
        return list(self._symbols.values())

    def __len__(self) -> int:
        return len(self._symbols)

    def __repr__(self) -> str:
        return f"SymbolTable({len(self)} Symbole)"
