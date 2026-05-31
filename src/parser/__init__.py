"""
parser – Stufe 1 der Analyse-Pipeline
Lexer + Parser für SCL-Funktionsbausteine (SIMATIC Manager Format).
Eingabe: kompilierbarer SCL-FB-Quelltext
Ausgabe: AST (Abstract Syntax Tree)
"""
from .scl_parser import SCLParser
from .ast_nodes import (
    ASTNode, FunctionBlockNode, VarSectionNode, VariableNode,
    StatementListNode, AssignmentNode, IfNode, ForNode, WhileNode,
    RepeatNode, CaseNode, CallNode, ExpressionNode, BinaryOpNode,
    UnaryOpNode, LiteralNode, IdentifierNode, IndexNode, MemberNode,
    ExitNode, ReturnNode,
)

__all__ = [
    "SCLParser",
    "ASTNode", "FunctionBlockNode", "VarSectionNode", "VariableNode",
    "StatementListNode", "AssignmentNode", "IfNode", "ForNode",
    "WhileNode", "RepeatNode", "CaseNode", "CallNode",
    "ExpressionNode", "BinaryOpNode", "UnaryOpNode",
    "LiteralNode", "IdentifierNode", "IndexNode", "MemberNode",
    "ExitNode", "ReturnNode",
]
