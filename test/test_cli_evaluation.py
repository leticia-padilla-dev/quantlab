from types import SimpleNamespace

import pandas as pd
import pytest

from quantlab.cli.evaluation import handle_evaluation_commands
from quantlab.errors import ConfigError
from support_quantitative_provenance import (
    stamp_authoritative_walkforward_fixture,
)


def _args(path=None):
    return SimpleNamespace(evaluate_walkforward_run=str(path) if path else None)


def _write_summary(run_dir, rows):
    pd.DataFrame(rows).to_csv(run_dir / "walkforward_summary.csv", index=False)
    stamp_authoritative_walkforward_fixture(run_dir, rows)


def test_evaluate_walkforward_run_writes_verdict_artifacts(tmp_path, capsys):
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

    result = handle_evaluation_commands(_args(tmp_path))

    captured = capsys.readouterr()
    assert result["status"] == "success"
    assert result["mode"] == "evaluation"
    assert result["verdict_status"] == "fail"
    assert "Walk-forward robustness verdict: FAIL" in captured.out
    assert "Positive OOS splits: 2/3" in captured.out
    assert "Worst OOS split return: -30.00%" in captured.out
    assert (tmp_path / "robustness_verdict.json").exists()
    assert (tmp_path / "robustness_verdict.md").exists()
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "metrics.json").exists()


def test_evaluate_walkforward_run_missing_summary_fails_clearly(tmp_path):
    stamp_authoritative_walkforward_fixture(tmp_path, [])
    with pytest.raises(ConfigError, match="Required artifact missing"):
        handle_evaluation_commands(_args(tmp_path))


def test_evaluate_walkforward_run_missing_directory_fails_clearly(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(ConfigError, match="does not exist"):
        handle_evaluation_commands(_args(missing))


def test_evaluation_handler_ignores_unrelated_commands():
    assert handle_evaluation_commands(_args()) is False
