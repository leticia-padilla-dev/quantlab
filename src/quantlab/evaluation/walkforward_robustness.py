"""Walk-forward robustness verdict artifacts.

This module evaluates existing walk-forward run artifacts. It does not
authorize paper trading, broker execution, live execution, or promotion.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


ARTIFACT_TYPE = "quantlab.walkforward_robustness_verdict"
SCHEMA_VERSION = "1.0"
VERDICT_JSON = "robustness_verdict.json"
VERDICT_MD = "robustness_verdict.md"
SUMMARY_CSV = "walkforward_summary.csv"
OOS_LEADERBOARD_CSV = "oos_leaderboard.csv"
REQUIRED_SUMMARY_COLUMNS = {
    "split_name",
    "avg_test_return_topk",
    "avg_test_sharpe_topk",
}


class WalkforwardRobustnessError(ValueError):
    """Raised when a run directory cannot be evaluated."""


def evaluate_walkforward_robustness(run_dir: str | Path) -> dict[str, Any]:
    """Evaluate a walk-forward run directory and return a verdict payload."""

    run_path = Path(run_dir)
    summary_path = run_path / SUMMARY_CSV
    if not summary_path.exists():
        raise WalkforwardRobustnessError(
            f"Required artifact missing: {summary_path}"
        )

    summary = pd.read_csv(summary_path)
    missing_columns = sorted(REQUIRED_SUMMARY_COLUMNS - set(summary.columns))
    if missing_columns:
        raise WalkforwardRobustnessError(
            "walkforward_summary.csv missing required columns: "
            + ", ".join(missing_columns)
        )
    if summary.empty:
        raise WalkforwardRobustnessError("walkforward_summary.csv is empty.")

    returns = pd.to_numeric(summary["avg_test_return_topk"], errors="coerce")
    sharpes = pd.to_numeric(summary["avg_test_sharpe_topk"], errors="coerce")
    valid_returns = returns.dropna()
    valid_sharpes = sharpes.dropna()
    if valid_returns.empty:
        raise WalkforwardRobustnessError(
            "walkforward_summary.csv has no numeric avg_test_return_topk values."
        )

    total_splits = int(len(summary))
    positive_oos_splits = int((valid_returns > 0).sum())
    positive_oos_ratio = positive_oos_splits / total_splits if total_splits else 0.0
    avg_oos_return_topk = _safe_float(valid_returns.mean())
    avg_oos_sharpe_topk = _safe_float(valid_sharpes.mean()) if not valid_sharpes.empty else None
    worst_oos_split_return = _safe_float(valid_returns.min())
    best_oos_split_return = _safe_float(valid_returns.max())

    oos_path = run_path / OOS_LEADERBOARD_CSV
    total_oos_trades, trade_count_source = _read_total_oos_trades(oos_path)

    source_artifacts = [SUMMARY_CSV]
    if oos_path.exists():
        source_artifacts.append(OOS_LEADERBOARD_CSV)

    reasons: list[str] = []
    diagnostics: list[str] = []
    hard_fail = False

    if positive_oos_ratio < 0.66:
        hard_fail = True
        reasons.append(
            f"Only {positive_oos_splits} of {total_splits} OOS splits had positive average test return."
        )
    if worst_oos_split_return is not None and worst_oos_split_return < -0.25:
        hard_fail = True
        reasons.append(
            f"Worst OOS split return was {_format_percent(worst_oos_split_return)}, below the -25.00% hard-fail threshold."
        )

    if (
        positive_oos_splits == 1
        and total_splits > 1
        and best_oos_split_return is not None
        and best_oos_split_return > 0
    ):
        diagnostics.append(
            "Positive evidence is concentrated in a single OOS split."
        )

    review_reasons = _collect_review_reasons(
        total_splits=total_splits,
        avg_oos_return_topk=avg_oos_return_topk,
        avg_oos_sharpe_topk=avg_oos_sharpe_topk,
        total_oos_trades=total_oos_trades,
        trade_count_source=trade_count_source,
    )

    if hard_fail:
        status = "fail"
        grade = "not_robust"
        reasons.extend(diagnostics)
        reasons.extend(review_reasons)
        recommendation = (
            "Do not mark as baseline or promote to paper trading. "
            "Treat as regime-specific or insufficiently robust evidence."
        )
    elif review_reasons or diagnostics:
        status = "review"
        grade = "needs_operator_review"
        reasons.extend(diagnostics)
        reasons.extend(review_reasons)
        recommendation = (
            "Do not promote automatically. Review the walk-forward evidence "
            "and collect stronger OOS evidence before promotion."
        )
    else:
        status = "pass"
        grade = "research_robustness_passed"
        reasons.append(
            f"{positive_oos_splits} of {total_splits} OOS splits had positive average test return."
        )
        recommendation = (
            "Research robustness gate passed. This does not authorize paper, "
            "broker, live, or capital deployment."
        )

    return {
        "artifact_type": ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "grade": grade,
        "total_splits": total_splits,
        "positive_oos_splits": positive_oos_splits,
        "positive_oos_ratio": _safe_float(positive_oos_ratio),
        "avg_oos_return_topk": avg_oos_return_topk,
        "avg_oos_sharpe_topk": avg_oos_sharpe_topk,
        "worst_oos_split_return": worst_oos_split_return,
        "best_oos_split_return": best_oos_split_return,
        "total_oos_trades": total_oos_trades,
        "trade_count_source": trade_count_source,
        "source_artifacts": source_artifacts,
        "reasons": reasons,
        "recommendation": recommendation,
    }


def write_walkforward_robustness_verdict(run_dir: str | Path) -> dict[str, Any]:
    """Evaluate a run directory and write JSON and Markdown verdict artifacts."""

    run_path = Path(run_dir)
    verdict = evaluate_walkforward_robustness(run_path)
    (run_path / VERDICT_JSON).write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_path / VERDICT_MD).write_text(
        render_walkforward_robustness_markdown(verdict),
        encoding="utf-8",
    )
    return verdict


def render_walkforward_robustness_markdown(verdict: dict[str, Any]) -> str:
    """Render a human-readable robustness verdict."""

    status = str(verdict.get("status", "review")).upper()
    grade = str(verdict.get("grade", "unknown"))
    reasons = verdict.get("reasons") or []
    reason_lines = "\n".join(f"- {reason}" for reason in reasons) or "- None recorded."
    source_lines = "\n".join(
        f"- {artifact}" for artifact in verdict.get("source_artifacts", [])
    ) or "- None recorded."

    return (
        "# Walk-forward Robustness Verdict\n\n"
        f"**Status:** {status}\n\n"
        f"**Grade:** `{grade}`\n\n"
        "## Key Metrics\n\n"
        f"- Positive OOS splits: {verdict.get('positive_oos_splits')} / {verdict.get('total_splits')}\n"
        f"- Positive OOS ratio: {_format_percent(verdict.get('positive_oos_ratio'))}\n"
        f"- Average OOS return top-k: {_format_percent(verdict.get('avg_oos_return_topk'))}\n"
        f"- Average OOS Sharpe top-k: {_format_number(verdict.get('avg_oos_sharpe_topk'))}\n"
        f"- Worst OOS split return: {_format_percent(verdict.get('worst_oos_split_return'))}\n"
        f"- Best OOS split return: {_format_percent(verdict.get('best_oos_split_return'))}\n"
        f"- Total OOS trades: {verdict.get('total_oos_trades') if verdict.get('total_oos_trades') is not None else 'unavailable'}\n\n"
        "## Reasons\n\n"
        f"{reason_lines}\n\n"
        "## Recommendation\n\n"
        f"{verdict.get('recommendation', '')}\n\n"
        "## Source Artifacts\n\n"
        f"{source_lines}\n\n"
        "## Boundary\n\n"
        "A `pass` verdict only means the research robustness gate passed. "
        "It does not authorize paper trading, broker execution, live execution, "
        "automation, or capital deployment.\n"
    )


def _collect_review_reasons(
    *,
    total_splits: int,
    avg_oos_return_topk: float | None,
    avg_oos_sharpe_topk: float | None,
    total_oos_trades: int | None,
    trade_count_source: str | None,
) -> list[str]:
    reasons: list[str] = []
    if total_splits < 3:
        reasons.append(
            f"Only {total_splits} OOS split(s) are available; at least 3 are preferred."
        )
    if avg_oos_return_topk is None or avg_oos_return_topk <= 0:
        reasons.append("Average OOS top-k return is not positive.")
    if avg_oos_sharpe_topk is None or avg_oos_sharpe_topk <= 0:
        reasons.append("Average OOS top-k Sharpe is not positive.")
    if total_oos_trades is None:
        reasons.append("OOS trade count unavailable.")
    elif total_oos_trades < 10:
        reasons.append(
            f"Only {total_oos_trades} OOS trades found from {trade_count_source}; at least 10 are preferred."
        )
    return reasons


def _read_total_oos_trades(oos_path: Path) -> tuple[int | None, str | None]:
    if not oos_path.exists():
        return None, None
    try:
        oos = pd.read_csv(oos_path)
    except Exception:
        return None, None
    for column in ("trade_trades", "trades"):
        if column in oos.columns:
            values = pd.to_numeric(oos[column], errors="coerce").dropna()
            if not values.empty:
                return int(values.sum()), column
    return None, None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _format_percent(value: Any) -> str:
    number = _safe_float(value)
    return "unavailable" if number is None else f"{number:.2%}"


def _format_number(value: Any) -> str:
    number = _safe_float(value)
    return "unavailable" if number is None else f"{number:.4f}"

