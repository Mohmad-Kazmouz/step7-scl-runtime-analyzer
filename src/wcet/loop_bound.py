"""
loop_bound.py – Schleifen-Schranken-Annotierung

Schleifenzyklen im CFG werden für die WCET-Analyse aufgelöst,
indem FOR-Schleifen mit statischen Grenzen direkt expandiert und
WHILE/REPEAT-Schleifen mit statisch erkannten oder konfigurierbaren
Grenzen annotiert werden.
"""

from __future__ import annotations

import copy
import warnings
from dataclasses import dataclass

import networkx as nx

from ..cfg.cfg_graph import CFGGraph
from ..parser.ast_nodes import (
    AssignmentNode,
    ASTNode,
    BinaryOpNode,
    ForNode,
    FunctionBlockNode,
    IdentifierNode,
    LiteralNode,
    RepeatNode,
    StatementListNode,
    WhileNode,
)

DEFAULT_MAX_ITERATIONS = 100  # Fallback für nicht auflösbare Schleifen

# UNTIL-Bedingung (Abbruch wenn wahr) → WHILE-äquivalente Fortsetzungsbedingung
_EXIT_TO_CONTINUE_OP: dict[str, str] = {
    ">=": "<",
    ">": "<=",
    "<=": ">",
    "<": ">=",
}


@dataclass(frozen=True)
class _CounterLimit:
    """Erkannte Zähler-Grenze aus einer Vergleichsbedingung."""

    variable: str
    op: str  # '<', '<=', '>', '>=' — Fortsetzungsbedingung (WHILE-Semantik)
    limit: int


def collect_var_literal_inits(fb: FunctionBlockNode) -> dict[str, int]:
    """
    Sammelt INT-Initialwerte aus VAR-/CONST-Abschnitten (Name → Wert).

    Namen werden upper-case gespeichert für case-insensitives Lookup.
    """
    inits: dict[str, int] = {}
    for section in fb.var_sections:
        for var in section.variables:
            if var.initial_value and isinstance(var.initial_value, LiteralNode):
                try:
                    inits[var.name.upper()] = int(var.initial_value.value)
                except (TypeError, ValueError):
                    pass
    return inits


class LoopBoundAnnotator:
    """
    Löst Schleifenzyklen im CFG auf, um einen DAG für die Longest-Path-Analyse
    zu erzeugen.

    Strategie:
    - FOR-Schleifen: Iterationsanzahl aus Grenzen berechnen (start, end, step)
    - WHILE / REPEAT: statische Zähler-Grenzen aus Bedingung + Body, sonst max_iter
    """

    def __init__(self, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> None:
        self._max_iter = max_iterations
        self._var_inits: dict[str, int] = {}

    def annotate(
        self,
        cfg: CFGGraph,
        loop_nodes: list,
        var_inits: dict[str, int] | None = None,
    ) -> CFGGraph:
        """
        Gibt einen azyklischen CFG zurück, bei dem Schleifenrückwärtskanten
        durch gewichtete Vorwärtskanten mit multiplizierter Latenz ersetzt wurden.

        :param cfg:        Originaler (möglicherweise zyklischer) CFG
        :param loop_nodes: Liste der ForNode / WhileNode / RepeatNode aus dem AST
        :param var_inits:  Optionale VAR-Initialwerte (Name → INT) für Grenzen
        :return:           Modifizierter, azyklischer CFG
        """
        self._var_inits = {k.upper(): v for k, v in (var_inits or {}).items()}
        new_cfg = copy.deepcopy(cfg)
        g = new_cfg.graph

        if len(g) == 0:
            return new_cfg

        entry = list(g.nodes)[0]

        try:
            dom = nx.immediate_dominators(g, entry)
        except Exception as exc:
            warnings.warn(
                f"Schleifenauflösung fehlgeschlagen (Dominatoren): {exc}. "
                "CFG bleibt zyklisch; WCET-Analyse kann fehlschlagen.",
                stacklevel=2,
            )
            return new_cfg

        def get_dominators(node):
            res = {node}
            curr = node
            while curr in dom and dom[curr] != curr:
                curr = dom[curr]
                res.add(curr)
            return res

        back_edges = []
        for u, v in list(g.edges()):
            if v in get_dominators(u):
                back_edges.append((u, v))

        multipliers = {node: 1 for node in g.nodes}

        for u, v in back_edges:
            body = {u}
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

            header_block = g.nodes[v].get("block")
            ast_node = None
            if header_block:
                ast_node = self._find_ast_loop(v, header_block, loop_nodes)

            iterations = self._max_iter
            if ast_node:
                if isinstance(ast_node, ForNode):
                    iterations = self._estimate_for_iterations(ast_node)
                    if iterations == 0:
                        iterations = self._max_iter
                elif isinstance(ast_node, WhileNode):
                    iterations = self._estimate_while_iterations(ast_node)
                elif isinstance(ast_node, RepeatNode):
                    iterations = self._estimate_repeat_iterations(ast_node)

            for node_id in body:
                multipliers[node_id] *= iterations
            multipliers[v] *= iterations + 1

            if g.has_edge(u, v):
                g.remove_edge(u, v)

            exit_nodes = [node for node in g.successors(v) if node not in body]
            for exit_node in exit_nodes:
                g.add_edge(u, exit_node)

        for node in g.nodes:
            mult = multipliers[node]
            if mult > 1:
                block = g.nodes[node].get("block")
                if block:
                    for instr in block.instructions:
                        instr.latency_ns *= mult
                    g.nodes[node]["latency_ns"] = block.total_latency_ns

        return new_cfg

    def _find_ast_loop(self, header_id: str, header_block, loop_nodes: list):
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

        best_node = None
        min_diff = float("inf")
        for node in loop_nodes:
            if isinstance(node, expected_type):
                diff = abs(node.line - line) if line > 0 else float("inf")
                if diff < min_diff:
                    min_diff = diff
                    best_node = node
        return best_node

    def _estimate_for_iterations(self, node: ForNode) -> int:
        """Berechnet Iterationszahl für statische FOR-Grenzen."""
        try:
            if isinstance(node.start, LiteralNode) and isinstance(
                node.end, LiteralNode
            ):
                start_val = int(node.start.value)
                end_val = int(node.end.value)
                step_val = 1
                if node.step and isinstance(node.step, LiteralNode):
                    step_val = int(node.step.value)
                if step_val == 0:
                    return 0

                iterations = (end_val - start_val) // step_val + 1
                return max(0, iterations)
        except (TypeError, ValueError):
            pass
        return self._max_iter

    def _estimate_while_iterations(self, node: WhileNode) -> int:
        """Statische Zähler-Grenze aus WHILE-Bedingung, sonst max_iter."""
        bound = self._estimate_static_loop_bound(
            node.condition, node.body, exit_condition=False
        )
        return bound if bound is not None else self._max_iter

    def _estimate_repeat_iterations(self, node: RepeatNode) -> int:
        """Statische Zähler-Grenze aus UNTIL-Bedingung, sonst max_iter."""
        bound = self._estimate_static_loop_bound(
            node.condition, node.body, exit_condition=True
        )
        return bound if bound is not None else self._max_iter

    def _estimate_static_loop_bound(
        self,
        condition: ASTNode | None,
        body: StatementListNode | None,
        *,
        exit_condition: bool,
    ) -> int | None:
        """
        Schätzt Iterationszahl aus Zähler-Vergleichen in der (UNTIL-)Bedingung.

        Unterstützt u.a.:
        - WHILE i < 10  mit i := i + 1
        - WHILE (cond) AND (i <= MaxCycles)  mit Literal oder VAR-Init
        - REPEAT ... UNTIL i >= 10  (äquivalent zu WHILE i < 10)
        """
        if condition is None:
            return None

        limits = self._extract_counter_limits(condition, exit_condition=exit_condition)
        if not limits:
            return None

        iteration_counts: list[int] = []
        for limit in limits:
            init = self._find_counter_init(body, limit.variable)
            step = self._find_counter_step(body, limit.variable)
            if step is None or step <= 0:
                continue
            count = self._iterations_for_counter(
                limit.op, limit.limit, init, step
            )
            if count is not None:
                iteration_counts.append(count)

        if not iteration_counts:
            return None
        # Engste explizite Zähler-Grenze bestimmt die maximale Iterationszahl
        return min(iteration_counts)

    def _extract_counter_limits(
        self, node: ASTNode, *, exit_condition: bool
    ) -> list[_CounterLimit]:
        """Extrahiert Zähler-Vergleiche aus AND-verknüpften Bedingungen."""
        if isinstance(node, BinaryOpNode) and node.operator.upper() == "AND":
            left = self._extract_counter_limits(node.left, exit_condition=exit_condition)
            right = self._extract_counter_limits(
                node.right, exit_condition=exit_condition
            )
            return left + right

        limit = self._parse_counter_comparison(node, exit_condition=exit_condition)
        return [limit] if limit else []

    def _parse_counter_comparison(
        self, node: ASTNode, *, exit_condition: bool
    ) -> _CounterLimit | None:
        if not isinstance(node, BinaryOpNode):
            return None

        op = node.operator
        if op not in _EXIT_TO_CONTINUE_OP and op not in ("<", "<=", ">", ">="):
            return None

        if exit_condition:
            op = _EXIT_TO_CONTINUE_OP.get(op)
            if op is None:
                return None

        # var < literal  oder  literal > var
        left_var, right_limit = self._comparison_operands(node.left, node.right, op)
        if left_var and right_limit is not None:
            return _CounterLimit(variable=left_var, op=op, limit=right_limit)

        # literal < var  →  var > literal  (Spiegelung)
        right_var, left_limit = self._comparison_operands(node.right, node.left, op)
        if right_var and left_limit is not None:
            mirrored = self._mirror_op(op)
            if mirrored:
                return _CounterLimit(variable=right_var, op=mirrored, limit=left_limit)

        return None

    @staticmethod
    def _mirror_op(op: str) -> str | None:
        return {">": "<", ">=": "<=", "<": ">", "<=": ">="}.get(op)

    def _comparison_operands(
        self, var_side: ASTNode | None, limit_side: ASTNode | None, op: str
    ) -> tuple[str | None, int | None]:
        if not isinstance(var_side, IdentifierNode):
            return None, None
        limit = self._resolve_int(limit_side)
        if limit is None:
            return None, None
        return var_side.name.upper(), limit

    def _resolve_int(self, node: ASTNode | None) -> int | None:
        if isinstance(node, LiteralNode):
            try:
                return int(node.value)
            except (TypeError, ValueError):
                return None
        if isinstance(node, IdentifierNode):
            return self._var_inits.get(node.name.upper())
        return None

    @staticmethod
    def _find_counter_init(
        body: StatementListNode | None, var_name: str
    ) -> int:
        """Erstes ``var := Literal`` im Schleifenrumpf, sonst 0."""
        if body is None:
            return 0
        name = var_name.upper()
        for stmt in body.statements:
            if isinstance(stmt, AssignmentNode):
                target = stmt.target
                if (
                    isinstance(target, IdentifierNode)
                    and target.name.upper() == name
                    and isinstance(stmt.value, LiteralNode)
                ):
                    try:
                        return int(stmt.value.value)
                    except (TypeError, ValueError):
                        return 0
        return 0

    @staticmethod
    def _find_counter_step(
        body: StatementListNode | None, var_name: str
    ) -> int | None:
        """Sucht ``var := var + step`` oder ``var := var - step`` im Rumpf."""
        if body is None:
            return None
        name = var_name.upper()
        for stmt in body.statements:
            step = LoopBoundAnnotator._assignment_step(stmt, name)
            if step is not None:
                return step
        return None

    @staticmethod
    def _assignment_step(stmt: ASTNode, var_name: str) -> int | None:
        if not isinstance(stmt, AssignmentNode):
            return None
        target = stmt.target
        if not isinstance(target, IdentifierNode) or target.name.upper() != var_name:
            return None
        value = stmt.value
        if not isinstance(value, BinaryOpNode):
            return None
        if value.operator == "+":
            if isinstance(value.left, IdentifierNode) and value.left.name.upper() == var_name:
                if isinstance(value.right, LiteralNode):
                    try:
                        return int(value.right.value)
                    except (TypeError, ValueError):
                        return None
        elif value.operator == "-":
            if isinstance(value.left, IdentifierNode) and value.left.name.upper() == var_name:
                if isinstance(value.right, LiteralNode):
                    try:
                        return -int(value.right.value)
                    except (TypeError, ValueError):
                        return None
        return None

    @staticmethod
    def _iterations_for_counter(
        op: str, limit: int, init: int, step: int
    ) -> int | None:
        """
        Berechnet maximale Iterationszahl für Zähler mit konstantem Schritt.

        WHILE-Semantik: Schleife läuft solange die Vergleichsbedingung wahr ist.
        """
        if step == 0:
            return None

        if step > 0:
            if op == "<":
                if init >= limit:
                    return 0
                return (limit - init + step - 1) // step
            if op == "<=":
                if init > limit:
                    return 0
                return (limit - init) // step + 1
            if op == ">":
                if init <= limit:
                    return 0
                return (init - limit + step - 1) // step
            if op == ">=":
                if init < limit:
                    return 0
                return (init - limit) // step + 1
        else:
            # Abwärtszähler (step negativ)
            if op == ">":
                if init <= limit:
                    return 0
                return (init - limit + (-step) - 1) // (-step)
            if op == ">=":
                if init < limit:
                    return 0
                return (init - limit) // (-step) + 1
            if op == "<":
                if init >= limit:
                    return 0
                return (limit - init + (-step) - 1) // (-step)
            if op == "<=":
                if init > limit:
                    return 0
                return (limit - init) // (-step) + 1

        return None
