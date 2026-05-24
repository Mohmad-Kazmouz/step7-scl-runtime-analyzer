"""Unit-Tests: IRGenerator Block Splitting"""
from src.parser.scl_parser import SCLParser
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.ir.ir_generator import IRGenerator
from src.profiles.profile_loader import ProfileLoader


def test_ir_generator_if_splitting():
    source = """
    FUNCTION_BLOCK FB_Test
    VAR
        x : BOOL;
        y : INT;
    END_VAR
    BEGIN
        IF x THEN
            y := 1;
        ELSE
            y := 2;
        END_IF;
    END_FUNCTION_BLOCK
    """
    ast = SCLParser().parse_string(source, "test_if")
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    symbol_table = SemanticAnalyzer(profile).analyze(ast)
    generator = IRGenerator(profile, symbol_table)
    blocks = generator.generate(ast)

    block_ids = [b.block_id for b in blocks]
    # Check that blocks were created for the then, else, and endif labels
    assert any(bid.startswith("then_") for bid in block_ids)
    assert any(bid.startswith("else_") for bid in block_ids)
    assert any(bid.startswith("endif_") for bid in block_ids)

    # Let's verify that the instructions in "then_" block have correct line numbers (y := 1 is line 9)
    then_blocks = [b for b in blocks if b.block_id.startswith("then_")]
    assert len(then_blocks) == 1
    then_block = then_blocks[0]
    # We expect y := 1 to emit STORE instruction at line 9
    then_lines = [i.source_line for i in then_block.instructions if i.source_line > 0]
    assert 9 in then_lines
    # The IF statement line (line 8) should NOT be in the then_block
    assert 8 not in then_lines


def test_ir_generator_for_splitting():
    source = """
    FUNCTION_BLOCK FB_Test_For
    VAR
        i : INT;
        y : INT;
    END_VAR
    BEGIN
        FOR i := 1 TO 10 DO
            y := y + 1;
        END_FOR;
    END_FUNCTION_BLOCK
    """
    ast = SCLParser().parse_string(source, "test_for")
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    symbol_table = SemanticAnalyzer(profile).analyze(ast)
    generator = IRGenerator(profile, symbol_table)
    blocks = generator.generate(ast)

    block_ids = [b.block_id for b in blocks]
    # Check for body and loop end/header blocks
    assert any(bid.startswith("for_body_") for bid in block_ids)
    assert any(bid.startswith("endfor_") for bid in block_ids)

    body_blocks = [b for b in blocks if b.block_id.startswith("for_body_")]
    assert len(body_blocks) == 1
    body_block = body_blocks[0]
    body_lines = [i.source_line for i in body_block.instructions if i.source_line > 0]
    # We expect y := y + 1 to be inside the body (line 9)
    assert 9 in body_lines
    # The FOR loop header line (line 8) should NOT be in the body block
    assert 8 not in body_lines
