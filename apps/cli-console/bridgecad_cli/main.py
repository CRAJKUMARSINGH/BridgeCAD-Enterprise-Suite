"""
BridgeCAD Enterprise — CLI console (M7).

Real commands:
  bridgecad draw gad   <input.xlsx> -o <outdir>   → 7-sheet DXF package
  bridgecad validate   <input.xlsx>               → QA compliance check
  bridgecad bill gen   <input.xlsx> -o <outdir>   → Excel + CSV BOQ
  bridgecad export all <input.xlsx> -o <outdir>   → full ZIP bundle
  bridgecad plugin list / info <id>
  bridgecad template new <type> -o <out.xlsx>
  bridgecad version / health
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel

# ── sys.path bootstrapping (dev install without pip editable) ─────────────
_SUITE = Path(__file__).parents[3]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export",
             "bridgecad-plugins"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

__version__  = "0.1.0-rc1"
__codename__ = "BRIDGECAD-OSS-1.0"

logging.basicConfig(level=logging.WARNING)

console = Console()
app = typer.Typer(
    name="bridgecad",
    help="🌉 BridgeCAD Enterprise Suite — AI-powered bridge GAD generator.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Sub-app groups
draw_app     = typer.Typer(help="DXF drawing generation.",      no_args_is_help=True)
bill_app     = typer.Typer(help="Bill of Quantities.",          no_args_is_help=True)
export_app   = typer.Typer(help="Unified export → ZIP bundle.", no_args_is_help=True)
plugin_app   = typer.Typer(help="Plugin management.",          no_args_is_help=True)
template_app = typer.Typer(help="Excel template operations.",  no_args_is_help=True)

app.add_typer(draw_app,     name="draw")
app.add_typer(bill_app,     name="bill")
app.add_typer(export_app,   name="export")
app.add_typer(plugin_app,   name="plugin")
app.add_typer(template_app, name="template")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_project(xlsx: Path):
    """Load an Excel workbook into a BridgeProject."""
    from bridgecad_io.excel_reader import read_excel
    return read_excel(xlsx)


def _resolve_output(output: Optional[Path], suffix: str) -> Path:
    p = output or Path.cwd() / "output"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Root commands
# ---------------------------------------------------------------------------

@app.command("version")
def version_cmd(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    """Show BridgeCAD version."""
    console.print(Panel(
        f"[bold cyan]{__codename__}[/]  [green]v{__version__}[/]\n"
        "[dim]Python ≥ 3.11  |  ezdxf ≥ 1.4  |  Pydantic V2[/]",
        title="🌉 BridgeCAD Enterprise Suite", expand=False,
    ))


@app.command("health")
def health_cmd() -> None:
    """Run health probes on all packages."""
    checks = []
    pkgs = {
        "bridgecad_core":    "types, models, geometry, validation",
        "bridgecad_io":      "excel_reader, excel_template",
        "bridgecad_draw":    "7 drawing sheets + booklet",
        "bridgecad_bill":    "rates_db, processor, formatters",
        "bridgecad_qa":      "rules_engine, compliance, reports",
        "bridgecad_export":  "orchestrator, bundler",
        "bridgecad_plugins": "registry (3 built-in plugins)",
    }
    for pkg, desc in pkgs.items():
        try:
            __import__(pkg)
            checks.append((pkg, "✅ OK",  desc))
        except Exception as e:
            checks.append((pkg, f"❌ {e}", desc))

    t = Table(title="Package Health", show_lines=False)
    t.add_column("Package",     style="cyan", min_width=22)
    t.add_column("Status",      min_width=8)
    t.add_column("Provides",    style="dim")
    for pkg, status, desc in checks:
        t.add_row(pkg, status, desc)
    console.print(t)


@app.command("validate")
def validate_cmd(
    input_file: Path = typer.Argument(..., help="Path to BridgeCAD Excel workbook"),
    report_html: Optional[Path] = typer.Option(None, "--report", "-r",
                                               help="Save HTML QA report here"),
) -> None:
    """Validate an Excel workbook against all 30 IRC/MORTH checks."""
    if not input_file.exists():
        console.print(f"[red]File not found: {input_file}[/]"); raise typer.Exit(1)
    with console.status("Loading workbook …"):
        project = _load_project(input_file)
    with console.status("Running 30 QA checks …"):
        from bridgecad_core.validation import run_all
        from bridgecad_qa.compliance   import score as _score
        report = run_all(project)
        comp   = _score(report)

    colour = "green" if comp.grade in ("A+","A") else \
             "yellow" if comp.grade in ("B","C") else "red"
    console.print(Panel(
        f"[bold {colour}]Score: {comp.overall}/100  Grade: {comp.grade}[/]\n"
        f"Critical fails: {comp.critical_fails}  |  "
        f"Warning fails: {comp.warning_fails}  |  "
        f"Total checks: {len(report.findings)}",
        title="🔍 QA Compliance Result",
    ))

    # Show failures
    fails = report.failed_findings()
    if fails:
        t = Table(title="Failed Checks", show_lines=False)
        t.add_column("ID",  style="red",  width=6)
        t.add_column("Sev", width=10)
        t.add_column("Message")
        for f in fails:
            t.add_row(f.check_id,
                      f.severity.name if hasattr(f.severity,"name") else str(f.severity),
                      f.message)
        console.print(t)

    if report_html:
        from bridgecad_qa.reports import generate_html_report
        generate_html_report(report, report_html, project)
        console.print(f"[green]HTML report saved:[/] {report_html}")

    raise typer.Exit(0 if comp.critical_fails == 0 else 1)


# ---------------------------------------------------------------------------
# draw sub-commands
# ---------------------------------------------------------------------------

@draw_app.command("gad")
def draw_gad_cmd(
    input_file: Path  = typer.Argument(..., help="BridgeCAD Excel workbook"),
    output_dir: Path  = typer.Option(Path("./output/drawings"), "-o", "--output"),
    scale:      int   = typer.Option(100, "-s", "--scale", help="Plot scale denominator"),
    prefix:     str   = typer.Option("GAD",      "-p", "--prefix"),
) -> None:
    """Generate a 7-sheet GAD DXF package from an Excel workbook."""
    if not input_file.exists():
        console.print(f"[red]Not found: {input_file}[/]"); raise typer.Exit(1)
    with console.status("Loading workbook …"):
        project = _load_project(input_file)
    with console.status(f"Generating 7-sheet DXF package → {output_dir} …"):
        from bridgecad_draw.booklet import generate_package
        sheets = generate_package(project, output_dir,
                                  prefix=prefix, scale_denom=scale)

    t = Table(title=f"📐 DXF Package — {len(sheets)}/7 sheets")
    t.add_column("Sheet", style="cyan")
    t.add_column("Size", justify="right")
    for p in sheets:
        t.add_row(p.name, f"{p.stat().st_size//1024} KB")
    console.print(t)
    console.print(f"[green]Done.[/] Total: "
                  f"{sum(p.stat().st_size for p in sheets)//1024} KB")


# ---------------------------------------------------------------------------
# bill sub-commands
# ---------------------------------------------------------------------------

@bill_app.command("gen")
def bill_gen_cmd(
    input_file: Path          = typer.Argument(..., help="BridgeCAD Excel workbook"),
    output_dir: Path          = typer.Option(Path("./output/bill"), "-o", "--output"),
    fmt:        str           = typer.Option("all",   "--format", "-f",
                                              help="all | excel | csv"),
    state:      Optional[str] = typer.Option(None,    "--state",  "-S",
                                              help="State code for PWD rates (e.g. MH)"),
) -> None:
    """Extract quantities and generate priced Bill of Quantities."""
    if not input_file.exists():
        console.print(f"[red]Not found: {input_file}[/]"); raise typer.Exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)
    with console.status("Loading workbook …"):
        project = _load_project(input_file)
    with console.status("Extracting quantities and pricing …"):
        from bridgecad_bill.processor           import extract_and_price
        from bridgecad_bill.formatters.excel_formatter import format_excel
        from bridgecad_bill.formatters.csv_formatter   import format_csv
        boq = extract_and_price(project, state=state)

    stem = input_file.stem
    saved = []
    if fmt in ("all", "excel"):
        p = format_excel(boq, output_dir / f"{stem}_BOQ.xlsx")
        saved.append(p)
    if fmt in ("all", "csv"):
        p = format_csv(boq,   output_dir / f"{stem}_BOQ.csv")
        saved.append(p)

    console.print(Panel(
        f"Grand Total: [bold green]INR {float(boq.grand_total):,.0f}[/]\n"
        f"Sub-total: INR {float(boq.subtotal):,.0f}\n"
        f"Contingency ({boq.contingency_pct}%): INR {float(boq.contingency_amount):,.0f}",
        title="💰 BOQ Summary",
    ))
    for p in saved:
        console.print(f"  [cyan]{p}[/]")


# ---------------------------------------------------------------------------
# export sub-commands
# ---------------------------------------------------------------------------

@export_app.command("all")
def export_all_cmd(
    input_file: Path          = typer.Argument(..., help="BridgeCAD Excel workbook"),
    output_dir: Path          = typer.Option(Path("./output"), "-o", "--output"),
    state:      Optional[str] = typer.Option(None, "--state", "-S"),
    scale:      int           = typer.Option(100, "--scale", "-s"),
) -> None:
    """Full export: 7-sheet DXF + BOQ (xlsx+csv) + QA HTML → ZIP bundle."""
    if not input_file.exists():
        console.print(f"[red]Not found: {input_file}[/]"); raise typer.Exit(1)
    with console.status("Loading workbook …"):
        project = _load_project(input_file)
    with console.status("Running full export pipeline …"):
        from bridgecad_export.orchestrator import export_all
        bundle = export_all(project, output_dir,
                            prefix=input_file.stem,
                            state=state, scale_denom=scale)
    size_kb = bundle.stat().st_size // 1024
    console.print(Panel(
        f"[bold green]{bundle.name}[/]  ({size_kb} KB)\n"
        f"Contents: DXF drawings + BOQ Excel/CSV + QA HTML report",
        title="📦 Export Bundle Complete",
    ))


# ---------------------------------------------------------------------------
# plugin sub-commands
# ---------------------------------------------------------------------------

@plugin_app.command("list")
def plugin_list_cmd() -> None:
    """List all installed/available plugins."""
    from bridgecad_plugins.registry import get_registry
    reg = get_registry()
    t = Table(title=f"Installed Plugins ({len(reg)} total)")
    t.add_column("ID",          style="cyan")
    t.add_column("Name")
    t.add_column("Version",     justify="center")
    t.add_column("Span range",  justify="center")
    t.add_column("Bridge types")
    for p in reg.all():
        t.add_row(
            p.plugin_id, p.name, p.version,
            f"{p.span_range_m[0]}–{p.span_range_m[1]} m",
            ", ".join(p.bridge_types),
        )
    console.print(t)


@plugin_app.command("info")
def plugin_info_cmd(
    plugin_id: str = typer.Argument(..., help="Plugin ID to inspect"),
) -> None:
    """Show full details for a plugin."""
    from bridgecad_plugins.registry import get_registry
    from bridgecad_plugins.runner   import PluginRunner
    reg = get_registry()
    m   = reg.get(plugin_id)
    if not m:
        console.print(f"[red]Plugin not found: {plugin_id}[/]"); raise typer.Exit(1)
    runner = PluginRunner(m)
    console.print(Panel(runner.describe(), title=f"🔌 {m.name}  [{m.plugin_id} v{m.version}]"))


# ---------------------------------------------------------------------------
# template sub-commands
# ---------------------------------------------------------------------------

@template_app.command("new")
def template_new_cmd(
    bridge_type: str = typer.Argument("simple_12m", help="Bridge type key"),
    output:      Path = typer.Option(Path("template.xlsx"), "-o", "--output"),
) -> None:
    """Generate a blank 14-sheet BridgeCAD Excel template."""
    with console.status(f"Generating template for type '{bridge_type}' …"):
        from bridgecad_io.excel_template import generate_template
        p = generate_template(output)
    console.print(f"[green]Template saved:[/] {p}  ({p.stat().st_size//1024} KB)")


@template_app.command("fill")
def template_fill_cmd(
    input_file: Path = typer.Argument(..., help="Existing BridgeCAD .xlsx to read"),
    output:     Path = typer.Option(None,  "-o", "--output"),
) -> None:
    """Round-trip: read Excel → BridgeProject → write back as styled template."""
    if not input_file.exists():
        console.print(f"[red]Not found: {input_file}[/]"); raise typer.Exit(1)
    out = output or input_file.parent / f"{input_file.stem}_styled.xlsx"
    with console.status("Loading …"):
        project = _load_project(input_file)
    with console.status("Writing styled template …"):
        from bridgecad_io.excel_template import generate_template
        generate_template(out, project=project)
    console.print(f"[green]Styled template:[/] {out}")


def _entry() -> None:
    app()


if __name__ == "__main__":
    _entry()
