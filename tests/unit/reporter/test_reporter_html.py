"""HTML export uses Jinja2 template when present."""
from pathlib import Path

from src.reporter.reporter import Reporter, _TEMPLATE_DIR
from src.wcet.hotspot_detector import Hotspot
from src.wcet.wcet_engine import WCETResult


def test_html_uses_jinja_template():
    assert (_TEMPLATE_DIR / "report.html.j2").exists()
    result = WCETResult(
        fb_name="FB_Test",
        wcet_ns=1_000_000,
        bcet_ns=500_000,
        cycle_time_ns=10_000_000,
        critical_path_blocks=[],
    )
    html = Reporter()._render_html(result, [])
    assert "SCL Runtime Analyzer" in html
    assert "FB_Test" in html
    assert "card" in html  # template-specific class
