"""
Integrationstest: Gesamte Analyse-Pipeline

Testet das Zusammenspiel aller Module ohne echten ANTLR-Parser
durch direkte AST-Konstruktion (simulierter Parser-Output).
"""
import pytest
from src.parser.ast_nodes import (
    FunctionBlockNode, VarSectionNode, VariableNode,
    StatementListNode, ForNode, LiteralNode, IdentifierNode,
)
from src.semantic.symbol_table import SymbolTable, Symbol, SymbolKind, StorageLocation
from src.ir.ir_nodes import IRBlock, IRInstruction, IROpcode
from src.cfg.cfg_builder import CFGBuilder
from src.cfg.cfg_graph import CFGGraph
from src.wcet.wcet_engine import WCETEngine
from src.wcet.hotspot_detector import HotspotDetector


def _make_block(bid, *lats):
    block = IRBlock(bid)
    for lat in lats:
        block.instructions.append(IRInstruction(IROpcode.ADD, latency_ns=lat))
    return block


def test_cfg_to_wcet_integration():
    """CFGBuilder → WCETEngine → WCETResult Integrationspfad."""
    b_entry = _make_block("entry", 100.0)
    b_loop  = _make_block("loop",  500.0)
    b_exit  = _make_block("exit",  80.0)

    # Manuell azyklischen CFG aufbauen (Schleife bereits aufgelöst)
    cfg = CFGGraph()
    for b in (b_entry, b_loop, b_exit):
        cfg.add_block(b)
    cfg.add_edge("entry", "loop")
    cfg.add_edge("loop",  "exit")

    engine = WCETEngine(cycle_time_ms=10.0)
    result = engine.analyze(cfg, fb_name="IntegTest_FB")

    assert result.fb_name == "IntegTest_FB"
    assert result.wcet_ns == pytest.approx(680.0)
    assert result.passed is True


def test_hotspot_detection_integration():
    """HotspotDetector identifiziert den dominanten Block korrekt."""
    b1 = _make_block("small",  100.0)
    b2 = _make_block("hot",   5000.0)   # 98% der Last
    blocks = [b1, b2]
    total_ns = sum(b.total_latency_ns for b in blocks)

    detector = HotspotDetector(threshold_pct=10.0)
    hotspots = detector.detect(blocks, total_ns)

    assert len(hotspots) >= 1
    assert hotspots[0].block_id == "hot"
    assert hotspots[0].share_pct > 80.0


def test_wcet_fail_when_over_budget():
    """FAIL wird korrekt gesetzt wenn WCET die Zykluszeit überschreitet."""
    cfg = CFGGraph()
    cfg.add_block(_make_block("only", 15_000_000.0))   # 15ms bei 10ms Zykluszeit
    result = WCETEngine(cycle_time_ms=10.0).analyze(cfg, "OverBudget_FB")
    assert result.passed is False
    assert result.safety_margin_pct < 0


def test_fb_simple_bcet_less_than_wcet():
    """End-to-end: BCET nutzt den ELSE-Zweig und ist strikt kleiner als WCET."""
    from pathlib import Path

    from src.cfg.cfg_builder import CFGBuilder
    from src.ir.ir_generator import IRGenerator
    from src.parser.scl_parser import SCLParser
    from src.profiles.profile_loader import ProfileLoader
    from src.semantic.semantic_analyzer import SemanticAnalyzer
    from src.wcet.loop_bound import LoopBoundAnnotator, collect_var_literal_inits

    scl_path = (
        Path(__file__).parent.parent / "fixtures" / "scl_samples" / "FB_Simple.scl"
    )
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    ast = SCLParser().parse_file(scl_path)
    st = SemanticAnalyzer(profile).analyze(ast)
    blocks = IRGenerator(profile, st).generate(ast)
    cfg = CFGBuilder().build(blocks)
    cfg = LoopBoundAnnotator(max_iterations=100).annotate(
        cfg, [], var_inits=collect_var_literal_inits(ast)
    )
    result = WCETEngine(cycle_time_ms=10.0).analyze(cfg, fb_name=ast.name)

    assert result.bcet_ns > 0
    assert result.bcet_ns < result.wcet_ns
