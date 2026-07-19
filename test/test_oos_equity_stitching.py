"""Regression tests for continuous out-of-sample equity stitching."""

from pathlib import Path

import pandas as pd
import pytest

from quantlab.experiments.runner import (
    _persist_walkforward_rich_artifacts,
    _stitch_oos_timeseries,
)


def _frame(split_name: str, start: str, returns: list[float]) -> pd.DataFrame:
    period_return = pd.Series(returns, dtype="float64")
    local_equity = (1.0 + period_return).cumprod()
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(start, periods=len(returns), freq="D"),
            "split_name": split_name,
            "equity": local_equity,
            "period_return": period_return,
            "cumulative_return": local_equity - 1.0,
            "close": [100.0 + index for index in range(len(returns))],
            "signal": [0] * len(returns),
            "position": [0] * len(returns),
        }
    )


def test_stitch_oos_timeseries_compounds_across_split_boundaries() -> None:
    first = _frame("split_00", "2024-01-01", [0.10, -0.05])
    second = _frame("split_01", "2024-01-03", [0.20, 0.00])

    stitched = _stitch_oos_timeseries([first, second])

    assert stitched["equity"].tolist() == pytest.approx([1.10, 1.045, 1.254, 1.254])
    assert stitched["cumulative_return"].tolist() == pytest.approx(
        [0.10, 0.045, 0.254, 0.254]
    )
    assert stitched.loc[2, "equity"] != pytest.approx(second.loc[0, "equity"])


def test_stitch_oos_timeseries_orders_frames_chronologically() -> None:
    earlier = _frame("split_00", "2024-01-01", [0.01, 0.02])
    later = _frame("split_01", "2024-01-03", [-0.01, 0.03])

    stitched = _stitch_oos_timeseries([later, earlier])

    assert stitched["timestamp"].is_monotonic_increasing
    assert stitched["split_name"].tolist() == [
        "split_00",
        "split_00",
        "split_01",
        "split_01",
    ]


def test_stitch_oos_timeseries_rejects_overlapping_timestamps() -> None:
    first = _frame("split_00", "2024-01-01", [0.01, 0.02])
    overlapping = _frame("split_01", "2024-01-02", [0.03, 0.04])

    with pytest.raises(ValueError, match="duplicate timestamps"):
        _stitch_oos_timeseries([first, overlapping])


def test_stitch_oos_timeseries_rejects_non_finite_returns() -> None:
    frame = _frame("split_00", "2024-01-01", [0.01, 0.02])
    frame.loc[1, "period_return"] = float("nan")

    with pytest.raises(ValueError, match="finite"):
        _stitch_oos_timeseries([frame])


def test_persist_walkforward_writes_continuously_stitched_equity(tmp_path: Path) -> None:
    first = _frame("split_00", "2024-01-01", [0.10, -0.05])
    second = _frame("split_01", "2024-01-03", [0.20, 0.00])

    _persist_walkforward_rich_artifacts(
        tmp_path,
        pd.DataFrame(),
        [],
        oos_timeseries_frames=[first, second],
    )

    persisted = pd.read_csv(tmp_path / "oos_equity_timeseries.csv")
    assert persisted["equity"].tolist() == pytest.approx([1.10, 1.045, 1.254, 1.254])
    assert persisted["cumulative_return"].tolist() == pytest.approx(
        [0.10, 0.045, 0.254, 0.254]
    )


def test_persist_walkforward_rejects_overlapping_oos_windows(tmp_path: Path) -> None:
    first = _frame("split_00", "2024-01-01", [0.01, 0.02])
    overlapping = _frame("split_01", "2024-01-02", [0.03, 0.04])

    with pytest.raises(ValueError, match="duplicate timestamps"):
        _persist_walkforward_rich_artifacts(
            tmp_path,
            pd.DataFrame(),
            [],
            oos_timeseries_frames=[first, overlapping],
        )

    assert not (tmp_path / "oos_equity_timeseries.csv").exists()
