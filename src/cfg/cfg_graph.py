"""
cfg_graph.py – Kontrollflussgraph (CFG)

Gerichteter Graph der IR-Basisblöcke. Kanten repräsentieren
mögliche Ausführungsübergänge (bedingt oder unbedingt).
Grundlage für die WCET-Analyse (kritischer Pfad).
"""
from __future__ import annotations
from dataclasses import dataclass, field
import networkx as nx
from ..ir.ir_nodes import IRBlock


class CFGGraph:
    """
    Wrapper um einen networkx DiGraph mit Annotationen pro Knoten (IRBlock).

    Verwendung::

        cfg = CFGGraph()
        cfg.add_block(block)
        cfg.add_edge("entry", "loop_0")
        path = cfg.find_critical_path()
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_block(self, block: IRBlock) -> None:
        """Fügt einen IR-Basisblock als Knoten hinzu."""
        self._graph.add_node(
            block.block_id,
            block=block,
            latency_ns=block.total_latency_ns,
        )

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Fügt eine Kontrollflusskante hinzu."""
        self._graph.add_edge(from_id, to_id)

    def find_critical_path(self) -> list[IRBlock]:
        """
        Berechnet den kritischen Pfad (maximale kumulierte Latenz)
        vom Eingangs- zum Ausgangsknoten mittels longest-path-Algorithmus.

        :return: Liste von IRBlock-Objekten auf dem kritischen Pfad
        :raises nx.NetworkXUnfeasible: bei Zyklen ohne Schranke
        """
        if not nx.is_directed_acyclic_graph(self._graph):
            # Schleifen werden für WCET mit maximaler Iterationszahl aufgelöst
            raise ValueError(
                "CFG enthält Zyklen. Schleifen müssen vor der Pfadsuche "
                "durch den LoopBoundAnnotator aufgelöst werden."
            )
        path_ids = nx.dag_longest_path(
            self._graph,
            weight="latency_ns",
        )
        return [self._graph.nodes[n]["block"] for n in path_ids]

    def total_wcet_ns(self) -> float:
        """Gibt die Summe der Latenzen auf dem kritischen Pfad zurück."""
        return sum(b.total_latency_ns for b in self.find_critical_path())

    @property
    def graph(self) -> nx.DiGraph:
        """Direktzugriff auf den networkx-Graphen (für Visualisierung)."""
        return self._graph

    def __len__(self) -> int:
        return len(self._graph)
