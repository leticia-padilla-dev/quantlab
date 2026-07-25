from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantlab.backtest.metrics import compute_metrics
from quantlab.quant.annualization import resolve_annualization
from quantlab.reporting import charts
from quantlab.reporting.advanced_metrics import (
    build_advanced_metrics,
    compute_drawdown_metrics,
    compute_equity_metrics,
)
from quantlab.reporting.forward_report import (
    _compute_summary_metrics,
    build_forward_report,
)


def _weekly_equity(n_periods: int = 90) -> pd.Series:
    period_returns = np.resize(
        np.array([0.012, -0.008, 0.006, -0.015, 0.02, -0.004], dtype=float),
        n_periods - 1,
    )
    values = np.concatenate(([1.0], np.cumprod(1.0 + period_returns)))
    return pd.Series(
        values,
        index=pd.date_range("2023-01-01", periods=n_periods, freq="W"),
        name="equity",
    )


def _backtest_from_equity(equity: pd.Series) -> pd.DataFrame:
    trades = np.zeros(len(equity), dtype=int)
    trades[[1, 12, 25, 50]] = [1, -1, 1, -1]
    return pd.DataFrame(
        {
            "equity": equity,
            "position": np.ones(len(equity), dtype=int),
            "trade": trades,
            "strategy_ret_net": equity.pct_change(),
        },
        index=equity.index,
    )


def _materially_irregular_daily_index() -> pd.DatetimeIndex:
    timestamps = [pd.Timestamp("2024-01-01")]
    for gap_days in [1] * 80 + [4] * 20:
        timestamps.append(timestamps[-1] + pd.Timedelta(days=gap_days))
    return pd.DatetimeIndex(timestamps)


def _write_forward_inputs(run_dir: Path, equity: pd.Series, interval: str) -> None:
    run_dir.mkdir()
    (run_dir / "portfolio_state.json").write_text(
        json.dumps(
            {
                "session_id": "acceptance-forward",
                "cash": 1_000.0,
                "current_equity": 1_000.0 * float(equity.iloc[-1]),
                "candidate": {"interval": interval},
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        {"timestamp": equity.index, "equity": equity.to_numpy()}
    ).to_csv(run_dir / "forward_equity_curve.csv", index=False)
    pd.DataFrame(columns=["side", "equity_after", "fee"]).to_csv(
        run_dir / "forward_trades.csv", index=False
    )


def test_cross_consumer_annualization_context_and_metrics_are_equivalent():
    equity = _weekly_equity()
    bt = _backtest_from_equity(equity)

    backtest = compute_metrics(bt, interval="1wk")
    advanced = compute_equity_metrics(equity, interval="1wk")
    drawdown = compute_drawdown_metrics(equity, interval="1wk")
    forward = _compute_summary_metrics(
        equity,
        pd.DataFrame(columns=["side", "equity_after", "fee"]),
        initial_cash=1_000.0,
        interval="1wk",
    )

    for consumer in (backtest, advanced, drawdown, forward):
        assert consumer["interval"] == "1wk"
        assert consumer["periods_per_year"] == 52.0
        assert consumer["annualization_status"] == "valid"

    # Volatility has the same return-series semantics in advanced and forward.
    assert forward["annualized_volatility"] == pytest.approx(
        advanced["annualized_volatility"], rel=1e-12
    )
    # Sharpe has the same return-series semantics in backtest and advanced.
    assert backtest["sharpe_simple"] == pytest.approx(
        advanced["sharpe"], rel=1e-8
    )
    # Calmar is advanced CAGR divided by the matching absolute max drawdown.
    assert drawdown["calmar"] == pytest.approx(
        advanced["cagr"] / abs(drawdown["max_drawdown"]), rel=1e-12
    )


def test_non_annualized_metrics_are_stable_when_annualization_is_unavailable():
    equity = _weekly_equity()
    bt = _backtest_from_equity(equity)

    valid = compute_metrics(bt, interval="1wk")
    unavailable = compute_metrics(bt, interval=None)
    for field in (
        "total_return",
        "max_drawdown",
        "winrate_active_days",
        "trades",
        "days",
    ):
        assert unavailable[field] == valid[field]

    expected_total_return = float(equity.iloc[-1] - 1.0)
    expected_max_drawdown = float((equity / equity.cummax() - 1.0).min())
    assert valid["total_return"] == pytest.approx(expected_total_return)
    assert valid["max_drawdown"] == pytest.approx(expected_max_drawdown)
    assert valid["trades"] == 4
    assert valid["days"] == len(equity)
    assert unavailable["sharpe_simple"] is None


@pytest.mark.parametrize(
    ("index", "interval"),
    [
        (pd.date_range("2024-01-01", periods=10, freq="D"), "unknown"),
        (pd.date_range("2024-01-01", periods=10, freq="W"), "1d"),
        (
            pd.DatetimeIndex(["2024-01-01", "2024-01-01", "2024-01-02"]),
            "1d",
        ),
        (
            pd.DatetimeIndex(["2024-01-01", "2024-01-03", "2024-01-02"]),
            "1d",
        ),
        (_materially_irregular_daily_index(), "1d"),
        (pd.RangeIndex(10), "1d"),
        (pd.Index(["not-a-date", "still-not-a-date", "missing"]), "1d"),
        (pd.date_range("2024-01-01", periods=10, freq="D"), None),
        (pd.date_range("2024-01-01", periods=2, freq="D"), "1d"),
        (pd.date_range("2024-01-01", periods=3, freq="D"), "1d"),
    ],
    ids=[
        "unknown-interval",
        "interval-mismatch",
        "duplicate",
        "non-monotonic",
        "materially-irregular",
        "range-index",
        "missing-timestamps",
        "missing-interval",
        "insufficient-sample",
        "insufficient-span",
    ],
)
def test_invalid_evidence_matrix_fails_closed_without_losing_total_return(
    index: pd.Index, interval: str | None
):
    context = resolve_annualization(index, interval)
    assert context.annualization_status == "unavailable"
    assert context.periods_per_year is None
    assert context.reason

    equity = pd.Series(np.linspace(1.0, 1.1, len(index)), index=index)
    metrics = compute_equity_metrics(equity, interval=interval)
    assert metrics["total_return"] == pytest.approx(0.1)
    assert metrics["annualized_volatility"] is None
    assert metrics["sharpe"] is None
    assert metrics["cagr"] is None
    assert metrics["annualization_status"] == "unavailable"
    assert metrics["annualization_reason"]


def test_timezone_aware_calendar_daily_cadence_survives_dst():
    index = pd.date_range(
        "2024-02-15", "2024-04-15", freq="D", tz="Europe/Madrid"
    )
    context = resolve_annualization(index, "1d")
    assert context.annualization_status == "valid"
    assert context.periods_per_year == 365.0


def test_advanced_builder_propagates_config_resolved_interval(tmp_path):
    run_dir = tmp_path / "advanced"
    run_dir.mkdir()
    equity = _weekly_equity()
    (run_dir / "report.json").write_text(
        json.dumps(
            {
                "header": {"run_id": "advanced", "mode": "grid"},
                "config_resolved": {"interval": "1wk"},
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        {"timestamp": equity.index, "equity": equity.to_numpy()}
    ).to_csv(run_dir / "equity_curve.csv", index=False)

    payload = build_advanced_metrics(run_dir)

    assert payload["equity_metrics"]["interval"] == "1wk"
    assert payload["equity_metrics"]["periods_per_year"] == 52.0
    assert payload["drawdown_metrics"]["periods_per_year"] == 52.0


def test_forward_builder_propagates_interval_and_preserves_input_artifacts(
    tmp_path,
):
    run_dir = tmp_path / "forward"
    equity = _weekly_equity()
    _write_forward_inputs(run_dir, equity, "1wk")
    before = {
        path.name: path.read_bytes()
        for path in run_dir.iterdir()
        if path.is_file()
    }

    payload = build_forward_report(run_dir)

    assert payload["summary"]["interval"] == "1wk"
    assert payload["summary"]["periods_per_year"] == 52.0
    assert payload["summary"]["annualization_status"] == "valid"
    assert {item["file"] for item in payload["artifacts"]} == set(before)
    assert {
        path.name: path.read_bytes()
        for path in run_dir.iterdir()
        if path.is_file()
    } == before
    assert not any(
        "version" in path.name or "supersed" in path.name
        for path in run_dir.iterdir()
    )


@pytest.mark.parametrize(
    ("config_name", "content"),
    [
        ("config.json", '{"interval": "1wk"}'),
        ("config_resolved.yaml", "interval: 1wk\n"),
    ],
)
def test_generate_charts_propagates_interval_from_supported_artifacts(
    monkeypatch, tmp_path, config_name, content
):
    run_dir = tmp_path / config_name.replace(".", "_")
    run_dir.mkdir()
    (run_dir / config_name).write_text(content, encoding="utf-8")
    equity = _weekly_equity()
    seen: list[str | None] = []

    monkeypatch.setattr(
        "quantlab.reporting.advanced_metrics._load_equity_from_artifacts",
        lambda _run_path: equity,
    )
    monkeypatch.setattr(charts, "plot_equity_curve", lambda *_args: None)
    monkeypatch.setattr(charts, "plot_drawdown", lambda *_args: None)
    monkeypatch.setattr(charts, "plot_trade_distribution", lambda *_args: None)
    monkeypatch.setattr(charts, "plot_monthly_returns", lambda *_args: None)

    def capture_rolling(_equity, out_path, window, interval):
        seen.append(interval)
        return out_path

    monkeypatch.setattr(charts, "plot_rolling_performance", capture_rolling)

    generated = charts.generate_charts(run_dir, tmp_path / "charts")

    assert seen == ["1wk"]
    assert generated == [str(tmp_path / "charts" / "chart_rolling_sharpe.png")]


def test_weekly_rolling_sharpe_uses_shared_factor_and_period_labels(
    monkeypatch, tmp_path
):
    equity = _weekly_equity()
    captured: dict[str, object] = {}

    def capture_figure(fig, out_path):
        line = fig.axes[0].lines[0]
        captured["values"] = np.asarray(line.get_ydata())
        captured["label"] = line.get_label()
        captured["title"] = fig.axes[0].get_title()
        return out_path

    monkeypatch.setattr(charts, "_savefig", capture_figure)
    out_path = str(tmp_path / "weekly-rolling.png")

    result = charts.plot_rolling_performance(
        equity, out_path, window=20, interval="1wk"
    )

    context = resolve_annualization(equity.index, "1wk")
    returns = equity.pct_change().dropna()
    shared = (
        returns.rolling(20).mean()
        / (returns.rolling(20).std() + 1e-12)
        * np.sqrt(context.periods_per_year)
    ).dropna()
    hard_coded_daily = (
        returns.rolling(20).mean()
        / (returns.rolling(20).std() + 1e-12)
        * np.sqrt(252)
    ).dropna()

    assert result == out_path
    np.testing.assert_allclose(captured["values"], shared.to_numpy(), rtol=1e-12)
    assert not np.allclose(captured["values"], hard_coded_daily.to_numpy())
    assert "period" in str(captured["label"]).lower()
    assert "period" in str(captured["title"]).lower()
    assert "day" not in str(captured["label"]).lower()
    assert "day" not in str(captured["title"]).lower()
    assert charts.plot_rolling_performance(
        equity, str(tmp_path / "missing.png"), window=20, interval=None
    ) is None
