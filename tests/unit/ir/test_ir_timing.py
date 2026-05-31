"""Unit-Tests: IR-Latenzen (Builtin-Ops, Speicherzugriffe)."""
from src.ir.ir_generator import IRGenerator
from src.ir.ir_nodes import IROpcode
from src.parser.ast_nodes import (
    AssignmentNode,
    BinaryOpNode,
    CallNode,
    FunctionBlockNode,
    IdentifierNode,
    LiteralNode,
    StatementListNode,
    VariableNode,
    VarSectionNode,
)
from src.profiles.profile_loader import ProfileLoader
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.semantic.symbol_table import StorageLocation


def _fb_with_body(*statements) -> FunctionBlockNode:
    return FunctionBlockNode(
        name="FB_Timing",
        body=StatementListNode(statements=list(statements)),
    )


def test_builtin_sqrt_uses_sqrt_opcode_latency():
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    ast = _fb_with_body(
        AssignmentNode(
            line=5,
            target=IdentifierNode(name="rTemp", access_type="LOCAL"),
            value=CallNode(line=5, name="SQRT", arguments=[("", LiteralNode(value=1.0))]),
        )
    )
    st = SemanticAnalyzer(profile).analyze(ast)
    blocks = IRGenerator(profile, st).generate(ast)
    sqrt_instr = [
        i
        for b in blocks
        for i in b.instructions
        if i.opcode == IROpcode.SQRT
    ]
    assert len(sqrt_instr) == 1
    assert sqrt_instr[0].latency_ns == profile.get_instruction_latency(IROpcode.SQRT)


def test_local_load_includes_stack_access_time():
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    ast = FunctionBlockNode(
        name="FB_T",
        var_sections=[],
        body=StatementListNode(
            statements=[
                AssignmentNode(
                    line=3,
                    target=IdentifierNode(name="rA", access_type="LOCAL"),
                    value=IdentifierNode(name="rB", access_type="LOCAL"),
                )
            ]
        ),
    )
    from src.parser.ast_nodes import VarSectionNode, VariableNode

    ast.var_sections = [
        VarSectionNode(
            kind="VAR_TEMP",
            variables=[
                VariableNode(name="rA", type_name="REAL"),
                VariableNode(name="rB", type_name="REAL"),
            ],
        )
    ]
    st = SemanticAnalyzer(profile).analyze(ast)
    blocks = IRGenerator(profile, st).generate(ast)
    load_b = [
        i
        for b in blocks
        for i in b.instructions
        if i.opcode == IROpcode.LOAD and "rB" in i.operands
    ]
    assert load_b
    read_stack, _ = profile.get_access_times(StorageLocation.LOCAL_STACK)
    expected = profile.get_instruction_latency(IROpcode.LOAD) + read_stack
    assert load_b[0].latency_ns == expected


def test_db_access_uses_shared_db_timing():
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    ast = _fb_with_body(
        AssignmentNode(
            line=2,
            target=IdentifierNode(name="DB1.DBX0.0", access_type="DB"),
            value=LiteralNode(value=True),
        )
    )
    st = SemanticAnalyzer(profile).analyze(ast)
    blocks = IRGenerator(profile, st).generate(ast)
    stores = [i for b in blocks for i in b.instructions if i.opcode == IROpcode.STORE]
    assert stores
    _, write_db = profile.get_access_times(StorageLocation.SHARED_DB)
    expected = profile.get_instruction_latency(IROpcode.STORE) + write_db
    assert stores[0].latency_ns == expected


def test_real_add_uses_real_opcode_latency():
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    ast = FunctionBlockNode(
        name="FB_Real",
        var_sections=[
            VarSectionNode(
                kind="VAR",
                variables=[
                    VariableNode(name="rA", type_name="REAL"),
                    VariableNode(name="rB", type_name="REAL"),
                    VariableNode(name="rC", type_name="REAL"),
                ],
            )
        ],
        body=StatementListNode(
            statements=[
                AssignmentNode(
                    line=5,
                    target=IdentifierNode(name="rC"),
                    value=BinaryOpNode(
                        line=5,
                        operator="+",
                        left=IdentifierNode(name="rA"),
                        right=IdentifierNode(name="rB"),
                    ),
                )
            ]
        ),
    )
    st = SemanticAnalyzer(profile).analyze(ast)
    blocks = IRGenerator(profile, st).generate(ast)
    adds = [
        i
        for b in blocks
        for i in b.instructions
        if i.opcode == IROpcode.ADD
    ]
    assert adds
    expected = profile.get_instruction_latency(IROpcode.ADD, "REAL")
    assert adds[0].latency_ns == expected
    assert expected == 440.0


def test_cpu314_add_real_matches_instruction_list():
    profile = ProfileLoader().load("S7-300-CPU314")
    assert profile.get_instruction_latency(IROpcode.ADD, "REAL") == 580.0
    assert profile.get_instruction_latency(IROpcode.MUL, "REAL") == 580.0
