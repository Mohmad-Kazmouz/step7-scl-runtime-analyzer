# ast_nodes.py – Knotentypen des Abstract Syntax Tree (AST)
#
# Jeder Knoten repräsentiert ein SCL-Sprachkonstrukt.
# Alle Knoten erben von ASTNode und speichern Quellposition (Zeile/Spalte)
# für spätere Hotspot-Rückverfolgung auf den SCL-Quelltext.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ASTNode:
    """Basisklasse aller AST-Knoten."""
    line: int = 0
    col: int = 0

    def accept(self, visitor):
        """Visitor-Pattern: leitet den Aufruf an den zuständigen Visitor weiter."""
        method = f"visit_{type(self).__name__}"
        return getattr(visitor, method, visitor.generic_visit)(self)


# ── Strukturknoten ────────────────────────────────────────────────────────────

@dataclass
class FunctionBlockNode(ASTNode):
    """Wurzelknoten: repräsentiert den gesamten FUNCTION_BLOCK ... END_FUNCTION_BLOCK."""
    name: str = ""
    var_sections: list[VarSectionNode] = field(default_factory=list)
    body: Optional[StatementListNode] = None


@dataclass
class VarSectionNode(ASTNode):
    """VAR / VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT / VAR_TEMP Abschnitt."""
    kind: str = "VAR"           # 'VAR' | 'VAR_INPUT' | 'VAR_OUTPUT' | 'VAR_IN_OUT' | 'VAR_TEMP'
    variables: list[VariableNode] = field(default_factory=list)


@dataclass
class VariableNode(ASTNode):
    """Einzelne Variablendeklaration mit Name, Typ und optionalem Initialwert."""
    name: str = ""
    type_name: str = ""
    initial_value: Optional[ASTNode] = None


@dataclass
class StatementListNode(ASTNode):
    """Folge von Anweisungen (Sequenz)."""
    statements: list[ASTNode] = field(default_factory=list)


# ── Anweisungsknoten ──────────────────────────────────────────────────────────

@dataclass
class AssignmentNode(ASTNode):
    """Zuweisung: target := value"""
    target: Optional[ASTNode] = None
    value: Optional[ASTNode] = None


@dataclass
class IfNode(ASTNode):
    """IF condition THEN ... ELSIF ... ELSE ... END_IF"""
    condition: Optional[ASTNode] = None
    then_body: Optional[StatementListNode] = None
    elsif_branches: list[tuple[ASTNode, StatementListNode]] = field(default_factory=list)
    else_body: Optional[StatementListNode] = None


@dataclass
class ForNode(ASTNode):
    """FOR var := start TO end BY step DO ... END_FOR"""
    variable: str = ""
    start: Optional[ASTNode] = None
    end: Optional[ASTNode] = None
    step: Optional[ASTNode] = None
    body: Optional[StatementListNode] = None


@dataclass
class WhileNode(ASTNode):
    """WHILE condition DO ... END_WHILE"""
    condition: Optional[ASTNode] = None
    body: Optional[StatementListNode] = None


@dataclass
class RepeatNode(ASTNode):
    """REPEAT ... UNTIL condition END_REPEAT"""
    body: Optional[StatementListNode] = None
    condition: Optional[ASTNode] = None


@dataclass
class CaseNode(ASTNode):
    """CASE expression OF value: ... ELSE: ... END_CASE"""
    expression: Optional[ASTNode] = None
    branches: list[tuple[list[ASTNode], StatementListNode]] = field(default_factory=list)
    else_body: Optional[StatementListNode] = None


@dataclass
class CallNode(ASTNode):
    """Funktions- oder FB-Aufruf: name(param1 := val1, ...)"""
    name: str = ""
    arguments: list[tuple[str, ASTNode]] = field(default_factory=list)


@dataclass
class ReturnNode(ASTNode):
    """RETURN-Anweisung."""
    pass


@dataclass
class ExitNode(ASTNode):
    """EXIT-Anweisung (Schleifenabbruch)."""
    pass


# ── Ausdrucksknoten ───────────────────────────────────────────────────────────

@dataclass
class ExpressionNode(ASTNode):
    """Basisklasse für Ausdrücke."""
    pass


@dataclass
class BinaryOpNode(ExpressionNode):
    """Binärer Operator: left op right (z.B. a + b, x AND y)."""
    operator: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None


@dataclass
class UnaryOpNode(ExpressionNode):
    """Unärer Operator: op operand (z.B. NOT x, -y)."""
    operator: str = ""
    operand: Optional[ASTNode] = None


@dataclass
class LiteralNode(ExpressionNode):
    """Literalwert: Zahl, Bool, String, Zeit, etc."""
    value: object = None
    type_name: str = ""        # 'INT', 'REAL', 'BOOL', 'TIME', ...


@dataclass
class IdentifierNode(ExpressionNode):
    """Bezeichner: einfache Variable, DB-Zugriff (DB1.DBX0.0), Merker (M0.0), etc."""
    name: str = ""
    access_type: str = "LOCAL"  # 'LOCAL' | 'DB' | 'MERKER' | 'INPUT' | 'OUTPUT'


@dataclass
class IndexNode(ExpressionNode):
    """Array-Zugriff: array[index1, index2, ...]"""
    array: Optional[ASTNode] = None
    indices: list[ASTNode] = field(default_factory=list)


@dataclass
class MemberNode(ExpressionNode):
    """Strukturierte Member-Zugriff: obj.member"""
    obj: Optional[ASTNode] = None
    member: str = ""
