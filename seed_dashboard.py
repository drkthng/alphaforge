import random
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from pathlib import Path
from alphaforge.config import load_config
from alphaforge.database import get_engine, SessionLocal
from alphaforge.models import (
    Base, Strategy, StrategyVersion, BacktestRun, RunMetric, 
    Universe, StrategyStatus, NoteType, AttachmentType, ArtifactType
)
from alphaforge.repository import (
    StrategyRepository, VersionRepository, BacktestRepository, 
    MetricsRepository, UniverseRepository, NoteRepository, 
    AttachmentRepository, ArtifactRepository
)

def seed():
    config = load_config()
    engine = get_engine(config.database.path)
    Session = SessionLocal(engine)
    session = Session()
    
    strat_repo = StrategyRepository(session)
    v_repo = VersionRepository(session)
    b_repo = BacktestRepository(session)
    m_repo = MetricsRepository(session)
    u_repo = UniverseRepository(session)
    note_repo = NoteRepository(session)
    attach_repo = AttachmentRepository(session)
    artifact_repo = ArtifactRepository(session)
    
    # Ensure directories exist
    base_data = Path("data")
    equity_dir = base_data / "equity_curves"
    trade_dir = base_data / "trade_logs"
    archive_dir = base_data / "archive"
    report_dir = base_data / "reports"
    attach_dir = base_data / "attachments"
    
    for d in [equity_dir, trade_dir, archive_dir, report_dir, attach_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Create Universes
    universes = []
    for u_name in ["S&P 500", "Nasdaq 100", "Russell 2000", "All Equities"]:
        u = u_repo.find_by_name(u_name)
        if not u:
            u = u_repo.create(name=u_name)
        universes.append(u)
    
    # Create Strategies
    statuses = list(StrategyStatus)
    strategy_names = [
        "Mean Reversion Alpha", "Trend Follower Pro", "Earnings Gap Hunter",
        "Volatility Breakout", "Pairs Trading Engine", "Sector Rotation",
        "Institutional Flow", "Dark Pool Tracker", "Sentiment Divergence",
        "Gamma Squeeze Scout"
    ]
    
    strategies = []
    for name in strategy_names:
        strat = strat_repo.find_by_name(name)
        if not strat:
            strat = strat_repo.create(
                name=name, 
                description=f"Quantitative research for {name}",
                status=random.choice(statuses)
            )
        strategies.append(strat)
    
    session.commit()
    
    # Add Notes and Attachments to Strategies
    for strat in strategies:
        # Notes
        num_notes = random.randint(2, 4)
        for i in range(num_notes):
            note_repo.create(
                strategy_id=strat.id,
                title=f"Seed Note {i+1} for {strat.name}",
                body=f"This is a synthetic research note for **{strat.name}**.\n\n- Point 1\n- Point 2\n\nGenerated at {datetime.now()}.",
                note_type=random.choice(list(NoteType))
            )
        
        # Attachments
        if random.random() > 0.3:
            attach_repo.create(
                strategy_id=strat.id,
                attachment_type=AttachmentType.url,
                title="Strategy Documentation",
                url="https://github.com/drkthng/alphaforge"
            )
        if random.random() > 0.5:
            attach_repo.create(
                strategy_id=strat.id,
                attachment_type=AttachmentType.image,
                title="Initial Concept Sketch",
                file_path="assets/placeholder.png"
            )
    
    session.commit()
    
    # Create versions and runs
    for strat in strategies:
        num_versions = random.randint(1, 3)
        for v_num in range(1, num_versions + 1):
            rts_path = archive_dir / f"{strat.slug}_v{v_num}.rts"
            rts_content = f"""// Strategy: {strat.name}
// Version: {v_num}
// Generated: {datetime.now()}

Procedure BackTest
    Set Capital = 100000
    Set DataSource = "SP500"
    Set StartDate = 2010-01-01
    Set EndDate = 2023-12-31
    
    // Mean Reversion Logic
    If Price < LowerBand Then Buy(100)
    If Price > UpperBand Then Sell(100)
End Procedure
"""
            rts_path.write_text(rts_content)
            
            v = v_repo.create(
                strategy_id=strat.id,
                version_number=v_num,
                description=f"Version {v_num} of {strat.name}",
                rts_file_path=str(rts_path)
            )
            session.commit()
            
            # Create runs for this version
            num_runs = random.randint(5, 15) # Reduced from 20-50 for faster seeding and fewer files
            for run_idx in range(num_runs):
                u = random.choice(universes)
                run_date = datetime.now() - timedelta(days=random.randint(0, 365))
                start_date = date(2010, 1, 1)
                end_date = date(2023, 12, 31)
                
                run = b_repo.create(
                    version_id=v.id,
                    universe_id=u.id,
                    run_date=run_date,
                    date_range_start=start_date,
                    date_range_end=end_date,
                    parameter_hash=f"hash_{random.getrandbits(64)}",
                    parameters_json={"lookback": random.randint(10, 100), "threshold": random.random()},
                    is_in_sample=random.choice([True, False, None])
                )
                
                # Metrics
                cagr = random.uniform(-5, 45)
                max_dd = random.uniform(-40, -5)
                sharpe = random.uniform(0.2, 3.5)
                profit_factor = random.uniform(0.8, 2.5)
                win_rate = random.uniform(0.3, 0.7)
                
                m_repo.create(
                    run_id=run.id,
                    cagr=cagr,
                    max_drawdown=max_dd,
                    sharpe=sharpe,
                    profit_factor=profit_factor,
                    pct_wins=win_rate,
                    total_trades=random.randint(50, 1000),
                    expectancy=random.uniform(0, 0.5),
                    net_profit=random.uniform(10000, 1000000),
                    rate_of_return=cagr * 2.5,
                    mar=cagr / abs(max_dd) if max_dd != 0 else 0,
                    avg_exposure=random.uniform(0.1, 0.9),
                    custom_metrics_json={"alpha_v1": random.random(), "beta_v1": random.random()}
                )
                
                # Equity Curve and Trade Log (only for first 3 runs per version)
                if run_idx < 3:
                    # Equity Curve
                    eq_path = equity_dir / f"run_{run.id}_equity.parquet"
                    dates = pd.bdate_range(start=start_date, end=end_date)
                    n_days = len(dates)
                    
                    # Random walk for equity
                    returns = np.random.normal(0.0003 + (cagr/25200), 0.012, n_days)
                    equity = 100000 * np.exp(np.cumsum(returns))
                    
                    # Compute drawdown
                    cum_max = np.maximum.accumulate(equity)
                    drawdown = (equity / cum_max - 1) * 100
                    
                    df_eq = pd.DataFrame({
                        "Date": dates,
                        "Equity": equity,
                        "Drawdown": drawdown
                    })
                    df_eq.to_parquet(eq_path)
                    run.equity_curve_path = str(eq_path)
                    
                    # Trade Log
                    trade_path = trade_dir / f"run_{run.id}_trades.parquet"
                    n_trades = random.randint(30, 100)
                    
                    trade_dates = sorted([random.choice(dates) for _ in range(n_trades)])
                    symbols = ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOG", "META", "NVDA"]
                    
                    trades = []
                    for t_date in trade_dates:
                        exit_date = t_date + timedelta(days=random.randint(1, 30))
                        entry_price = random.uniform(50, 500)
                        pnl_pct = random.uniform(-0.1, 0.15)
                        exit_price = entry_price * (1 + pnl_pct)
                        
                        trades.append({
                            "EntryDate": t_date,
                            "ExitDate": exit_date,
                            "Symbol": random.choice(symbols),
                            "Direction": random.choice(["Long", "Short"]),
                            "EntryPrice": entry_price,
                            "ExitPrice": exit_price,
                            "PnL": (exit_price - entry_price) * 100,
                            "HoldingDays": (exit_date - t_date).days
                        })
                    
                    df_trades = pd.DataFrame(trades)
                    df_trades.to_parquet(trade_path)
                    run.trade_log_path = str(trade_path)
                    
                    # HTML Report Artifact (only for the first run)
                    if run_idx == 0:
                        rep_path = report_dir / f"run_{run.id}_report.html"
                        html_content = f"""
                        <html>
                        <head><style>body {{ font-family: sans-serif; padding: 20px; }} table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }} tr:nth-child(even) {{ background-color: #f2f2f2; }}</style></head>
                        <body>
                            <h1>Strategy Report: {strat.name}</h1>
                            <p><strong>Run ID:</strong> {run.id}</p>
                            <p><strong>CAGR:</strong> {cagr:.2f}%</p>
                            <p><strong>Sharpe:</strong> {sharpe:.2f}</p>
                            <hr>
                            <h2>Key Statistics</h2>
                            <table>
                                <tr><th>Metric</th><th>Value</th></tr>
                                <tr><td>Net Profit</td><td>${cagr*10000:,.0f}</td></tr>
                                <tr><td>Max Drawdown</td><td>{max_dd:.2f}%</td></tr>
                                <tr><td>Total Trades</td><td>{n_trades}</td></tr>
                            </table>
                        </body>
                        </html>
                        """
                        rep_path.write_text(html_content)
                        artifact_repo.create(
                            run_id=run.id,
                            artifact_type=ArtifactType.html_report,
                            file_path=str(rep_path),
                            description="Main Backtest Report"
                        )
    
    session.commit()
    print(f"Seed complete. Created {len(strategies)} strategies, versions, and runs with synthetic data.")

if __name__ == "__main__":
    seed()
