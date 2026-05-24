"""Unit-Tests: CFGGraph"""
import pytest
from src.cfg.cfg_graph import CFGGraph
from src.ir.ir_nodes import IRBlock, IRInstruction, IROpcode


def _make_block(bid, latency=100.0):
    block = IRBlock(bid)
    block.instructions = [IRInstruction(IROpcode.ADD, latency_ns=latency)]
    return block


def test_add_block_and_edge():
    cfg = CFGGraph()
    b1 = _make_block("A")
    b2 = _make_block("B")
    cfg.add_block(b1)
    cfg.add_block(b2)
    cfg.add_edge("A", "B")
    assert len(cfg) == 2


def test_critical_path_linear():
    cfg = CFGGraph()
    for bid, lat in [("A", 100.0), ("B", 200.0), ("C", 50.0)]:
        cfg.add_block(_make_block(bid, lat))
    cfg.add_edge("A", "B")
    cfg.add_edge("B", "C")
    path = cfg.find_critical_path()
    assert [b.block_id for b in path] == ["A", "B", "C"]


def test_total_wcet():
    cfg = CFGGraph()
    for bid, lat in [("A", 100.0), ("B", 200.0)]:
        cfg.add_block(_make_block(bid, lat))
    cfg.add_edge("A", "B")
    assert cfg.total_wcet_ns() == pytest.approx(300.0)
