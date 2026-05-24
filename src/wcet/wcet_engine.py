"""
wcet_engine.py – WCET-Berechnung

Koordiniert CFG-Analyse und gibt WCET/BCET sowie Pass/Fail zurück.
"""
from __future__ import annotations
from dataclasses import dataclass
from ..cfg.cfg_graph import CFGGraph


@dataclass
class WCETResult:
    """Ergebnis einer WCET-Analyse."""
    fb_name: str
    wcet_ns: float          # Worst-Case Execution Time in Nanosekunden
    bcet_ns: float          # Best-Case Execution Time in Nanosekunden
    cycle_time_ns: float    # Konfigurierte Zykluszeit in Nanosekunden
    critical_path_blocks: list  # IRBlock-Objekte auf dem kritischen Pfad

    @property
    def wcet_ms(self) -> float:
        return self.wcet_ns / 1_000_000

    @property
    def bcet_ms(self) -> float:
        return self.bcet_ns / 1_000_000

    @property
    def cycle_time_ms(self) -> float:
        return self.cycle_time_ns / 1_000_000

    @property
    def safety_margin_pct(self) -> float:
        """Verbleibender Puffer als Prozentsatz der Zykluszeit."""
        if self.cycle_time_ns <= 0:
            return 0.0
        return (1.0 - self.wcet_ns / self.cycle_time_ns) * 100.0

    @property
    def passed(self) -> bool:
        """True wenn WCET innerhalb der Zykluszeit liegt."""
        return self.wcet_ns <= self.cycle_time_ns

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"WCET={self.wcet_ms:.3f}ms  "
            f"BCET={self.bcet_ms:.3f}ms  "
            f"Zykluszeit={self.cycle_time_ms:.1f}ms  "
            f"Puffer={self.safety_margin_pct:.1f}%  [{status}]"
        )


class WCETEngine:
    """
    Berechnet WCET und BCET aus dem CFG.

    Verwendung::

        engine = WCETEngine(cycle_time_ms=10.0)
        result = engine.analyze(cfg, fb_name="FB10_Regelung")
    """

    def __init__(self, cycle_time_ms: float) -> None:
        """
        :param cycle_time_ms: Konfigurierte SPS-Zykluszeit in Millisekunden
        """
        self._cycle_ns = cycle_time_ms * 1_000_000

    def analyze(self, cfg: CFGGraph, fb_name: str) -> WCETResult:
        """
        Führt die WCET/BCET-Analyse durch.

        :param cfg:     Kontrollflussgraph (Schleifen bereits aufgelöst)
        :param fb_name: Name des Funktionsbausteins
        :return:        WCETResult mit allen Kennzahlen
        """
        critical_path = cfg.find_critical_path()
        wcet_ns = sum(b.total_latency_ns for b in critical_path)
        bcet_ns = self._compute_bcet(cfg)

        return WCETResult(
            fb_name=fb_name,
            wcet_ns=wcet_ns,
            bcet_ns=bcet_ns,
            cycle_time_ns=self._cycle_ns,
            critical_path_blocks=critical_path,
        )

    def _compute_bcet(self, cfg: CFGGraph) -> float:
        """
        BCET = kürzester Pfad durch den CFG.
        Vereinfachung: Summe der minimalen Blocklatenz aller Blöcke auf dem
        kürzesten Pfad (Dijkstra mit negativierten Gewichten).
        """
        import networkx as nx
        g = cfg.graph
        if len(g) == 0:
            return 0.0
        nodes = list(g.nodes)
        source = nodes[0]
        sinks  = [n for n in g.nodes if g.out_degree(n) == 0]
        if not sinks:
            return 0.0

        # Kürzester Pfad über alle Senken
        bcet = float("inf")
        for sink in sinks:
            try:
                length = nx.shortest_path_length(
                    g, source=source, target=sink, weight="latency_ns"
                )
                bcet = min(bcet, length)
            except nx.NetworkXNoPath:
                pass
        return bcet if bcet != float("inf") else 0.0
