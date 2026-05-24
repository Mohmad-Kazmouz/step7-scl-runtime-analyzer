"""
test_cli_smoke.py – CLI-Smoke-Tests

Testet den Aufruf des scl-analyzer Command-Line-Interfaces
über Click's CliRunner.
"""
from __future__ import annotations
import json
from pathlib import Path
from click.testing import CliRunner
import pytest

from src.cli.main import cli


def test_cli_help():
    """Testet, ob der --help Aufruf die Hilfe ausgibt."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SCL Runtime Analyzer" in result.output
    assert "analyze" in result.output
    assert "profiles" in result.output


def test_cli_profiles():
    """Testet das 'profiles' Kommando."""
    runner = CliRunner()
    result = runner.invoke(cli, ["profiles"])
    assert result.exit_code == 0
    assert "Verfügbare S7-300 CPU-Profile" in result.output
    assert "S7-300-CPU314" in result.output
    assert "S7-300-CPU315-2DP" in result.output
    assert "S7-300-CPU317F-3" in result.output


def test_cli_analyze_success():
    """Testet eine erfolgreiche Analyse eines SCL-FB."""
    runner = CliRunner()
    scl_path = Path(__file__).parent.parent / "fixtures" / "scl_samples" / "FB_Simple.scl"
    
    result = runner.invoke(cli, [
        "analyze",
        str(scl_path),
        "--cpu", "S7-300-CPU315-2DP",
        "--cycle-time", "10ms"
    ])
    
    assert result.exit_code == 0
    assert "Parsing abgeschlossen: FB 'FB_Simple'" in result.output
    assert "WCET (Worst Case)" in result.output
    assert "BCET (Best Case)" in result.output
    assert "Top Hotspots" in result.output
    assert "PASS" in result.output


def test_cli_analyze_missing_file():
    """Testet das Verhalten bei einer nicht existierenden SCL-Datei."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "analyze",
        "non_existent_file.scl",
        "--cpu", "S7-300-CPU315-2DP",
        "--cycle-time", "10ms"
    ])
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "existiert nicht" in result.output.lower()


def test_cli_analyze_invalid_export():
    """Testet die Fehlermeldung bei falschem Exportformat."""
    runner = CliRunner()
    scl_path = Path(__file__).parent.parent / "fixtures" / "scl_samples" / "FB_Simple.scl"
    
    result = runner.invoke(cli, [
        "analyze",
        str(scl_path),
        "--cpu", "S7-300-CPU315-2DP",
        "--cycle-time", "10ms",
        "--export", "invalid_format"
    ])
    assert result.exit_code != 0
    assert "Invalid value for '--export'" in result.output


def test_cli_analyze_export_autodetect(tmp_path: Path):
    """Testet den automatischen Export-Format-Detektor über die Dateiendung."""
    runner = CliRunner()
    scl_path = Path(__file__).parent.parent / "fixtures" / "scl_samples" / "FB_Simple.scl"
    out_file = tmp_path / "result.json"
    
    result = runner.invoke(cli, [
        "analyze",
        str(scl_path),
        "--cpu", "S7-300-CPU315-2DP",
        "--cycle-time", "10ms",
        "--output", str(out_file)
    ])
    
    assert result.exit_code == 0
    assert out_file.exists()
    
    # Inhalt der JSON-Datei validieren
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["fb_name"] == "FB_Simple"
    assert "wcet_ms" in data
    assert "bcet_ms" in data
    assert data["passed"] is True
