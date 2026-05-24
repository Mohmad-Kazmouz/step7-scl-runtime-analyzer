"""Unit-Tests für den SCLParser und ASTBuilder"""
from pathlib import Path
import pytest
from src.parser.scl_parser import SCLParser
from src.parser.ast_nodes import (
    FunctionBlockNode, VarSectionNode, VariableNode,
    AssignmentNode, IfNode, ForNode, WhileNode, RepeatNode,
    LiteralNode, IdentifierNode, CallNode, BinaryOpNode,
)


def test_parse_simple_fb():
    source = """
    FUNCTION_BLOCK FB_Simple
    VAR_INPUT
        x : BOOL;
    END_VAR
    VAR
        y : INT := 42;
    END_VAR
    BEGIN
        x := FALSE;
    END_FUNCTION_BLOCK
    """
    parser = SCLParser()
    ast = parser.parse_string(source, "test_simple")
    
    assert isinstance(ast, FunctionBlockNode)
    assert ast.name == "FB_Simple"
    assert len(ast.var_sections) == 2
    
    var_sec_input = ast.var_sections[0]
    assert var_sec_input.kind == "VAR_INPUT"
    assert len(var_sec_input.variables) == 1
    assert var_sec_input.variables[0].name == "x"
    assert var_sec_input.variables[0].type_name == "BOOL"
    assert var_sec_input.variables[0].initial_value is None
    
    var_sec_local = ast.var_sections[1]
    assert var_sec_local.kind == "VAR"
    assert len(var_sec_local.variables) == 1
    assert var_sec_local.variables[0].name == "y"
    assert var_sec_local.variables[0].type_name == "INT"
    assert isinstance(var_sec_local.variables[0].initial_value, LiteralNode)
    assert var_sec_local.variables[0].initial_value.value == 42

    assert ast.body is not None
    assert len(ast.body.statements) == 1
    stmt = ast.body.statements[0]
    assert isinstance(stmt, AssignmentNode)
    assert isinstance(stmt.target, IdentifierNode)
    assert stmt.target.name == "x"
    assert isinstance(stmt.value, LiteralNode)
    assert stmt.value.value is False


def test_parse_fb10_regelung():
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "scl_samples" / "FB10_Regelung.scl"
    parser = SCLParser()
    ast = parser.parse_file(fixture_path)
    
    assert ast.name == "FB10_Regelung"
    assert len(ast.var_sections) == 4  # VAR_INPUT, VAR_OUTPUT, VAR, VAR_TEMP
    
    # Check body contains IF statement
    assert ast.body is not None
    assert len(ast.body.statements) == 1
    if_stmt = ast.body.statements[0]
    assert isinstance(if_stmt, IfNode)
    assert isinstance(if_stmt.condition, IdentifierNode)
    assert if_stmt.condition.name == "bAktiv"
    
    # Check then body statements
    # Assignment: rFehler   := rSollwert - rIstwert;
    # Assignment: rIntegral := rIntegral + rFehler * rKi;
    # Assignment: rTemp     := rKp * rFehler + rIntegral;
    # ForNode: FOR iIndex := 1 TO 10 DO ...
    # Assignment: rStellwert := rTemp;
    # Assignment: bFehler    := FALSE;
    # Total 6 statements!
    assert len(if_stmt.then_body.statements) == 6
    
    for_loop = if_stmt.then_body.statements[3]
    assert isinstance(for_loop, ForNode)
    assert for_loop.variable == "iIndex"
    assert isinstance(for_loop.start, LiteralNode)
    assert for_loop.start.value == 1
    assert isinstance(for_loop.end, LiteralNode)
    assert for_loop.end.value == 10
    
    # Check FOR loop body has: rTemp := rTemp + SQRT(ABS(rFehler));
    assert len(for_loop.body.statements) == 1
    for_stmt = for_loop.body.statements[0]
    assert isinstance(for_stmt, AssignmentNode)
    assert isinstance(for_stmt.value, BinaryOpNode)
    assert for_stmt.value.operator == "+"
    assert isinstance(for_stmt.value.right, CallNode)
    assert for_stmt.value.right.name == "SQRT"


def test_identifier_access_type():
    source = """
    FUNCTION_BLOCK FB_Access
    BEGIN
        DB1.DBX0.0 := TRUE;
        M10.2 := FALSE;
        I0.0 := TRUE;
        E1.0 := FALSE;
        Q0.1 := TRUE;
        A1.1 := FALSE;
        x := y;
    END_FUNCTION_BLOCK
    """
    parser = SCLParser()
    ast = parser.parse_string(source, "test_access")
    
    statements = ast.body.statements
    assert len(statements) == 7
    
    # DB1.DBX0.0 (DB)
    assert statements[0].target.access_type == "DB"
    assert statements[0].target.name == "DB1.DBX0.0"
    
    # M10.2 (MERKER)
    assert statements[1].target.access_type == "MERKER"
    
    # I0.0 (INPUT)
    assert statements[2].target.access_type == "INPUT"
    
    # E1.0 (INPUT - German)
    assert statements[3].target.access_type == "INPUT"
    
    # Q0.1 (OUTPUT)
    assert statements[4].target.access_type == "OUTPUT"
    
    # A1.1 (OUTPUT - German)
    assert statements[5].target.access_type == "OUTPUT"
    
    # x := y (LOCAL)
    assert statements[6].target.access_type == "LOCAL"
    assert statements[6].value.access_type == "LOCAL"


def test_parse_while_and_repeat():
    source = """
    FUNCTION_BLOCK FB_Loops
    BEGIN
        WHILE x < 10 DO
            x := x + 1;
        END_WHILE;
        
        REPEAT
            y := y - 1;
        UNTIL y = 0
        END_REPEAT;
    END_FUNCTION_BLOCK
    """
    parser = SCLParser()
    ast = parser.parse_string(source, "test_loops")
    
    assert len(ast.body.statements) == 2
    
    while_stmt = ast.body.statements[0]
    assert isinstance(while_stmt, WhileNode)
    assert while_stmt.condition is not None
    assert len(while_stmt.body.statements) == 1
    
    repeat_stmt = ast.body.statements[1]
    assert isinstance(repeat_stmt, RepeatNode)
    assert repeat_stmt.condition is not None
    assert len(repeat_stmt.body.statements) == 1


def test_parse_extensions():
    source = """
    FUNCTION_BLOCK FB_Extensions
    CONST
        MAX_VAL := 100;
        MIN_VAL : INT := 0;
    END_CONST
    VAR
        u32_Val : DWORD;
        arr_Val AT u32_Val : ARRAY[0..3] OF BYTE;
        user_struct : STRUCT
            a : BOOL;
        END_STRUCT;
    END_VAR
    BEGIN
        u32_Val := 42;
    END_FUNCTION_BLOCK
    """
    parser = SCLParser()
    ast = parser.parse_string(source, "test_extensions")
    
    assert isinstance(ast, FunctionBlockNode)
    assert ast.name == "FB_Extensions"
    
    assert len(ast.var_sections) == 2
    
    # Check CONST section
    const_sec = ast.var_sections[1]
    assert const_sec.kind == "VAR"
    assert len(const_sec.variables) == 2
    assert const_sec.variables[0].name == "MAX_VAL"
    assert const_sec.variables[0].type_name == ""
    assert const_sec.variables[1].name == "MIN_VAL"
    assert const_sec.variables[1].type_name == "INT"
    
    # Check VAR section
    var_sec = ast.var_sections[0]
    assert var_sec.kind == "VAR"
    assert len(var_sec.variables) == 3
    assert var_sec.variables[0].name == "u32_Val"
    assert var_sec.variables[0].type_name == "DWORD"
    
    assert var_sec.variables[1].name == "arr_Val"
    assert var_sec.variables[1].type_name == "ARRAY[0..3] OF BYTE"
    
    assert var_sec.variables[2].name == "user_struct"
    assert var_sec.variables[2].type_name == "STRUCT"

