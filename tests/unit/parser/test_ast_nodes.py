"""Unit-Tests: AST-Knoten"""
import pytest
from src.parser.ast_nodes import (
    FunctionBlockNode, VarSectionNode, VariableNode,
    ForNode, IfNode, LiteralNode, IdentifierNode,
)


def test_function_block_node_defaults():
    fb = FunctionBlockNode()
    assert fb.name == ""
    assert fb.var_sections == []
    assert fb.body is None


def test_literal_node_stores_value():
    lit = LiteralNode(value=42, type_name="INT", line=5)
    assert lit.value == 42
    assert lit.type_name == "INT"
    assert lit.line == 5


def test_identifier_access_type_default():
    ident = IdentifierNode(name="rSollwert")
    assert ident.access_type == "LOCAL"


def test_for_node_fields():
    node = ForNode(variable="i", line=10)
    assert node.variable == "i"
    assert node.line == 10
