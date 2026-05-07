"""CLI commands for research evaluation artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.errors import ConfigError
from quantlab.evaluation.walkforward_robustness import (
    VERDICT_JSON,
    VERDICT_MD,
    WalkforwardRobustnessError,
    write_walkforward_robustness_verdict,
)


def handle_evaluation_commands(args) -> dict[str, Any] | bool:
    run_dir_arg = getattr(args, "evaluate_walkforward_run", None)
    if not run_dir_arg:
        return False

    run_dir = Path(run_dir_arg)
    if not run_dir.exists() or not run_dir.is_dir():
        raise ConfigError(f"Walk-forward run directory does not exist: {run_dir}")

    try:
        verdict = write_walkforward_robustness_verdict(run_dir)
    except WalkforwardRobustnessError as exc:
        raise ConfigError(str(exc)) from exc

    json_path = run_dir / VERDICT_JSON
    md_path = run_dir / VERDICT_MD

    print(f"Walk-forward robustness verdict: {str(verdict['status']).upper()}")
    print(f"Grade: {verdict['grade']}")
    print(
        "Positive OOS splits: "
        f"{verdict['positive_oos_splits']}/{verdict['total_splits']}"
    )
    print(
        "Worst OOS split return: "
        f"{_format_percent(verdict.get('worst_oos_split_return'))}"
    )
    print(f"Recommendation: {verdict['recommendation']}")
    print(f"JSON artifact: {json_path}")
    print(f"Markdown artifact: {md_path}")

    return {
        "status": "success",
        "mode": "evaluation",
        "evaluation_type": "walkforward_robustness",
        "run_dir": str(run_dir),
        "verdict_status": verdict["status"],
        "verdict_grade": verdict["grade"],
        "robustness_verdict_json": str(json_path),
        "robustness_verdict_md": str(md_path),
    }


def _format_percent(value: Any) -> str:
    if value is None:
        return "unavailable"
    return f"{float(value):.2%}"

