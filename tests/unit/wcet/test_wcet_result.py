"""Unit-Tests: WCETResult"""
import pytest
from src.wcet.wcet_engine import WCETResult


def _make_result(wcet_ns, cycle_ns):
    return WCETResult(
        fb_name="TestFB",
        wcet_ns=wcet_ns,
        bcet_ns=wcet_ns * 0.3,
        cycle_time_ns=cycle_ns,
        critical_path_blocks=[],
    )


def test_pass_when_wcet_below_cycle():
    r = _make_result(wcet_ns=7_000_000, cycle_ns=10_000_000)
    assert r.passed is True


def test_fail_when_wcet_exceeds_cycle():
    r = _make_result(wcet_ns=12_000_000, cycle_ns=10_000_000)
    assert r.passed is False


def test_safety_margin_correct():
    r = _make_result(wcet_ns=8_000_000, cycle_ns=10_000_000)
    assert r.safety_margin_pct == pytest.approx(20.0)


def test_ms_conversion():
    r = _make_result(wcet_ns=7_830_000, cycle_ns=10_000_000)
    assert r.wcet_ms == pytest.approx(7.83)
