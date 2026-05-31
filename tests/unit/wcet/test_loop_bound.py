"""Unit-Tests: LoopBoundAnnotator"""

import networkx as nx
import pytest

from src.cfg.cfg_graph import CFGGraph
from src.ir.ir_nodes import IRBlock, IRInstruction, IROpcode
from src.parser.ast_nodes import (
    AssignmentNode,
    BinaryOpNode,
    ForNode,
    FunctionBlockNode,
    IdentifierNode,
    LiteralNode,
    RepeatNode,
    StatementListNode,
    VarSectionNode,
    VariableNode,
    WhileNode,
)
from src.wcet.loop_bound import LoopBoundAnnotator, collect_var_literal_inits


def _while_body(*statements) -> StatementListNode:
    return StatementListNode(statements=list(statements))


def test_estimate_for_iterations():
    annotator = LoopBoundAnnotator(max_iterations=50)

    node = ForNode(
        start=LiteralNode(value=1), end=LiteralNode(value=10), step=LiteralNode(value=1)
    )
    assert annotator._estimate_for_iterations(node) == 10

    node2 = ForNode(
        start=LiteralNode(value=0), end=LiteralNode(value=8), step=LiteralNode(value=2)
    )
    assert annotator._estimate_for_iterations(node2) == 5

    node3 = ForNode(start=LiteralNode(value=1), end=None)
    assert annotator._estimate_for_iterations(node3) == 50


def test_while_static_bound_counter_less_than():
    annotator = LoopBoundAnnotator(max_iterations=999)
    node = WhileNode(
        condition=BinaryOpNode(
            operator="<",
            left=IdentifierNode(name="i"),
            right=LiteralNode(value=10),
        ),
        body=_while_body(
            AssignmentNode(
                target=IdentifierNode(name="i"),
                value=LiteralNode(value=0),
            ),
            AssignmentNode(
                target=IdentifierNode(name="i"),
                value=BinaryOpNode(
                    operator="+",
                    left=IdentifierNode(name="i"),
                    right=LiteralNode(value=1),
                ),
            ),
        ),
    )
    assert annotator._estimate_while_iterations(node) == 10


def test_while_static_bound_with_and_and_var_init():
    annotator = LoopBoundAnnotator(max_iterations=999)
    annotator._var_inits = {"MAXCYCLES": 15}
    node = WhileNode(
        condition=BinaryOpNode(
            operator="AND",
            left=IdentifierNode(name="bAktiv"),
            right=BinaryOpNode(
                operator="<=",
                left=IdentifierNode(name="i"),
                right=IdentifierNode(name="MaxCycles"),
            ),
        ),
        body=_while_body(
            AssignmentNode(
                target=IdentifierNode(name="i"),
                value=LiteralNode(value=0),
            ),
            AssignmentNode(
                target=IdentifierNode(name="i"),
                value=BinaryOpNode(
                    operator="+",
                    left=IdentifierNode(name="i"),
                    right=LiteralNode(value=1),
                ),
            ),
        ),
    )
    # i = 0..15 → 16 Iterationen bei i <= 15
    assert annotator._estimate_while_iterations(node) == 16


def test_repeat_until_static_bound():
    annotator = LoopBoundAnnotator(max_iterations=999)
    node = RepeatNode(
        body=_while_body(
            AssignmentNode(
                target=IdentifierNode(name="i"),
                value=LiteralNode(value=0),
            ),
            AssignmentNode(
                target=IdentifierNode(name="i"),
                value=BinaryOpNode(
                    operator="+",
                    left=IdentifierNode(name="i"),
                    right=LiteralNode(value=1),
                ),
            ),
        ),
        condition=BinaryOpNode(
            operator=">=",
            left=IdentifierNode(name="i"),
            right=LiteralNode(value=10),
        ),
    )
    assert annotator._estimate_repeat_iterations(node) == 10


def test_while_without_counter_falls_back_to_max_iter():
    annotator = LoopBoundAnnotator(max_iterations=50)
    node = WhileNode(
        condition=IdentifierNode(name="bSensor"),
        body=_while_body(
            AssignmentNode(
                target=IdentifierNode(name="x"),
                value=LiteralNode(value=1),
            ),
        ),
    )
    assert annotator._estimate_while_iterations(node) == 50


def test_collect_var_literal_inits():
    fb = FunctionBlockNode(
        var_sections=[
            VarSectionNode(
                kind="VAR",
                variables=[
                    VariableNode(
                        name="MaxCycles",
                        type_name="INT",
                        initial_value=LiteralNode(value=20),
                    )
                ],
            )
        ]
    )
    assert collect_var_literal_inits(fb) == {"MAXCYCLES": 20}


def test_loop_bound_annotation_cycle():
    annotator = LoopBoundAnnotator(max_iterations=10)

    cfg = CFGGraph()
    # build entry -> for_0 (header) -> body -> for_0
    #                    for_0 -> exit

    b_entry = IRBlock("entry")
    b_entry.instructions = [IRInstruction(IROpcode.ADD, latency_ns=10.0)]

    b_header = IRBlock("for_0")
    b_header.instructions = [
        IRInstruction(IROpcode.ADD, latency_ns=20.0, source_line=5)
    ]

    b_body = IRBlock("body")
    b_body.instructions = [IRInstruction(IROpcode.ADD, latency_ns=30.0, source_line=6)]

    b_exit = IRBlock("exit")
    b_exit.instructions = [IRInstruction(IROpcode.ADD, latency_ns=40.0)]

    for b in (b_entry, b_header, b_body, b_exit):
        cfg.add_block(b)

    cfg.add_edge("entry", "for_0")
    cfg.add_edge("for_0", "body")
    cfg.add_edge("body", "for_0")
    cfg.add_edge("for_0", "exit")

    assert not nx.is_directed_acyclic_graph(cfg.graph)

    # Mock loop nodes
    loop_nodes = [
        ForNode(
            line=5,
            start=LiteralNode(value=1),
            end=LiteralNode(value=5),  # 5 iterations
            step=LiteralNode(value=1),
        )
    ]

    new_cfg = annotator.annotate(cfg, loop_nodes)

    # Back-edge "body -> for_0" should be removed
    assert nx.is_directed_acyclic_graph(new_cfg.graph)
    assert not new_cfg.graph.has_edge("body", "for_0")
    assert new_cfg.graph.has_edge("for_0", "body")

    # Header: (N+1) iterations = 6 × 20ns = 120ns
    # Body: N iterations = 5 × 30ns = 150ns
    assert new_cfg.graph.nodes["entry"]["block"].total_latency_ns == 10.0
    assert new_cfg.graph.nodes["for_0"]["block"].total_latency_ns == 120.0
    assert new_cfg.graph.nodes["body"]["block"].total_latency_ns == 150.0
    assert new_cfg.graph.nodes["exit"]["block"].total_latency_ns == 40.0
