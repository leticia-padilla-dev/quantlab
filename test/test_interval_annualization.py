import pandas as pd
import pytest
from quantlab.reporting.charts import plot_rolling_performance
from quantlab.quant.annualization import resolve_annualization


def test_calendar_daily_uses_365_not_252():
    index = pd.date_range("2024-01-01", periods=366, freq="D")
    context = resolve_annualization(index, "1d")
    assert context.periods_per_year == 365.0


def test_weekly_uses_52_and_elapsed_calendar_years():
    index = pd.date_range("2020-01-05", periods=53, freq="W")
    context = resolve_annualization(index, "1w")
    assert context.periods_per_year == 52.0
    assert context.elapsed_years == pytest.approx(1.0, rel=0.03)


def test_yfinance_weekly_alias_and_hourly_factor():
    weekly = resolve_annualization(pd.date_range("2020-01-05", periods=53, freq="W"), "1wk")
    hourly = resolve_annualization(pd.date_range("2024-01-01", periods=8761, freq="h"), "1h")
    assert weekly.periods_per_year == 52.0
    assert hourly.periods_per_year == 8760.0


def test_business_daily_resolves_to_252():
    context = resolve_annualization(pd.bdate_range("2024-01-01", periods=260), "1d")
    assert context.periods_per_year == 252.0


def test_invalid_timestamp_evidence_fails_closed():
    index = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-03"])
    context = resolve_annualization(index, "1d")
    assert context.annualization_status == "unavailable"


def test_insufficient_sample_or_span_fails_closed():
    short = resolve_annualization(pd.date_range("2024-01-01", periods=2, freq="D"), "1d")
    assert short.annualization_status == "unavailable"


def test_rolling_sharpe_without_interval_fails_closed(tmp_path):
    equity = pd.Series(
        range(1, 100), index=pd.date_range("2024-01-01", periods=99, freq="D"), dtype=float
    )
    assert plot_rolling_performance(equity, str(tmp_path / "rolling.png"), window=30) is None
