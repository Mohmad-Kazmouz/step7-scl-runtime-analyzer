"""Unit-Tests: LoopBoundAnnotator"""
import pytest
import networkx as nx
from src.wcet.loop_bound import LoopBoundAnnotator
from src.parser.ast_nodes import ForNode, WhileNode, RepeatNode, LiteralNode
from src.cfg.cfg_graph import CFGGraph
from src.ir.ir_nodes import IRBlock, IRInstruction, IROpcode


def test_estimate_for_iterations():
    annotator = LoopBoundAnnotator(max_iterations=50)
    
    # FOR i := 1 TO 10 BY 1
    node = ForNode(
        start=LiteralNode(value=1),
        end=LiteralNode(value=10),
        step=LiteralNode(value=1)
    )
    assert annotator._estimate_for_iterations(node) == 10
    
    # FOR i := 0 TO 8 BY 2
    node2 = ForNode(
        start=LiteralNode(value=0),
        end=LiteralNode(value=8),
        step=LiteralNode(value=2)
    )
    assert annotator._estimate_for_iterations(node2) == 5
    
    # Dynamic bounds fallback
    node3 = ForNode(
        start=LiteralNode(value=1),
        end=None
    )
    assert annotator._estimate_for_iterations(node3) == 50


def test_loop_bound_annotation_cycle():
    annotator = LoopBoundAnnotator(max_iterations=10)
    
    cfg = CFGGraph()
    # build entry -> for_0 (header) -> body -> for_0
    #                    for_0 -> exit
    
    b_entry = IRBlock("entry")
    b_entry.instructions = [IRInstruction(IROpcode.ADD, latency_ns=10.0)]
    
    b_header = IRBlock("for_0")
    b_header.instructions = [IRInstruction(IROpcode.ADD, latency_ns=20.0, source_line=5)]
    
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
            step=LiteralNode(value=1)
        )
    ]
    
    new_cfg = annotator.annotate(cfg, loop_nodes)
    
    # Back-edge "body -> for_0" should be removed
    assert nx.is_directed_acyclic_graph(new_cfg.graph)
    assert not new_cfg.graph.has_edge("body", "for_0")
    assert new_cfg.graph.has_edge("for_0", "body")
    
    # Latencies of loop body (for_0 and body) should be multiplied by 5
    assert new_cfg.graph.nodes["entry"]["block"].total_latency_ns == 10.0
    assert new_cfg.graph.nodes["for_0"]["block"].total_latency_ns == 100.0
    assert new_cfg.graph.nodes["body"]["block"].total_latency_ns == 150.0
    assert new_cfg.graph.nodes["exit"]["block"].total_latency_ns == 40.0
