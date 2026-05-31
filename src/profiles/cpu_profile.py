"""
cpu_profile.py – S7-300 CPU-Profil-Datenmodell

Ein CPU-Profil enthält die Ausführungszeiten (in Nanosekunden) für
jeden IR-Opcode sowie Speicherzugriffszeiten auf der Ziel-CPU.
Profile werden als JSON-Dateien unter profiles/s7_300/ gespeichert.
"""

from __future__ import annotations

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
    instruction_list_doc: str | None = None
    order_number: str | None = None
    storage_access_source: str | None = None
    typed_opcode_source: str | None = None


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

    def get_instruction_latency(
        self, opcode: IROpcode, scl_type: str | None = None
    ) -> float:
        """Gibt die Ausführungszeit des Opcodes in ns zurück (0.0 wenn unbekannt).

        Für arithmetische und Vergleichsoperationen kann ``scl_type`` (REAL, DINT, …)
        übergeben werden; es wird dann zuerst nach typisierten Einträgen wie
        ``ADD_REAL`` im Profil gesucht.
        """
        if scl_type:
            key = self._typed_opcode_key(opcode.name, scl_type)
            if key is not None and key in self._instr_map:
                return self._instr_map[key]

        lat = self._instr_map.get(opcode.name)
        if lat is None:
            import warnings

            warnings.warn(
                f"Opcode '{opcode.name}' nicht im CPU-Profil '{self.name}' gefunden. "
                f"Latenz wird mit 0.0 ns angenommen — WCET kann unterschätzt sein!"
            )
            return 0.0
        return lat

    @staticmethod
    def _typed_opcode_key(base_opcode: str, scl_type: str) -> str | None:
        """Mappt SCL-Typ auf Profil-Suffix (ADD + REAL → ADD_REAL)."""
        t = scl_type.upper()
        if t in ("REAL", "LREAL"):
            suffix = "REAL"
        elif t in ("DINT", "UDINT", "DWORD", "TIME", "DATE", "DT", "TIME_OF_DAY"):
            suffix = "DINT"
        else:
            return None
        key = f"{base_opcode}_{suffix}"
        return key

    def get_access_times(self, location: StorageLocation) -> tuple[float, float]:
        """Gibt (read_ns, write_ns) für den Speicherbereich zurück."""
        return self._storage_map.get(location.name, (0.0, 0.0))

    def __repr__(self) -> str:
        return f"CPUProfile({self._model.name}, {self._model.clock_mhz}MHz)"
