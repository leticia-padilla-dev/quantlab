import pytest
import pandas as pd
from quantlab.experiments import runner
from quantlab.experiments.runner import expand_grid


class _FakeStrategy:
    def __init__(self, *args, **kwargs):
        pass

    def generate_signals(self, df):
        return pd.Series(0, index=df.index, dtype="int64")

def test_expand_grid_creates_correct_count():
    """
    Test that expand_grid creates the expected number of combinations.
    """
    config = {
        "ticker": "ETH-USD",
        "param_grid": {
            "rsi_buy_max": [55, 60],
            "rsi_sell_min": [70, 75, 80],
            "cooldown_days": [0, 5]
        }
    }
    # 2 * 3 * 2 = 12
    runs = expand_grid(config)
    assert len(runs) == 12
    
    # Check one run
    run = runs[0]
    assert "param_grid" not in run
    assert run["ticker"] == "ETH-USD"
    assert "rsi_buy_max" in run
    assert "rsi_sell_min" in run
    assert "cooldown_days" in run

def test_expand_grid_no_grid():
    config = {"ticker": "ETH-USD", "rsi_buy_max": 60}
    runs = expand_grid(config)
    assert len(runs) == 1
    assert runs[0]["rsi_buy_max"] == 60

def test_expand_grid_preserves_other_keys():
    config = {
        "ticker": "ETH-USD",
        "fee": 0.002,
        "param_grid": {
            "rsi_buy_max": [55, 60]
        }
    }
    runs = expand_grid(config)
    assert len(runs) == 2
    for r in runs:
        assert r["ticker"] == "ETH-USD"
        assert r["fee"] == 0.002


def test_run_one_paths_propagate_interval_to_shared_metrics(monkeypatch):
    index = pd.date_range("2023-01-01", periods=12, freq="W")
    prices = pd.DataFrame({"close": range(100, 112)}, index=index)
    backtest = pd.DataFrame(
        {
            "equity": pd.Series(range(100, 112), index=index) / 100,
            "position": 1,
            "trade": 0,
            "strategy_ret_net": 0.01,
        },
        index=index,
    )
    seen_intervals: list[str | None] = []

    monkeypatch.setattr(runner, "fetch_ohlc_cached", lambda *args, **kwargs: prices)
    monkeypatch.setattr(runner, "add_indicators", lambda df: df)
    monkeypatch.setattr(runner, "RsiMaAtrStrategy", _FakeStrategy)
    monkeypatch.setattr(runner, "run_backtest", lambda **kwargs: backtest)
    monkeypatch.setattr(
        runner,
        "run_paper_broker",
        lambda **kwargs: pd.DataFrame(),
    )

    def capture_metrics(bt, interval=None):
        seen_intervals.append(interval)
        return {
            "total_return": 0.1,
            "max_drawdown": 0.0,
            "sharpe_simple": 1.0,
            "trades": 0,
        }

    monkeypatch.setattr(runner, "compute_metrics", capture_metrics)
    config = {
        "ticker": "ETH-USD",
        "start": "2023-01-01",
        "end": "2023-03-31",
        "interval": "1wk",
    }

    runner.run_one(config)
    runner.run_one_with_timeseries(config)

    assert seen_intervals == ["1wk", "1wk"]
