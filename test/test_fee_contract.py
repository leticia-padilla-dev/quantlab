import numpy as np
import pandas as pd
import pytest

from quantlab.backtest.engine import run_backtest
from quantlab.execution.paper import run_paper_broker
from quantlab.execution.forward_eval import CandidateConfig, run_forward_evaluation


def _round_trip_fixture() -> tuple[pd.DataFrame, pd.Series]:
    index = pd.date_range("2025-01-01", periods=4, freq="D")
    frame = pd.DataFrame({"close": [100.0] * 4, "atr": [1.0] * 4}, index=index)
    signals = pd.Series([1, 0, 0, -1], index=index)
    return frame, signals


def test_constant_price_round_trip_uses_monetary_fee_and_single_slippage_application():
    frame, signals = _round_trip_fixture()
    capital = 10_000.0
    fee_rate = 0.01
    slippage_bps = 100.0
    expected = capital * (1 - fee_rate) ** 2 * (1 - 0.01) / (1 + 0.01)

    paper = run_paper_broker(
        frame, signals, initial_cash=capital, fee_rate=fee_rate, slippage_bps=slippage_bps
    )
    backtest = run_backtest(
        frame, signals, fee_rate=fee_rate, slippage_bps=slippage_bps, backend="python"
    )

    assert paper.iloc[-1]["equity_after"] == pytest.approx(expected)
    assert backtest.iloc[-1]["equity"] * capital == pytest.approx(expected)


def test_invalid_cost_parameters_fail_closed():
    frame, signals = _round_trip_fixture()
    with pytest.raises(ValueError):
        run_backtest(frame, signals, fee_rate=-0.1)
    with pytest.raises(ValueError):
        run_paper_broker(frame, signals, slippage_mode="unknown")


def test_python_and_numba_cost_accounting_match():
    pytest.importorskip("numba")
    frame, signals = _round_trip_fixture()
    python = run_backtest(frame, signals, fee_rate=0.01, slippage_bps=100, backend="python")
    numba = run_backtest(frame, signals, fee_rate=0.01, slippage_bps=100, backend="numba")
    pd.testing.assert_series_equal(python["equity"], numba["equity"], check_dtype=False)
    pd.testing.assert_series_equal(python["fees"], numba["fees"], check_dtype=False)


def test_strategy_return_net_is_period_ratio_not_equity_difference():
    frame = pd.DataFrame({"close": [100.0, 110.0, 121.0], "atr": [1.0, 1.0, 1.0]})
    signals = pd.Series([1, 0, 0])
    result = run_backtest(frame, signals, fee_rate=0.0, slippage_bps=0.0)
    assert result["strategy_ret_net"].iloc[2] == pytest.approx(0.1)


def test_multiple_fills_charge_one_fee_per_transition():
    index = pd.date_range("2025-01-01", periods=6, freq="D")
    frame = pd.DataFrame({"close": [100.0] * 6, "atr": [1.0] * 6}, index=index)
    signals = pd.Series([1, 0, -1, 1, 0, -1], index=index)
    trades = run_paper_broker(frame, signals, initial_cash=1_000.0, fee_rate=0.01, slippage_bps=0)
    assert len(trades) == 4
    assert trades["fee"].sum() > 0
    assert trades["fee"].sum() == pytest.approx(
        trades.iloc[0]["fee"] + trades.iloc[1]["fee"] + trades.iloc[2]["fee"] + trades.iloc[3]["fee"]
    )
