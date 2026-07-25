import pandas as pd
import pytest
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


def test_invalid_timestamp_evidence_fails_closed():
    index = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-03"])
    context = resolve_annualization(index, "1d")
    assert context.annualization_status == "unavailable"
