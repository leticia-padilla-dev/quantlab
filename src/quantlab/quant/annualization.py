"""Shared, timestamp-aware annualization policy."""
from __future__ import annotations

from dataclasses import dataclass
import math
import pandas as pd


_ALIASES = {"1wk": "1w"}
_INTERVALS = {"1d": 365.0, "1w": 52.0, "1h": 8760.0, "1m": 525600.0}


@dataclass(frozen=True)
class AnnualizationContext:
    interval: str | None
    elapsed_years: float | None
    periods_per_year: float | None
    annualization_source: str
    annualization_status: str
    reason: str | None = None


def resolve_annualization(index, interval: str | None = None) -> AnnualizationContext:
    interval = _ALIASES.get(interval, interval)
    if interval not in _INTERVALS:
        return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "unsupported_interval")
    try:
        ts = pd.DatetimeIndex(index)
    except (TypeError, ValueError):
        return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "timestamps_required")
    if len(ts) < 3 or not ts.is_monotonic_increasing or ts.has_duplicates:
        return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "invalid_timestamps")
    deltas = ts.to_series().diff().dropna().dt.total_seconds()
    median = float(deltas.median())
    expected = {"1d": 86400.0, "1w": 604800.0, "1h": 3600.0, "1m": 60.0}[interval]
    irregular = (deltas.sub(median).abs() > max(1.0, median * 0.05)).any()
    if interval == "1d":
        irregular = bool((deltas < 86400.0).any() or (deltas > 86400.0 * 4.0).any())
    if median <= 0 or irregular or abs(median - expected) > expected * 0.05:
        return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "interval_timestamp_mismatch")
    elapsed_years = (ts[-1] - ts[0]).total_seconds() / (365.25 * 86400.0)
    if elapsed_years <= 0 or (ts[-1] - ts[0]).total_seconds() < expected:
        return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "insufficient_span")
    periods = _INTERVALS[interval]
    if interval == "1d":
        periods = 365.0 if (deltas > 86400.0 * 1.5).mean() < 0.1 else 252.0
    return AnnualizationContext(interval, elapsed_years, periods, "interval_and_timestamps", "valid")
