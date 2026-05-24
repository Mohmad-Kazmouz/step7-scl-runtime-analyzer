"""
ir_nodes.py – Knoten der Intermediate Representation

Die IR normalisiert alle SCL-Konstrukte auf eine flache Liste von
IRInstruction-Objekten, die direkt den S7-300-Maschinenbefehlen
entsprechen und Laufzeiten aus dem CPU-Profil erhalten.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto


class IROpcode(Enum):
    """Abstrakter Befehlssatz – entspricht grob S7-300 STL-Gruppen."""
    # Datentransfer
    LOAD        = auto()   # Wert laden (aus DB, Merker, Lokalstack)
    STORE       = auto()   # Wert speichern
    # Arithmetik
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    DIV         = auto()
    MOD         = auto()
    # Vergleich
    CMP_EQ      = auto()
    CMP_NE      = auto()
    CMP_LT      = auto()
    CMP_LE      = auto()
    CMP_GT      = auto()
    CMP_GE      = auto()
    # Logik
    AND         = auto()
    OR          = auto()
    XOR         = auto()
    NOT         = auto()
    # Sprung / Kontrolle
    JUMP        = auto()   # unbedingter Sprung
    JUMP_IF     = auto()   # bedingter Sprung (wahr)
    JUMP_UNLESS = auto()   # bedingter Sprung (falsch)
    LABEL       = auto()   # Sprungziel
    CALL        = auto()   # FB/FC-Aufruf
    RETURN      = auto()
    # Mathematische Funktionen (S7-300 Sonderzeit)
    SQRT        = auto()
    ABS         = auto()
    SIN         = auto()
    COS         = auto()
    # Konvertierung
    CONV        = auto()   # Typkonvertierung (INT→REAL, etc.)
    # Bit-Operationen
    SHL         = auto()
    SHR         = auto()
    ROL         = auto()
    ROR         = auto()


@dataclass
class IRInstruction:
    """
    Eine einzelne IR-Anweisung.

    :param opcode:      Befehlstyp
    :param operands:    Liste der Operanden (Symbolnamen oder Literale)
    :param result:      Zielregister / Zielvariable (optional)
    :param source_line: Ursprungszeile im SCL-Quelltext (für Hotspot-Rückverfolgung)
    :param latency_ns:  Ausführungszeit auf der Ziel-CPU (wird aus CPU-Profil befüllt)
    """
    opcode: IROpcode
    operands: list[str] = field(default_factory=list)
    result: str | None = None
    source_line: int = 0
    latency_ns: float = 0.0

    def __repr__(self) -> str:
        res = f"{self.result} = " if self.result else ""
        ops = ", ".join(self.operands)
        return f"{res}{self.opcode.name}({ops})  [{self.latency_ns:.1f}ns @ L{self.source_line}]"


@dataclass
class IRBlock:
    """
    Basisblock: zusammenhängende IR-Folge ohne Sprünge im Inneren.
    Entspricht einem Knoten im Control Flow Graph.
    """
    block_id: str
    instructions: list[IRInstruction] = field(default_factory=list)
    successors: list[str] = field(default_factory=list)   # block_id der Nachfolger

    @property
    def total_latency_ns(self) -> float:
        """Summe der Latenzen aller Befehle im Block."""
        return sum(i.latency_ns for i in self.instructions)

    def __repr__(self) -> str:
        return (f"IRBlock({self.block_id}, "
                f"{len(self.instructions)} instr, "
                f"{self.total_latency_ns:.1f}ns)")
