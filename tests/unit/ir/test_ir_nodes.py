"""Unit-Tests: IR-Knoten"""
import pytest
from src.ir.ir_nodes import IRInstruction, IRBlock, IROpcode


def test_ir_instruction_repr():
    instr = IRInstruction(opcode=IROpcode.ADD, operands=["a", "b"],
                          result="c", source_line=5, latency_ns=50.0)
    assert "ADD" in repr(instr)
    assert "50.0ns" in repr(instr)


def test_ir_block_total_latency():
    block = IRBlock("test")
    block.instructions = [
        IRInstruction(IROpcode.LOAD, latency_ns=100.0),
        IRInstruction(IROpcode.ADD,  latency_ns=50.0),
        IRInstruction(IROpcode.STORE, latency_ns=120.0),
    ]
    assert block.total_latency_ns == pytest.approx(270.0)


def test_ir_block_empty_latency():
    block = IRBlock("empty")
    assert block.total_latency_ns == 0.0
