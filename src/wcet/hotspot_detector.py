"""
hotspot_detector.py – Hotspot-Erkennung

Identifiziert Codeblöcke, die mehr als einen konfigurierbaren Anteil
(Standard: 10%) der WCET verursachen, und gibt Optimierungshinweise.
"""
from __future__ import annotations
from dataclasses import dataclass
from ..ir.ir_nodes import IRBlock


@dataclass
class Hotspot:
    """Beschreibt einen einzelnen Laufzeit-Hotspot."""
    block_id: str
    source_line_start: int
    source_line_end: int
    latency_ns: float
    share_pct: float            # Anteil an der Gesamt-WCET
    hint: str                   # Optimierungshinweis


class HotspotDetector:
    """
    Analysiert die kritischen IRBlöcke und liefert priorisierte Hotspot-Liste.

    Verwendung::

        detector = HotspotDetector(threshold_pct=10.0)
        hotspots = detector.detect(critical_path_blocks, wcet_ns)
    """

    def __init__(self, threshold_pct: float = 10.0) -> None:
        """
        :param threshold_pct: Mindestanteil (%) an der WCET, ab dem ein Block
                              als Hotspot gilt. Standard: 10%
        """
        self._threshold = threshold_pct

    def detect(self, blocks: list[IRBlock], wcet_ns: float) -> list[Hotspot]:
        """
        Erkennt Hotspots im kritischen Pfad.

        :param blocks:  IRBlöcke auf dem kritischen Pfad
        :param wcet_ns: Gesamte WCET in Nanosekunden
        :return:        Priorisierte Liste von Hotspot-Objekten (absteigende Latenz)
        """
        hotspots: list[Hotspot] = []
        for block in blocks:
            if wcet_ns <= 0:
                continue
            share = (block.total_latency_ns / wcet_ns) * 100.0
            if share >= self._threshold:
                lines = [i.source_line for i in block.instructions if i.source_line > 0]
                hotspots.append(Hotspot(
                    block_id=block.block_id,
                    source_line_start=min(lines) if lines else 0,
                    source_line_end=max(lines) if lines else 0,
                    latency_ns=block.total_latency_ns,
                    share_pct=share,
                    hint=self._generate_hint(block),
                ))
        hotspots.sort(key=lambda h: h.latency_ns, reverse=True)
        return hotspots

    def _generate_hint(self, block: IRBlock) -> str:
        """Erzeugt einen kontextbezogenen Optimierungshinweis."""
        from ..ir.ir_nodes import IROpcode
        opcodes = {i.opcode for i in block.instructions}

        if IROpcode.SQRT in opcodes or IROpcode.SIN in opcodes or IROpcode.COS in opcodes:
            return ("Mathematische Funktionen (SQRT/SIN/COS) sind auf der S7-300 sehr langsam. "
                    "Vorberechnung oder Lookup-Tabellen in Betracht ziehen.")
        if IROpcode.DIV in opcodes:
            return ("Division ist teuer. Falls möglich, durch Multiplikation mit "
                    "reziprokem Wert ersetzen oder als DINT berechnen.")
        if IROpcode.MUL in opcodes:
            return ("Viele Multiplikationen im Block. Bei REAL-Operanden ist DINT "
                    "auf der S7-300 bis zu 3x schneller.")
        if any(op in opcodes for op in (IROpcode.LOAD, IROpcode.STORE)):
            return ("Intensiver DB-Zugriff. Werte in VAR_TEMP-Variablen (Lokalstack) "
                    "zwischenspeichern reduziert DB-Zugriffszeiten erheblich.")
        return "Block auf dem kritischen Pfad. Schleifenstruktur oder Berechnungen prüfen."
