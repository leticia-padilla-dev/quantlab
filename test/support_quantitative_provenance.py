from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quantlab.runs.quantitative_provenance import (
    attach_report_quantitative_provenance,
    attach_quantitative_provenance,
    propagate_quantitative_provenance_to_report,
)


SOURCE_COMMIT = "a" * 40


def stamp_authoritative_forward_fixture(session_dir: Path) -> None:
    """Stamp a synthetic forward fixture through the production builder."""

    state = json.loads(
        (session_dir / "portfolio_state.json").read_text(encoding="utf-8")
    )
    equity = pd.read_csv(session_dir / "forward_equity_curve.csv")["equity"]
    total_return = (
        float(equity.iloc[-1] / equity.iloc[0]) - 1.0
        if len(equity) and float(equity.iloc[0]) > 0
        else None
    )
    summary = {"total_return": total_return}
    session_id = str(state.get("session_id") or session_dir.name)
    report = {
        "schema_version": "1.0",
        "artifact_type": "quantlab_forward_report",
        "session_id": session_id,
        "summary": summary,
        "machine_contract": {
            "schema_version": "1.0",
            "contract_type": "quantlab.forward.result",
            "run_id": session_id,
            "summary": summary,
        },
    }
    report = attach_report_quantitative_provenance(
        report,
        artifact_type="forward",
        relative_run_path=session_dir.name,
        source_git_commit=SOURCE_COMMIT,
        run_id=session_id,
        metric_payload=report,
        annualization_applicability="unavailable",
        annualization_reason="synthetic_fixture_has_no_annualization_evidence",
    )
    (session_dir / "report.json").write_text(
        json.dumps(report),
        encoding="utf-8",
    )


def stamp_authoritative_paper_fixture(session_dir: Path) -> None:
    """Stamp an existing synthetic paper fixture as recognized evidence."""

    metadata_path = session_dir / "session_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    session_id = str(metadata.get("session_id") or session_dir.name)
    metadata["git_commit"] = SOURCE_COMMIT
    metrics = {
        "summary": {},
        "best_result": None,
        "leaderboard_size": 0,
    }
    metadata, metrics = attach_quantitative_provenance(
        metadata,
        metrics,
        artifact_type="paper",
        relative_run_path=session_dir.name,
        source_git_commit=SOURCE_COMMIT,
        run_id=session_id,
        annualization_applicability="unavailable",
        annualization_reason="synthetic_fixture_has_no_annualization_evidence",
    )
    report_path = session_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    header = report.setdefault("header", {})
    header["git_commit"] = SOURCE_COMMIT
    report["summary"] = metrics["summary"]
    report = propagate_quantitative_provenance_to_report(
        report,
        metadata,
        metrics,
    )
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    (session_dir / "metrics.json").write_text(
        json.dumps(metrics),
        encoding="utf-8",
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")


def stamp_authoritative_walkforward_fixture(
    run_dir: Path,
    rows: list[dict],
) -> None:
    """Stamp a synthetic walk-forward fixture as recognized evidence."""

    best_result = rows[0] if rows else None
    summary = {
        "total_return": (
            best_result.get("avg_test_return_topk") if best_result else None
        ),
        "sharpe_simple": (
            best_result.get("avg_test_sharpe_topk") if best_result else None
        ),
    }
    metadata, metrics = attach_quantitative_provenance(
        {
            "run_id": run_dir.name,
            "mode": "walkforward",
            "command": "sweep",
            "git_commit": SOURCE_COMMIT,
        },
        {
            "summary": summary,
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
            "kpi_summary": summary,
        },
        metadata,
        metrics,
    )
    for filename, payload in (
        ("metadata.json", metadata),
        ("metrics.json", metrics),
        ("report.json", report),
    ):
        (run_dir / filename).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
