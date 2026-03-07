import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from alphaforge.config import load_config
from alphaforge.database import get_session
from alphaforge.ingestion.ingest import ingest_stats
from alphaforge.repository import StrategyRepository, BacktestRepository

app = typer.Typer(name="alphaforge", help="AlphaForge — RealTest strategy manager")

@app.command("init")
def init_cmd():
    """Initialize the database schema."""
    from alphaforge.database import get_engine, init_db
    init_db(get_engine())
    console.print(Panel("[bold green]✅ AlphaForge Project Initialized[/bold green]\nWelcome to AlphaForge. Your database and structure are ready.", expand=False))

@app.command("launch")
def launch_cmd():
    """Launch the AlphaForge Streamlit Dashboard."""
    import subprocess
    import sys
    console.print(Panel("[bold blue]🚀 Launching AlphaForge Dashboard[/bold blue]\nStarting the Streamlit interface...", expand=False))
    subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])

ingest_app = typer.Typer(help="Ingestion commands")
list_app = typer.Typer(help="List commands")
app.add_typer(ingest_app, name="ingest")
app.add_typer(list_app, name="list")

console = Console()

def _perform_ingestion(
    csv_path: Path,
    equity: Optional[Path] = None,
    rts: Optional[Path] = None,
    reports: Optional[Path] = None,
    strategy: Optional[str] = None,
    universe: Optional[str] = None,
    duplicate_note: Optional[str] = None
):
    """Core ingestion logic used by CLI commands."""
    config = load_config()
    session = get_session()
    
    try:
        runs = ingest_stats(
            session=session,
            csv_path=csv_path,
            config=config,
            equity_path=equity,
            rts_path=rts,
            report_dir=reports,
            strategy_name_override=strategy,
            universe_name=universe,
            duplicate_note=duplicate_note
        )
        session.commit()
        
        console.print(f"[green]Successfully ingested {len(runs)} runs from {csv_path.name}.[/green]")
        
        table = Table(title=f"Ingested Runs ({csv_path.name})")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Strategy", style="magenta")
        table.add_column("Date Range", style="green")
        table.add_column("Duplicates", style="yellow")

        for run in runs:
            table.add_row(
                str(run.id),
                run.version.strategy.name,
                f"{run.date_range_start} - {run.date_range_end}",
                "Yes" if run.duplicate_of_id else "No"
            )
        console.print(table)
        
    except Exception as e:
        session.rollback()
        console.print(f"[red]Error during ingestion of {csv_path.name}: {e}[/red]")
        # We don't raise Exit here to allow scan to continue
    finally:
        session.close()

@ingest_app.command("run")
def ingest_run_cmd(
    csv_path: Path = typer.Argument(..., help="Path to the RealTest stats CSV file"),
    equity: Optional[Path] = typer.Option(None, "--equity-csv", help="Path to the equity curve CSV file"),
    rts: Optional[Path] = typer.Option(None, "--rts", help="Path to the strategy .rts file"),
    reports: Optional[Path] = typer.Option(None, "--reports", help="Directory containing HTML reports"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Override strategy name"),
    universe: Optional[str] = typer.Option(None, "--universe", help="Universe name"),
    duplicate_note: Optional[str] = typer.Option(None, "--duplicate-note", help="Note for duplicate runs")
):
    """Ingest backtest results from a RealTest stats CSV."""
    _perform_ingestion(
        csv_path=csv_path,
        equity=equity,
        rts=rts,
        reports=reports,
        strategy=strategy,
        universe=universe,
        duplicate_note=duplicate_note
    )

@ingest_app.command("scan")
def scan_dir(
    directory: Path = typer.Argument(..., help="Directory to scan for .csv files"),
    pattern: str = typer.Option("*.csv", "--pattern", help="Glob pattern to match CSV files"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Override strategy name"),
):
    """Scan a directory for CSV files matching a pattern and ingest them."""
    csv_files = list(directory.glob(pattern))
    if not csv_files:
        console.print(f"[yellow]No files matching '{pattern}' found in {directory}[/yellow]")
        return

    console.print(f"Found {len(csv_files)} files matching '{pattern}'. Starting ingestion...")
    for csv_file in csv_files:
        _perform_ingestion(csv_path=csv_file, strategy=strategy)

@ingest_app.command("refresh")
def refresh_run(
    run_id: int = typer.Option(..., "--run-id", help="ID of the backtest run to refresh"),
):
    """Re-parse the equity curve CSV for a given run and update the parquet file."""
    session = get_session()
    b_repo = BacktestRepository(session)

    run = b_repo.get_by_id(run_id)
    if not run:
        console.print(f"[red]Run {run_id} not found.[/red]")
        raise typer.Exit(code=1)

    if not run.equity_curve_path:
        console.print(f"[yellow]Run {run_id} has no equity curve path set.[/yellow]")
        session.close()
        return

    console.print(f"[cyan]Refreshing equity data for run {run_id}...[/cyan]")
    console.print(f"  Equity path: {run.equity_curve_path}")
    console.print(f"  Strategy: {run.version.strategy.name} v{run.version.version_number}")
    console.print(f"[green]Run {run_id} info displayed. (Full re-parse requires the original CSV.)[/green]")
    session.close()


@list_app.command("strategies")
def list_strategies():
    """List all strategies in the database."""
    session = get_session()
    repo = StrategyRepository(session)
    strategies = repo.list_all()
    
    if not strategies:
        console.print("[yellow]No strategies found.[/yellow]")
        return
        
    table = Table(title="Strategies")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    for s in strategies:
        table.add_row(str(s.id), s.name, s.status.value, s.created_at.strftime("%Y-%m-%d"))
    
    console.print(table)
    session.close()

@list_app.command("runs")
def list_runs(strategy: Optional[str] = typer.Option(None, "--strategy", help="Filter by strategy name")):
    """List backtest runs."""
    session = get_session()
    repo = BacktestRepository(session)
    
    if strategy:
        strat_repo = StrategyRepository(session)
        s_obj = strat_repo.find_by_name(strategy)
        if not s_obj:
            console.print(f"[red]Strategy '{strategy}' not found.[/red]")
            return
        runs = repo.list_by_strategy(s_obj.id)
    else:
        # Simplification: just query all runs directly if no filter
        from sqlalchemy import select
        from alphaforge.models import BacktestRun
        runs = session.scalars(select(BacktestRun)).all()
        
    if not runs:
        console.print("[yellow]No runs found.[/yellow]")
        return
        
    table = Table(title="Backtest Runs")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Strategy", style="magenta")
    table.add_column("Version", justify="right")
    table.add_column("Date Range", style="green")
    table.add_column("Sharpe", justify="right")

    for r in runs:
        metrics = r.metrics[0] if r.metrics else None
        sharpe = f"{metrics.sharpe:.2f}" if metrics and metrics.sharpe else "N/A"
        table.add_row(
            str(r.id),
            r.version.strategy.name,
            f"v{r.version.version_number}",
            f"{r.date_range_start} - {r.date_range_end}",
            sharpe
        )
    
    console.print(table)
    session.close()

@app.command("show")
def show_run(run_id: int):
    """Show detailed information for a specific run."""
    session = get_session()
    repo = BacktestRepository(session)
    run = repo.get_by_id(run_id)
    
    if not run:
        console.print(f"[red]Run {run_id} not found.[/red]")
        return
        
    console.print(f"[bold cyan]Run {run.id} Details[/bold cyan]")
    console.print(f"Strategy: [magenta]{run.version.strategy.name}[/magenta] (v{run.version.version_number})")
    console.print(f"Date Range: {run.date_range_start} to {run.date_range_end}")
    console.print(f"Run Date: {run.run_date}")
    
    if run.metrics:
        m = run.metrics[0]
        console.print("\n[bold green]Metrics:[/bold green]")
        console.print(f"  Net Profit: {m.net_profit}")
        console.print(f"  Sharpe: {m.sharpe}")
        console.print(f"  Max DD: {m.max_drawdown}")
        
    console.print("\n[bold yellow]Parameters:[/bold yellow]")
    for k, v in run.parameters_json.items():
        console.print(f"  {k}: {v}")
        
    session.close()

if __name__ == "__main__":
    app()
