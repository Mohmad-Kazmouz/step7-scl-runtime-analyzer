"""
cfg_graph.py – Kontrollflussgraph (CFG)

Gerichteter Graph der IR-Basisblöcke. Kanten repräsentieren
mögliche Ausführungsübergänge (bedingt oder unbedingt).
Grundlage für die WCET-Analyse (kritischer Pfad).
"""
from __future__ import annotations

import networkx as nx

from ..ir.ir_nodes import IRBlock


class CFGGraph:
    """
    Wrapper um einen networkx DiGraph mit Annotationen pro Knoten (IRBlock).

    Pfadgewichte basieren auf der Summe der Blocklatenzen (Knotenattribute),
    nicht auf Kanten — S7-Kontrollfluss modelliert Kosten pro Basisblock.
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

    def _source_node(self) -> str:
        nodes = list(self._graph.nodes)
        if not nodes:
            raise ValueError("CFG ist leer")
        return nodes[0]

    def _sink_nodes(self) -> list[str]:
        return [n for n in self._graph.nodes if self._graph.out_degree(n) == 0]

    def _extreme_latency_path(self, *, maximize: bool) -> list[IRBlock]:
        """Berechnet einen Pfad mit maximaler/minimaler Summe der Blocklatenzen."""
        g = self._graph
        if len(g) == 0:
            return []

        if not nx.is_directed_acyclic_graph(g):
            raise ValueError(
                "CFG enthält Zyklen. Schleifen müssen vor der Pfadsuche "
                "durch den LoopBoundAnnotator aufgelöst werden."
            )

        order = list(nx.topological_sort(g))
        source = self._source_node()
        sinks = self._sink_nodes()
        if not sinks:
            return []

        inf = float("inf")
        neg_inf = float("-inf")
        best: dict[str, float] = {
            n: (neg_inf if maximize else inf) for n in order
        }
        best[source] = g.nodes[source]["latency_ns"]
        prev: dict[str, str] = {}

        for node in order:
            base = best[node]
            if base == (neg_inf if maximize else inf):
                continue
            for succ in g.successors(node):
                candidate = base + g.nodes[succ]["latency_ns"]
                if maximize:
                    if candidate > best[succ]:
                        best[succ] = candidate
                        prev[succ] = node
                elif candidate < best[succ]:
                    best[succ] = candidate
                    prev[succ] = node

        if maximize:
            target = max(sinks, key=lambda s: best[s])
            if best[target] == -inf:
                raise ValueError("Kein gültiger Pfad vom Einstieg zum Austritt")
        else:
            target = min(sinks, key=lambda s: best[s])
            if best[target] == inf:
                raise ValueError("Kein gültiger Pfad vom Einstieg zum Austritt")

        path_ids: list[str] = []
        cur: str | None = target
        while cur is not None:
            path_ids.append(cur)
            cur = prev.get(cur)
        path_ids.reverse()
        return [g.nodes[n]["block"] for n in path_ids]

    def find_critical_path(self) -> list[IRBlock]:
        """Pfad mit maximaler kumulierter Blocklatenz (WCET)."""
        return self._extreme_latency_path(maximize=True)

    def find_best_case_path(self) -> list[IRBlock]:
        """Pfad mit minimaler kumulierter Blocklatenz (BCET)."""
        return self._extreme_latency_path(maximize=False)

    def total_wcet_ns(self) -> float:
        """Summe der Latenzen auf dem kritischen Pfad."""
        return sum(b.total_latency_ns for b in self.find_critical_path())

    @property
    def graph(self) -> nx.DiGraph:
        """Direktzugriff auf den networkx-Graphen (für Visualisierung)."""
        return self._graph

    def __len__(self) -> int:
        return len(self._graph)
