"""Tests for src/quantlab/reporting/compare_runs.py (Stage J)."""

import json
import pytest
from pathlib import Path

from quantlab.reporting.compare_runs import (
    compare_runs,
    render_comparison_md,
    write_comparison,
)
from quantlab.runs.quantitative_provenance import (
    attach_quantitative_provenance,
    propagate_quantitative_provenance_to_report,
)


SOURCE_COMMIT = "a" * 40


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_run_dir(
    base: Path,
    name: str,
    sharpe: float | None,
    mode: str = "grid",
    total_return: float = 0.1,
) -> Path:
    """Create a minimal valid run directory for comparison tests."""
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    results = []
    if sharpe is not None:
        results = [{"sharpe_simple": sharpe, "total_return": total_return, "max_drawdown": -0.05, "trades": 5}]
    summary = {
        "sharpe_simple": sharpe,
        "total_return": total_return,
        "max_drawdown": -0.05,
        "trades": 5,
    }
    metadata = {
        "run_id": name,
        "mode": mode,
        "command": "sweep",
        "git_commit": SOURCE_COMMIT,
    }
    metrics = {
        "summary": summary,
        "best_result": results[0] if results else None,
        "leaderboard_size": len(results),
    }
    metadata, metrics = attach_quantitative_provenance(
        metadata,
        metrics,
        artifact_type="sweep",
        relative_run_path=name,
        source_git_commit=SOURCE_COMMIT,
        run_id=name,
    )
    report = propagate_quantitative_provenance_to_report({
        "header": {
            "run_id": name,
            "mode": mode,
            "created_at": "2023-03-06T00:00:00",
            "git_commit": SOURCE_COMMIT,
        },
        "results": results,
        "summary": summary,
        "config_resolved": {"ticker": "ETH-USD"},
    }, metadata, metrics)
    for filename, payload in (
        ("metadata.json", metadata),
        ("metrics.json", metrics),
        ("report.json", report),
    ):
        with open(d / filename, "w") as f:
            json.dump(payload, f)
    return d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_compare_runs_sorted_descending(tmp_path):
    """compare_runs must return runs sorted descending by the chosen metric."""
    low = _make_run_dir(tmp_path, "low", sharpe=0.5)
    high = _make_run_dir(tmp_path, "high", sharpe=2.3)
    mid = _make_run_dir(tmp_path, "mid", sharpe=1.1)

    payload = compare_runs([str(low), str(high), str(mid)], sort_by="sharpe_simple")

    sharpes = [r.get("sharpe_simple") for r in payload["runs"]]
    assert sharpes[0] == 2.3
    assert sharpes[1] == 1.1
    assert sharpes[2] == 0.5


def test_compare_best_run_selection(tmp_path):
    """best_run_id must point to the run with the highest metric value."""
    _make_run_dir(tmp_path, "worst", sharpe=0.2)
    _make_run_dir(tmp_path, "best", sharpe=3.0)
    _make_run_dir(tmp_path, "middle", sharpe=1.7)

    dirs = [str(tmp_path / n) for n in ("worst", "best", "middle")]
    payload = compare_runs(dirs, sort_by="sharpe_simple")

    assert payload["best_run_id"] == "best"
    assert "best" in payload["best_run_path"]


def test_compare_missing_metric_graceful(tmp_path):
    """A run without the sort metric must still appear, sorted last."""
    good = _make_run_dir(tmp_path, "good", sharpe=1.5)
    no_metric = _make_run_dir(tmp_path, "no_metric", sharpe=None)  # results=[] → no sharpe

    payload = compare_runs([str(good), str(no_metric)], sort_by="sharpe_simple")

    assert payload["n_runs"] == 2
    # good must come first
    assert payload["runs"][0]["run_id"] == "good"
    # no_metric still included
    assert payload["runs"][1]["run_id"] == "no_metric"
    # best run is 'good'
    assert payload["best_run_id"] == "good"


def test_write_comparison_creates_artifacts(tmp_path):
    """write_comparison must create compare_report.json + compare_report.md."""
    d1 = _make_run_dir(tmp_path / "runs", "alpha", sharpe=1.2)
    d2 = _make_run_dir(tmp_path / "runs", "beta", sharpe=0.8)
    out = tmp_path / "out"

    json_p, md_p = write_comparison([str(d1), str(d2)], out_path=str(out))

    assert Path(json_p).exists()
    assert Path(md_p).exists()

    # Strict JSON loads
    with open(json_p) as f:
        data = json.load(f)
    assert data["n_runs"] == 2
    assert data["best_run_id"] == "alpha"

    # Markdown headings
    md = Path(md_p).read_text(encoding="utf-8")
    assert "# Run Comparison" in md
    assert "## Summary" in md
    assert "## Ranking" in md
    assert "## Best Run" in md
    assert "## Runs Compared" in md


def test_compare_strict_json_no_nan(tmp_path):
    """NaN/Inf in run metrics must become null in compare_report.json."""
    d = _make_run_dir(
        tmp_path,
        "nan_run",
        sharpe=float("nan"),
        total_return=float("inf"),
    )

    out = tmp_path / "out"
    json_p, _ = write_comparison([str(d)], out_path=str(out))

    # Must load without error (strict JSON)
    with open(json_p) as f:
        data = json.load(f)
    run_entry = data["runs"][0]
    assert run_entry["sharpe_simple"] is None
    assert run_entry["total_return"] is None


def test_compare_empty_list(tmp_path):
    """write_comparison with an empty list must not crash."""
    out = tmp_path / "out"
    json_p, md_p = write_comparison([], out_path=str(out))

    with open(json_p) as f:
        data = json.load(f)
    assert data["n_runs"] == 0
    assert data["best_run_id"] is None

    md = Path(md_p).read_text(encoding="utf-8")
    assert "# Run Comparison" in md
