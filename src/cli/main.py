"""
main.py – CLI-Einstiegspunkt (Click)

Kommandos:
  analyze   – Hauptanalyse eines SCL-FB
  profiles  – Verfügbare S7-300 CPU-Profile auflisten
"""
from __future__ import annotations
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

console = Console()


@click.group()
@click.version_option("1.0.0", prog_name="scl-analyzer")
def cli():
    """SCL Runtime Analyzer – WCET-Analyse für Siemens S7-300 Funktionsbausteine."""
    pass


@cli.command()
@click.argument("scl_file", type=click.Path(exists=True, path_type=Path))
@click.option("--cpu",        required=True,  help="S7-300 CPU-Profil (z.B. S7-300-CPU315-2DP)")
@click.option("--cycle-time", required=True,  help="Zykluszeit in ms (z.B. 10ms)")
@click.option("--export",     type=click.Choice(["json", "html", "csv", "text"], case_sensitive=False),
              help="Exportformat: json|html|csv|text")
@click.option("--output",     default=None,   type=click.Path(path_type=Path),
              help="Ausgabepfad für den Export")
@click.option("--max-iter",   default=100,    show_default=True,
              help="Maximale Iterationszahl für WHILE/REPEAT-Schleifen")
def analyze(scl_file: Path, cpu: str, cycle_time: str,
            export: str | None, output: Path | None, max_iter: int):
    """
    Analysiert einen SCL-Funktionsbaustein (FB) und berechnet WCET/BCET.

    SCL_FILE  Pfad zur kompilierbaren SCL-FB-Quelldatei (SIMATIC Manager Export)
    """
    from ..profiles.profile_loader import ProfileLoader
    from ..parser.scl_parser import SCLParser
    from ..semantic.semantic_analyzer import SemanticAnalyzer
    from ..ir.ir_generator import IRGenerator
    from ..cfg.cfg_builder import CFGBuilder
    from ..wcet.wcet_engine import WCETEngine
    from ..wcet.hotspot_detector import HotspotDetector
    from ..reporter.reporter import Reporter

    # Zykluszeit parsen
    try:
        cycle_ms = _parse_time_ms(cycle_time)
    except ValueError as e:
        console.print(f"[red]Fehler:[/red] {e}")
        sys.exit(1)

    console.print(Panel(
        f"[bold blue]SCL Runtime Analyzer v1.0.0[/bold blue]  |  "
        f"Zielplattform: Siemens S7-300",
        expand=False
    ))

    # 1. CPU-Profil laden
    with console.status(f"[1/3] CPU-Profil '[cyan]{cpu}[/cyan]' laden..."):
        try:
            profile = ProfileLoader().load(cpu)
        except FileNotFoundError as e:
            console.print(f"[red]Fehler:[/red] {e}")
            sys.exit(1)
    console.print(f"[green]✓[/green] CPU-Profil geladen: {profile}")

    # 2. Parsing
    with console.status(f"[1/3] Parsing SCL-FB '[cyan]{scl_file.name}[/cyan]'..."):
        try:
            parser = SCLParser()
            ast = parser.parse_file(scl_file)
        except (FileNotFoundError, ValueError, NotImplementedError) as e:
            console.print(f"[red]Fehler:[/red] {e}")
            sys.exit(1)
    console.print(f"[green]✓[/green] Parsing abgeschlossen: FB '{ast.name}'")

    # 3. Semantik
    with console.status("[2/3] Semantikanalyse & IR-Erzeugung..."):
        symbol_table = SemanticAnalyzer(profile).analyze(ast)
        ir_blocks    = IRGenerator(profile, symbol_table).generate(ast)
        cfg          = CFGBuilder().build(ir_blocks)
        
        # Schleifen-Schranken auflösen
        loop_nodes = _collect_loops(ast)
        from ..wcet.loop_bound import LoopBoundAnnotator
        cfg = LoopBoundAnnotator(max_iterations=max_iter).annotate(cfg, loop_nodes)
        
    console.print(f"[green]✓[/green] CFG erstellt: {len(cfg)} Blöcke (Schleifen aufgelöst)")

    # 4. WCET
    with console.status("[3/3] WCET-Berechnung..."):
        result   = WCETEngine(cycle_ms).analyze(cfg, fb_name=ast.name)
        hotspots = HotspotDetector().detect(result.critical_path_blocks, result.wcet_ns)

    _print_results(result, hotspots)

    # Export
    # Falls --output angegeben ist, aber --export fehlt: Format aus Dateiendung ableiten
    if not export and output and not output.is_dir():
        suffix = output.suffix.lower().lstrip('.')
        if suffix in ["json", "html", "csv", "text", "txt"]:
            export = "text" if suffix in ["txt", "text"] else suffix

    if export:
        # Falls output ein existierender Ordner ist, Standard-Dateinamen anhängen
        if output and output.is_dir():
            out = output / f"report_{scl_file.stem}.{export.lower()}"
        else:
            out = output or Path(f"report_{scl_file.stem}.{export.lower()}")

        try:
            Reporter().export(result, hotspots, fmt=export, output=out)
            console.print(f"\n[green]Ergebnis gespeichert:[/green] {out}")
        except Exception as e:
            console.print(f"\n[red]Fehler beim Exportieren:[/red] {e}")
            sys.exit(1)

    sys.exit(0 if result.passed else 1)


@cli.command()
def profiles():
    """Listet alle verfügbaren S7-300 CPU-Profile auf."""
    from ..profiles.profile_loader import ProfileLoader
    from ..profiles.cpu_profile import CPUProfile

    loader   = ProfileLoader()
    available = loader.list_available()

    if not available:
        console.print("[yellow]Keine CPU-Profile gefunden.[/yellow]")
        return

    table = Table(title="Verfügbare S7-300 CPU-Profile", box=box.ROUNDED)
    table.add_column("Profil-Name",  style="cyan")
    table.add_column("Taktfrequenz", justify="right")
    table.add_column("Beschreibung")

    for name in sorted(available):
        p = loader.load(name)
        table.add_row(name, f"{p.clock_mhz:.0f} MHz", p._model.description)

    console.print(table)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _parse_time_ms(s: str) -> float:
    """Parst Zeitangaben wie '10ms', '0.5s', '10' (als ms)."""
    s = s.strip().lower()
    if s.endswith("ms"):
        return float(s[:-2])
    if s.endswith("s"):
        return float(s[:-1]) * 1000.0
    return float(s)


def _print_results(result, hotspots) -> None:
    status = "[bold green]PASS[/bold green]" if result.passed else "[bold red]FAIL[/bold red]"

    summary = Table(box=box.ROUNDED, show_header=True)
    summary.add_column("Kennzahl", style="bold")
    summary.add_column("Wert", justify="right")
    summary.add_row("WCET (Worst Case)",   f"{result.wcet_ms:.3f} ms")
    summary.add_row("BCET (Best Case)",    f"{result.bcet_ms:.3f} ms")
    summary.add_row("Zykluszeit",          f"{result.cycle_time_ms:.1f} ms")
    summary.add_row("Sicherheitspuffer",   f"{result.safety_margin_pct:.1f}%")
    summary.add_row("Bewertung",           status)
    console.print("\n", summary)

    if hotspots:
        hs_table = Table(title="Top Hotspots", box=box.ROUNDED)
        hs_table.add_column("#",       justify="right")
        hs_table.add_column("Zeilen")
        hs_table.add_column("Latenz",  justify="right")
        hs_table.add_column("Anteil",  justify="right")
        hs_table.add_column("Hinweis")
        for i, h in enumerate(hotspots, 1):
            hs_table.add_row(
                str(i),
                f"{h.source_line_start}–{h.source_line_end}",
                f"{h.latency_ns/1e6:.3f} ms",
                f"{h.share_pct:.0f}%",
                h.hint,
            )
        console.print(hs_table)


def _collect_loops(node) -> list:
    """Sammelt alle Schleifenknoten aus dem AST in Preorder-Reihenfolge."""
    from ..parser.ast_nodes import ForNode, WhileNode, RepeatNode, FunctionBlockNode, StatementListNode, IfNode, CaseNode
    loops = []
    if isinstance(node, (ForNode, WhileNode, RepeatNode)):
        loops.append(node)
    
    # Kinder traversieren
    if isinstance(node, FunctionBlockNode):
        if node.body:
            loops.extend(_collect_loops(node.body))
    elif isinstance(node, StatementListNode):
        for stmt in node.statements:
            loops.extend(_collect_loops(stmt))
    elif isinstance(node, IfNode):
        loops.extend(_collect_loops(node.then_body))
        for cond, body in node.elsif_branches:
            loops.extend(_collect_loops(body))
        if node.else_body:
            loops.extend(_collect_loops(node.else_body))
    elif isinstance(node, ForNode):
        if node.body:
            loops.extend(_collect_loops(node.body))
    elif isinstance(node, WhileNode):
        if node.body:
            loops.extend(_collect_loops(node.body))
    elif isinstance(node, RepeatNode):
        if node.body:
            loops.extend(_collect_loops(node.body))
    elif isinstance(node, CaseNode):
        for val, body in node.branches:
            loops.extend(_collect_loops(body))
        if node.else_body:
            loops.extend(_collect_loops(node.else_body))
    return loops
