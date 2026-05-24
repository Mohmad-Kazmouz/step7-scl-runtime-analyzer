"""
reporter.py – Ergebnis-Export (JSON, HTML, CSV, Text)

Wandelt ein WCETResult + Hotspot-Liste in das gewünschte Ausgabeformat.
HTML-Export nutzt ein Jinja2-Template (templates/report.html.j2).
"""
from __future__ import annotations
import json
import csv
import io
from pathlib import Path
from ..wcet.wcet_engine import WCETResult
from ..wcet.hotspot_detector import Hotspot

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class Reporter:
    """
    Exportiert Analyseergebnisse in verschiedene Formate.

    Verwendung::

        reporter = Reporter()
        reporter.export(result, hotspots, fmt="html", output=Path("./report.html"))
    """

    SUPPORTED_FORMATS = ("json", "html", "csv", "text")

    def export(
        self,
        result: WCETResult,
        hotspots: list[Hotspot],
        fmt: str,
        output: Path,
    ) -> None:
        """
        Exportiert das Ergebnis in die angegebene Datei.

        :param result:   WCET-Analyseergebnis
        :param hotspots: Erkannte Hotspots
        :param fmt:      Ausgabeformat ('json' | 'html' | 'csv' | 'text')
        :param output:   Zielpfad der Ausgabedatei
        :raises ValueError: Unbekanntes Format
        """
        fmt = fmt.lower()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unbekanntes Format '{fmt}'. "
                f"Unterstützt: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        content = getattr(self, f"_render_{fmt}")(result, hotspots)
        output.write_text(content, encoding="utf-8")

    # ── Render-Methoden ───────────────────────────────────────────────────────

    def _render_json(self, result: WCETResult, hotspots: list[Hotspot]) -> str:
        data = {
            "fb_name":         result.fb_name,
            "wcet_ms":         round(result.wcet_ms, 4),
            "bcet_ms":         round(result.bcet_ms, 4),
            "cycle_time_ms":   round(result.cycle_time_ms, 4),
            "safety_margin_pct": round(result.safety_margin_pct, 2),
            "passed":          result.passed,
            "hotspots": [
                {
                    "block_id":    h.block_id,
                    "lines":       f"{h.source_line_start}-{h.source_line_end}",
                    "latency_ms":  round(h.latency_ns / 1e6, 4),
                    "share_pct":   round(h.share_pct, 1),
                    "hint":        h.hint,
                }
                for h in hotspots
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _render_text(self, result: WCETResult, hotspots: list[Hotspot]) -> str:
        lines = [
            "=" * 60,
            f"SCL Runtime Analyzer – Ergebnis: {result.fb_name}",
            "=" * 60,
            f"  WCET (Worst Case):   {result.wcet_ms:.3f} ms",
            f"  BCET (Best Case):    {result.bcet_ms:.3f} ms",
            f"  Zykluszeit:          {result.cycle_time_ms:.1f} ms",
            f"  Sicherheitspuffer:   {result.safety_margin_pct:.1f}%",
            f"  Bewertung:           {'[PASS]' if result.passed else '[FAIL]'}",
            "",
            "TOP HOTSPOTS",
            "-" * 60,
        ]
        for i, h in enumerate(hotspots, 1):
            lines.append(
                f"  #{i}  Zeilen {h.source_line_start}-{h.source_line_end}"
                f"  {h.latency_ns/1e6:.3f}ms  ({h.share_pct:.0f}%)"
            )
            lines.append(f"      Hinweis: {h.hint}")
        return "\n".join(lines)

    def _render_csv(self, result: WCETResult, hotspots: list[Hotspot]) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["FB", "WCET_ms", "BCET_ms", "Zykluszeit_ms", "Puffer_%", "Bestanden"])
        w.writerow([
            result.fb_name,
            round(result.wcet_ms, 4),
            round(result.bcet_ms, 4),
            round(result.cycle_time_ms, 1),
            round(result.safety_margin_pct, 2),
            result.passed,
        ])
        w.writerow([])
        w.writerow(["Block", "Zeilen", "Latenz_ms", "Anteil_%", "Hinweis"])
        for h in hotspots:
            w.writerow([
                h.block_id,
                f"{h.source_line_start}-{h.source_line_end}",
                round(h.latency_ns / 1e6, 4),
                round(h.share_pct, 1),
                h.hint,
            ])
        return buf.getvalue()

    def _render_html(self, result: WCETResult, hotspots: list[Hotspot]) -> str:
        """Rendert den HTML-Report (Jinja2-Template)."""
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))
            tmpl = env.get_template("report.html.j2")
            return tmpl.render(result=result, hotspots=hotspots)
        except Exception:
            # Fallback: einfaches HTML ohne Template
            return self._render_html_inline(result, hotspots)

    def _render_html_inline(self, result: WCETResult, hotspots: list[Hotspot]) -> str:
        status_color = "#2e7d32" if result.passed else "#c62828"
        hs_rows = "".join(
            f"<tr><td>{i}</td><td>{h.source_line_start}–{h.source_line_end}</td>"
            f"<td>{h.latency_ns/1e6:.3f}</td><td>{h.share_pct:.0f}%</td>"
            f"<td>{h.hint}</td></tr>"
            for i, h in enumerate(hotspots, 1)
        )
        return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<title>SCL Runtime Analyzer – {result.fb_name}</title>
<style>body{{font-family:Arial,sans-serif;margin:2em;}}
table{{border-collapse:collapse;width:100%;}}
th{{background:#1f3864;color:#fff;padding:8px;}}
td{{padding:6px;border:1px solid #bdd7ee;}}
.badge{{display:inline-block;padding:4px 12px;color:#fff;
  background:{status_color};border-radius:4px;font-weight:bold;}}
</style></head><body>
<h1>SCL Runtime Analyzer</h1>
<h2>Funktionsbaustein: {result.fb_name}</h2>
<table><tr><th>Kennzahl</th><th>Wert</th></tr>
<tr><td>WCET</td><td>{result.wcet_ms:.3f} ms</td></tr>
<tr><td>BCET</td><td>{result.bcet_ms:.3f} ms</td></tr>
<tr><td>Zykluszeit</td><td>{result.cycle_time_ms:.1f} ms</td></tr>
<tr><td>Sicherheitspuffer</td><td>{result.safety_margin_pct:.1f}%</td></tr>
<tr><td>Bewertung</td><td><span class="badge">{"PASS" if result.passed else "FAIL"}</span></td></tr>
</table>
<h3>Hotspots</h3>
<table><tr><th>#</th><th>Zeilen</th><th>Latenz (ms)</th><th>Anteil</th><th>Hinweis</th></tr>
{hs_rows}</table></body></html>"""
