from pathlib import Path

import json
import pandas as pd
import pytest

from quantlab.evaluation.walkforward_robustness import (
    WalkforwardRobustnessError,
    evaluate_walkforward_robustness,
    write_walkforward_robustness_verdict,
)
from quantlab.runs.quantitative_provenance import (
    attach_quantitative_provenance,
    propagate_quantitative_provenance_to_report,
)


SOURCE_COMMIT = "a" * 40


def _stamp_authoritative_walkforward(
    run_dir: Path, rows: list[dict]
) -> None:
    best_result = rows[0] if rows else None
    metadata, metrics = attach_quantitative_provenance(
        {
            "run_id": run_dir.name,
            "mode": "walkforward",
            "command": "sweep",
            "git_commit": SOURCE_COMMIT,
        },
        {
            "summary": {
                "total_return": (
                    best_result.get("avg_test_return_topk")
                    if best_result
                    else None
                ),
                "sharpe_simple": (
                    best_result.get("avg_test_sharpe_topk")
                    if best_result
                    else None
                ),
            },
            "best_result": best_result,
            "leaderboard_size": len(rows),
        },
        artifact_type="walkforward",
        relative_run_path=run_dir.name,
        source_git_commit=SOURCE_COMMIT,
        run_id=run_dir.name,
    )
    report = propagate_quantitative_provenance_to_report(
        {
            "header": {
                "run_id": run_dir.name,
                "mode": "walkforward",
                "git_commit": SOURCE_COMMIT,
            },
            "oos_leaderboard": [best_result] if best_result else [],
            "kpi_summary": metrics["summary"],
        },
        metadata,
        metrics,
    )
    for filename, payload in (
        ("metadata.json", metadata),
        ("metrics.json", metrics),
        ("report.json", report),
    ):
        (run_dir / filename).write_text(json.dumps(payload))


def _write_summary(run_dir: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(run_dir / "walkforward_summary.csv", index=False)
    _stamp_authoritative_walkforward(run_dir, rows)


def _write_oos(run_dir: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(run_dir / "oos_leaderboard.csv", index=False)


def test_walkforward_robustness_fails_on_weak_split_coverage_and_large_loss(tmp_path):
    _write_summary(
        tmp_path,
        [
            {
                "split_name": "2021_train__2022_test",
                "avg_test_return_topk": -0.4477,
                "avg_test_sharpe_topk": -0.8,
            },
            {
                "split_name": "2022_train__2023_test",
                "avg_test_return_topk": -0.0901,
                "avg_test_sharpe_topk": 0.2,
            },
            {
                "split_name": "H1_2023_train__H2_2023_test",
                "avg_test_return_topk": 0.1844,
                "avg_test_sharpe_topk": 1.55,
            },
        ],
    )
    _write_oos(tmp_path, [{"trade_trades": 4}, {"trade_trades": 3}, {"trade_trades": 5}])

    verdict = evaluate_walkforward_robustness(tmp_path)

    assert verdict["status"] == "fail"
    assert verdict["grade"] == "not_robust"
    assert verdict["total_splits"] == 3
    assert verdict["positive_oos_splits"] == 1
    assert verdict["positive_oos_ratio"] == pytest.approx(1 / 3)
    assert verdict["worst_oos_split_return"] == pytest.approx(-0.4477)
    assert any("Only 1 of 3" in reason for reason in verdict["reasons"])
    assert any("-25.00%" in reason for reason in verdict["reasons"])


def test_walkforward_robustness_reviews_low_sample_without_hard_fail(tmp_path):
    _write_summary(
        tmp_path,
        [
            {
                "split_name": "split_a",
                "avg_test_return_topk": 0.04,
                "avg_test_sharpe_topk": 0.6,
            },
            {
                "split_name": "split_b",
                "avg_test_return_topk": 0.02,
                "avg_test_sharpe_topk": 0.4,
            },
        ],
    )
    _write_oos(tmp_path, [{"trade_trades": 2}, {"trade_trades": 3}])

    verdict = evaluate_walkforward_robustness(tmp_path)

    assert verdict["status"] == "review"
    assert verdict["grade"] == "needs_operator_review"
    assert verdict["total_splits"] == 2
    assert verdict["total_oos_trades"] == 5
    assert any("Only 2 OOS split" in reason for reason in verdict["reasons"])
    assert any("Only 5 OOS trades" in reason for reason in verdict["reasons"])


def test_walkforward_robustness_passes_strong_oos_evidence(tmp_path):
    _write_summary(
        tmp_path,
        [
            {
                "split_name": "split_a",
                "avg_test_return_topk": 0.08,
                "avg_test_sharpe_topk": 0.9,
            },
            {
                "split_name": "split_b",
                "avg_test_return_topk": 0.03,
                "avg_test_sharpe_topk": 0.4,
            },
            {
                "split_name": "split_c",
                "avg_test_return_topk": 0.11,
                "avg_test_sharpe_topk": 1.2,
            },
        ],
    )
    _write_oos(tmp_path, [{"trade_trades": 4}, {"trade_trades": 5}, {"trade_trades": 6}])

    verdict = evaluate_walkforward_robustness(tmp_path)

    assert verdict["status"] == "pass"
    assert verdict["grade"] == "research_robustness_passed"
    assert verdict["positive_oos_splits"] == 3
    assert verdict["total_oos_trades"] == 15
    assert "paper" in verdict["recommendation"]
    assert "live" in verdict["recommendation"]


def test_walkforward_robustness_reviews_when_trade_count_unavailable(tmp_path):
    _write_summary(
        tmp_path,
        [
            {
                "split_name": "split_a",
                "avg_test_return_topk": 0.08,
                "avg_test_sharpe_topk": 0.9,
            },
            {
                "split_name": "split_b",
                "avg_test_return_topk": 0.03,
                "avg_test_sharpe_topk": 0.4,
            },
            {
                "split_name": "split_c",
                "avg_test_return_topk": 0.11,
                "avg_test_sharpe_topk": 1.2,
            },
        ],
    )

    verdict = evaluate_walkforward_robustness(tmp_path)

    assert verdict["status"] == "review"
    assert verdict["total_oos_trades"] is None
    assert any("trade count unavailable" in reason for reason in verdict["reasons"])


def test_walkforward_robustness_requires_summary_artifact(tmp_path):
    _stamp_authoritative_walkforward(tmp_path, [])
    with pytest.raises(WalkforwardRobustnessError, match="Required artifact missing"):
        evaluate_walkforward_robustness(tmp_path)


def test_walkforward_robustness_writes_json_and_markdown(tmp_path):
    _write_summary(
        tmp_path,
        [
            {
                "split_name": "split_a",
                "avg_test_return_topk": -0.30,
                "avg_test_sharpe_topk": -0.5,
            },
            {
                "split_name": "split_b",
                "avg_test_return_topk": 0.01,
                "avg_test_sharpe_topk": 0.2,
            },
            {
                "split_name": "split_c",
                "avg_test_return_topk": 0.02,
                "avg_test_sharpe_topk": 0.3,
            },
        ],
    )

    verdict = write_walkforward_robustness_verdict(tmp_path)

    assert verdict["status"] == "fail"
    assert (tmp_path / "robustness_verdict.json").exists()
    markdown = (tmp_path / "robustness_verdict.md").read_text(encoding="utf-8")
    assert "Walk-forward Robustness Verdict" in markdown
    assert "does not authorize paper trading" in markdown
