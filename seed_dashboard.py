import random
from datetime import datetime, timedelta, date
from alphaforge.config import load_config
from alphaforge.database import get_engine, SessionLocal
from alphaforge.models import Base, Strategy, StrategyVersion, BacktestRun, RunMetrics, Universe, StrategyStatus
from alphaforge.repository import StrategyRepository, VersionRepository, BacktestRepository, MetricsRepository, UniverseRepository

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
    
    # Create versions and runs
    for strat in strategies:
        num_versions = random.randint(1, 3)
        for v_num in range(1, num_versions + 1):
            v = v_repo.create(
                strategy_id=strat.id,
                version_number=v_num,
                description=f"Version {v_num} of {strat.name}"
            )
            session.commit()
            
            # Create runs for this version
            num_runs = random.randint(20, 50)
            for _ in range(num_runs):
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
    
    session.commit()
    print(f"Seed complete. Created {len(strategies)} strategies and total runs.")

if __name__ == "__main__":
    seed()
