"""
loop_bound.py – Schleifen-Schranken-Annotierung

Schleifenzyklen im CFG werden für die WCET-Analyse aufgelöst,
indem FOR-Schleifen mit statischen Grenzen direkt expandiert und
WHILE/REPEAT-Schleifen mit einer konfigurierbaren maximalen
Iterationszahl annotiert werden.
"""
from __future__ import annotations
import copy
import networkx as nx
from ..parser.ast_nodes import ForNode, WhileNode, RepeatNode, LiteralNode
from ..cfg.cfg_graph import CFGGraph


DEFAULT_MAX_ITERATIONS = 100  # Konservative Schranke für unbekannte Schleifen


class LoopBoundAnnotator:
    """
    Löst Schleifenzyklen im CFG auf, um einen DAG für die Longest-Path-Analyse
    zu erzeugen.

    Strategie:
    - FOR-Schleifen: Iterationsanzahl aus Grenzen berechnen (start, end, step)
    - WHILE / REPEAT: Schranke aus Annotation oder DEFAULT_MAX_ITERATIONS
    """

    def __init__(self, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> None:
        self._max_iter = max_iterations

    def annotate(self, cfg: CFGGraph, loop_nodes: list) -> CFGGraph:
        """
        Gibt einen azyklischen CFG zurück, bei dem Schleifenrückwärtskanten
        durch gewichtete Vorwärtskanten mit multiplizierter Latenz ersetzt wurden.

        :param cfg:        Originaler (möglicherweise zyklischer) CFG
        :param loop_nodes: Liste der ForNode / WhileNode / RepeatNode aus dem AST
        :return:           Modifizierter, azyklischer CFG
        """
        new_cfg = copy.deepcopy(cfg)
        g = new_cfg.graph
        
        if len(g) == 0:
            return new_cfg
            
        # 1. Bestimme den Startknoten (Eintragspunkt)
        entry = list(g.nodes)[0]
        
        # 2. Finde Dominatoren
        try:
            dom = nx.immediate_dominators(g, entry)
        except Exception:
            return new_cfg
            
        def get_dominators(node):
            res = {node}
            curr = node
            while curr in dom and dom[curr] != curr:
                curr = dom[curr]
                res.add(curr)
            return res

        # 3. Finde alle Rückwärtskanten (Back-edges)
        back_edges = []
        for u, v in list(g.edges()):
            if v in get_dominators(u):
                back_edges.append((u, v))
                
        # 4. Bestimme für jede Rückwärtskante die Schleife und deren Grenzen
        multipliers = {node: 1 for node in g.nodes}
        
        for u, v in back_edges:
            # v ist der Header, u ist die Quelle der Rückwärtskante
            body = {v, u}
            rev_g = g.reverse()
            queue = [u]
            visited = {u, v}
            while queue:
                curr = queue.pop(0)
                for parent in rev_g.neighbors(curr):
                    if parent not in visited:
                        visited.add(parent)
                        body.add(parent)
                        queue.append(parent)
            
            # Finde passenden AST-Knoten für die Schleife, um Iterationszahl zu schätzen
            header_block = g.nodes[v].get("block")
            ast_node = None
            if header_block:
                ast_node = self._find_ast_loop(v, header_block, loop_nodes)
                
            iterations = self._max_iter
            if ast_node:
                if isinstance(ast_node, ForNode):
                    iterations = self._estimate_for_iterations(ast_node)
                elif isinstance(ast_node, WhileNode):
                    iterations = self._estimate_while_iterations(ast_node)
                elif isinstance(ast_node, RepeatNode):
                    iterations = self._estimate_repeat_iterations(ast_node)
            
            # Multipliziere Latenzen im Body
            for node in body:
                multipliers[node] *= iterations
                
            # Redirect the back-edge to the loop exit nodes to keep loop body connected to the exit
            exit_nodes = [node for node in g.successors(v) if node not in body]
            
            # Entferne die Rückwärtskante
            if g.has_edge(u, v):
                g.remove_edge(u, v)
                
            for exit_node in exit_nodes:
                g.add_edge(u, exit_node)
                
        # 5. Aktualisiere die Latenzen im Graphen und in den Blöcken
        for node in g.nodes:
            mult = multipliers[node]
            if mult > 1:
                block = g.nodes[node].get("block")
                if block:
                    # Multipliziere Latenzen der einzelnen Instruktionen
                    for instr in block.instructions:
                        instr.latency_ns *= mult
                    # Aktualisiere die Gesamtlatenz im Node-Attribut
                    g.nodes[node]["latency_ns"] = block.total_latency_ns
                    
        return new_cfg

    def _find_ast_loop(self, header_id: str, header_block, loop_nodes: list):
        # Zeilennummer der ersten Anweisung im Header ermitteln
        line = 0
        for instr in header_block.instructions:
            if instr.source_line > 0:
                line = instr.source_line
                break
                
        if header_id.startswith("for_"):
            expected_type = ForNode
        elif header_id.startswith("while_"):
            expected_type = WhileNode
        elif header_id.startswith("repeat_"):
            expected_type = RepeatNode
        else:
            return None
            
        # Match by line number closeness
        best_node = None
        min_diff = float("inf")
        for node in loop_nodes:
            if isinstance(node, expected_type):
                diff = abs(node.line - line) if line > 0 else 0
                if diff < min_diff:
                    min_diff = diff
                    best_node = node
        return best_node

    def _estimate_for_iterations(self, node: ForNode) -> int:
        """Berechnet Iterationszahl für statische FOR-Grenzen."""
        try:
            if isinstance(node.start, LiteralNode) and isinstance(node.end, LiteralNode):
                start_val = int(node.start.value)
                end_val = int(node.end.value)
                step_val = 1
                if node.step and isinstance(node.step, LiteralNode):
                    step_val = int(node.step.value)
                if step_val == 0:
                    step_val = 1
                
                iterations = (end_val - start_val) // step_val + 1
                return max(0, iterations)
        except Exception:
            pass
        return self._max_iter

    def _estimate_while_iterations(self, node: WhileNode) -> int:
        """Gibt MAX-Schranke für WHILE-Schleifen zurück."""
        return self._max_iter

    def _estimate_repeat_iterations(self, node: RepeatNode) -> int:
        """Gibt MAX-Schranke für REPEAT-Schleifen zurück."""
        return self._max_iter
