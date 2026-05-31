"""End-to-end test: real ANTLR parser through WCET pipeline."""
from pathlib import Path

from src.cfg.cfg_builder import CFGBuilder
from src.cli.main import _collect_loops
from src.ir.ir_generator import IRGenerator
from src.parser.scl_parser import SCLParser
from src.profiles.profile_loader import ProfileLoader
from src.semantic.semantic_analyzer import SemanticAnalyzer
from src.wcet.hotspot_detector import HotspotDetector
from src.wcet.loop_bound import LoopBoundAnnotator, collect_var_literal_inits
from src.wcet.wcet_engine import WCETEngine


def test_full_pipeline_fb10():
    scl = (
        Path(__file__).parent.parent / "fixtures" / "scl_samples" / "FB10_Regelung.scl"
    )
    profile = ProfileLoader().load("S7-300-CPU315-2DP")
    ast = SCLParser().parse_file(scl)
    st = SemanticAnalyzer(profile).analyze(ast)
    cfg = CFGBuilder().build(IRGenerator(profile, st).generate(ast))
    cfg = LoopBoundAnnotator(max_iterations=100).annotate(
        cfg, _collect_loops(ast), var_inits=collect_var_literal_inits(ast)
    )

    result = WCETEngine(cycle_time_ms=10.0).analyze(cfg, fb_name=ast.name)
    hotspots = HotspotDetector().detect(result.critical_path_blocks, result.wcet_ns)

    assert result.wcet_ns > 0
    assert result.passed
    assert any(h.latency_ns > 0 for h in hotspots)
