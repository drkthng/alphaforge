import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from alphaforge.config import load_config
from alphaforge.database import SessionLocal
from alphaforge.ingestion.ingest import ingest_stats
from alphaforge.repository import StrategyRepository, BacktestRepository

app = typer.Typer(name="alphaforge", help="AlphaForge — RealTest strategy manager")
ingest_app = typer.Typer(help="Ingestion commands")
list_app = typer.Typer(help="List commands")
app.add_typer(ingest_app, name="ingest")
app.add_typer(list_app, name="list")

console = Console()

@ingest_app.command("stats")
def ingest_stats_cmd(
    csv_path: Path = typer.Argument(..., help="Path to the RealTest stats CSV file"),
    equity: Optional[Path] = typer.Option(None, "--equity", help="Path to the equity curve CSV file"),
    rts: Optional[Path] = typer.Option(None, "--rts", help="Path to the strategy .rts file"),
    reports: Optional[Path] = typer.Option(None, "--reports", help="Directory containing HTML reports"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Override strategy name"),
    universe: Optional[str] = typer.Option(None, "--universe", help="Universe name"),
    duplicate_note: Optional[str] = typer.Option(None, "--duplicate-note", help="Note for duplicate runs")
):
    """Ingest backtest results from a RealTest stats CSV."""
    config = load_config()
    session = SessionLocal()
    
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
        
        console.print(f"[green]Successfully ingested {len(runs)} runs.[/green]")
        
        table = Table(title="Ingested Runs")
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
        console.print(f"[red]Error during ingestion: {e}[/red]")
        raise typer.Exit(code=1)
    finally:
        session.close()

@ingest_app.command("scan")
def scan_dir(
    directory: Path = typer.Argument(..., help="Directory to scan for .csv files"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Override strategy name")
):
    """Scan a directory for CSV files and ingest them."""
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        console.print(f"[yellow]No CSV files found in {directory}[/yellow]")
        return
        
    console.print(f"Found {len(csv_files)} CSV files. Starting ingestion...")
    for csv_file in csv_files:
        console.print(f"Processing [cyan]{csv_file.name}[/cyan]...")
        # Since we're in a simple CLI, we'll just call the other command logic or ingest_stats
        # For simplicity in this script, we'll re-open sessions
        ingest_stats_cmd(csv_path=csv_file, strategy=strategy)

@list_app.command("strategies")
def list_strategies():
    """List all strategies in the database."""
    session = SessionLocal()
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
    session = SessionLocal()
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
    session = SessionLocal()
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
