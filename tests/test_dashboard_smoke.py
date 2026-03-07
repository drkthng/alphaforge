import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphaforge.models import Base, Strategy, StrategyVersion, BacktestRun, RunMetric
from alphaforge.repository import (
    BacktestRepository, StrategyRepository, VersionRepository, 
    MetricsRepository
)
from alphaforge.analysis.heatmap import prepare_heatmap_data
from alphaforge.analysis.custom_metrics import (
    drawdowns_greater_than_10, ulcer_index, avg_monthly_return
)

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_dashboard_leaderboard_columns(session):
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    
    v_repo = VersionRepository(session)
    v = v_repo.create(strategy_id=strat.id, version_number=1)
    
    b_repo = BacktestRepository(session)
    run = b_repo.create(
        version_id=v.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="p1",
        parameters_json={"lookback": 20}
    )
    
    m_repo = MetricsRepository(session)
    m_repo.create(run_id=run.id, sharpe=1.5, cagr=20.0)
    
    session.commit()
    
    leaderboard = b_repo.get_leaderboard(filters={})
    assert len(leaderboard) == 1
    row = leaderboard[0]
    assert "strategy_name" in row
    assert row["strategy_name"] == "S1"
    assert row["sharpe"] == 1.5
    assert row["cagr"] == 20.0

def test_dashboard_heatmap_preparation():
    runs = [
        {"parameters_json": {"lookback": 10, "threshold": 0.5}, "sharpe": 1.0},
        {"parameters_json": {"lookback": 10, "threshold": 0.6}, "sharpe": 1.1},
        {"parameters_json": {"lookback": 20, "threshold": 0.5}, "sharpe": 1.2},
        {"parameters_json": {"lookback": 20, "threshold": 0.6}, "sharpe": 1.3},
    ]
    
    df = prepare_heatmap_data(runs, x_param="lookback", y_param="threshold", metric="sharpe")
    assert df.shape == (2, 2)
    assert df.loc[0.5, 10] == 1.0
    assert df.loc[0.6, 20] == 1.3

def test_dashboard_heatmap_empty():
    runs = []
    df = prepare_heatmap_data(runs, x_param="lookback", y_param="threshold", metric="sharpe")
    assert df.empty

def test_custom_metrics_nan_input():
    # Equity curve with NaN
    data = pd.DataFrame({
        "Equity": [100.0, np.nan, 90.0, 95.0, 80.0]
    })
    
    # Should not crash
    try:
        count = drawdowns_greater_than_10(data)
        assert isinstance(count, (int, float, np.integer, np.floating))
    except Exception as e:
        pytest.fail(f"drawdowns_greater_than_10 crashed on NaN input: {e}")

    try:
        ui = ulcer_index(data)
        assert isinstance(ui, (int, float, np.integer, np.floating))
    except Exception as e:
        pytest.fail(f"ulcer_index crashed on NaN input: {e}")

    try:
        amr = avg_monthly_return(data)
        assert isinstance(amr, (int, float, np.integer, np.floating))
    except Exception as e:
        pytest.fail(f"avg_monthly_return crashed on NaN input: {e}")
