"""Shared, timestamp-aware annualization policy."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


_ALIASES = {"1wk": "1w"}
_INTERVALS = {"1d": 365.0, "1w": 52.0, "1h": 8760.0, "1m": 525600.0}
_MIN_DAILY_CLASSIFICATION_SPAN_DAYS = 7
_MAX_MISSING_BUSINESS_DAY_RATIO = 0.05


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

    expected = {"1d": 86400.0, "1w": 604800.0, "1h": 3600.0, "1m": 60.0}[interval]
    if interval == "1d":
        local_dates = ts.tz_localize(None).normalize()
        calendar_deltas = local_dates.to_series().diff().dropna().dt.days
        span_days = int((local_dates[-1] - local_dates[0]).days)
        if span_days < _MIN_DAILY_CLASSIFICATION_SPAN_DAYS:
            return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "insufficient_span")
        if (calendar_deltas < 1).any() or (calendar_deltas > 4).any():
            return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "interval_timestamp_mismatch")

        if (calendar_deltas == 1).all():
            periods = 365.0
        else:
            observed_dates = pd.DatetimeIndex(local_dates)
            if (observed_dates.dayofweek >= 5).any():
                return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "interval_timestamp_mismatch")
            expected_business_days = len(pd.bdate_range(local_dates[0], local_dates[-1]))
            missing_business_days = expected_business_days - len(observed_dates)
            missing_ratio = max(0, missing_business_days) / expected_business_days
            if missing_ratio > _MAX_MISSING_BUSINESS_DAY_RATIO:
                return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "interval_timestamp_mismatch")
            periods = 252.0
    else:
        deltas = ts.to_series().diff().dropna().dt.total_seconds()
        median = float(deltas.median())
        irregular = (deltas.sub(median).abs() > max(1.0, median * 0.05)).any()
        if median <= 0 or irregular or abs(median - expected) > expected * 0.05:
            return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "interval_timestamp_mismatch")
        periods = _INTERVALS[interval]

    elapsed_years = (ts[-1] - ts[0]).total_seconds() / (365.25 * 86400.0)
    if elapsed_years <= 0 or (ts[-1] - ts[0]).total_seconds() < expected:
        return AnnualizationContext(interval, None, None, "unavailable", "unavailable", "insufficient_span")
    return AnnualizationContext(interval, elapsed_years, periods, "interval_and_timestamps", "valid")
