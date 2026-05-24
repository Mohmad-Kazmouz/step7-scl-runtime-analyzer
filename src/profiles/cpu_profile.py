"""
cpu_profile.py – S7-300 CPU-Profil-Datenmodell

Ein CPU-Profil enthält die Ausführungszeiten (in Nanosekunden) für
jeden IR-Opcode sowie Speicherzugriffszeiten auf der Ziel-CPU.
Profile werden als JSON-Dateien unter profiles/s7_300/ gespeichert.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pydantic import BaseModel
from ..ir.ir_nodes import IROpcode
from ..semantic.symbol_table import StorageLocation


class InstructionTiming(BaseModel):
    """Ausführungszeit eines IR-Opcodes in Nanosekunden."""
    opcode: str
    latency_ns: float


class StorageAccessTiming(BaseModel):
    """Lese-/Schreibzeit eines Speicherbereichs in Nanosekunden."""
    location: str
    read_ns: float
    write_ns: float


class CPUProfileModel(BaseModel):
    """Pydantic-Modell zur Validierung der JSON-Profildatei."""
    name: str
    description: str
    clock_mhz: float
    instructions: list[InstructionTiming]
    storage_access: list[StorageAccessTiming]


class CPUProfile:
    """
    Laufzeit-Wrapper um das geladene CPU-Profil.
    Bietet schnellen Zugriff auf Latenzen per Opcode / StorageLocation.

    Verwendung::

        profile = ProfileLoader().load("S7-300-CPU315-2DP")
        ns = profile.get_instruction_latency(IROpcode.MUL)
        r, w = profile.get_access_times(StorageLocation.INSTANCE_DB)
    """

    def __init__(self, model: CPUProfileModel) -> None:
        self._model = model
        self._instr_map: dict[str, float] = {
            t.opcode: t.latency_ns for t in model.instructions
        }
        self._storage_map: dict[str, tuple[float, float]] = {
            t.location: (t.read_ns, t.write_ns) for t in model.storage_access
        }

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def clock_mhz(self) -> float:
        return self._model.clock_mhz

    def get_instruction_latency(self, opcode: IROpcode) -> float:
        """Gibt die Ausführungszeit des Opcodes in ns zurück (0.0 wenn unbekannt)."""
        return self._instr_map.get(opcode.name, 0.0)

    def get_access_times(self, location: StorageLocation) -> tuple[float, float]:
        """Gibt (read_ns, write_ns) für den Speicherbereich zurück."""
        return self._storage_map.get(location.name, (0.0, 0.0))

    def __repr__(self) -> str:
        return f"CPUProfile({self._model.name}, {self._model.clock_mhz}MHz)"
