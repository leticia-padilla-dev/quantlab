from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from quantlab.cli.runs import handle_runs_commands
from quantlab.cli.paper_sessions import build_paper_sessions_promotion_report
from quantlab.evaluation.walkforward_robustness import (
    WalkforwardRobustnessError,
    evaluate_walkforward_robustness,
)
from quantlab.execution.forward_eval import load_candidate_from_run
from quantlab.reporting.compare_runs import compare_runs
from quantlab.reporting.portfolio_report import get_eligible_sessions
from quantlab.reporting.run_index import build_runs_index, load_run_summary
from quantlab.runs.quantitative_provenance import (
    AUTHORITY_CURRENT,
    AUTHORITY_SUPERSEDED,
    AUTHORITY_UNKNOWN,
    QUANTITATIVE_AUTHORITY_REGISTRY_FILENAME,
    attach_quantitative_provenance,
    build_artifact_identity,
    build_canonical_metric_payload,
    build_quantitative_contract,
    compute_quantitative_evidence_digest,
    propagate_quantitative_provenance_to_report,
    resolve_quantitative_authority,
    validate_quantitative_contract,
)


SOURCE_COMMIT = "a" * 40


def _write_legacy_run(run_dir: Path, *, sharpe: float = 1.5) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "mode": "grid",
                "status": "success",
                "git_commit": SOURCE_COMMIT,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "status": "success",
                "summary": {
                    "sharpe_simple": sharpe,
                    "total_return": 0.2,
                    "max_drawdown": -0.1,
                    "trades": 4,
                },
                "best_result": {
                    "strategy_name": "rsi_ma_cross_v2",
                    "sharpe_simple": sharpe,
                    "total_return": 0.2,
                },
                "leaderboard_size": 1,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "report.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "header": {
                    "run_id": run_dir.name,
                    "mode": "grid",
                    "git_commit": SOURCE_COMMIT,
                },
                "results": [
                    {
                        "strategy_name": "rsi_ma_cross_v2",
                        "sharpe_simple": sharpe,
                        "total_return": 0.2,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_current_run(
    run_dir: Path,
    *,
    artifact_type: str = "run",
    sharpe: float = 1.5,
    source_commit: str = SOURCE_COMMIT,
) -> tuple[dict, dict, dict]:
    run_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "run_id": run_dir.name,
        "mode": artifact_type,
        "command": "sweep" if artifact_type != "run" else "run",
        "status": "success",
        "git_commit": source_commit,
    }
    metrics = {
        "status": "success",
        "summary": {
            "sharpe_simple": sharpe,
            "total_return": 0.2,
            "max_drawdown": -0.1,
            "trades": 4,
        },
        "best_result": {
            "strategy_name": "rsi_ma_cross_v2",
            "sharpe_simple": sharpe,
            "total_return": 0.2,
        },
        "leaderboard_size": 1,
    }
    metadata, metrics = attach_quantitative_provenance(
        metadata,
        metrics,
        artifact_type=artifact_type,
        relative_run_path=run_dir.name,
        source_git_commit=source_commit,
        run_id=run_dir.name,
    )
    report = propagate_quantitative_provenance_to_report(
        {
            "schema_version": "1.0",
            "header": {
                "run_id": run_dir.name,
                "mode": artifact_type,
                "git_commit": source_commit,
            },
            "results": [metrics["best_result"]],
            "summary": metrics["summary"],
            "machine_contract": {
                "schema_version": "1.0",
                "contract_type": f"quantlab.{metadata['command']}.result",
                "summary": metrics["summary"],
            },
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
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    return metadata, metrics, report


def _write_registry(root: Path, entries: object) -> Path:
    path = root / QUANTITATIVE_AUTHORITY_REGISTRY_FILENAME
    path.write_text(
        json.dumps({"schema_version": "1.0", "entries": entries}, indent=2),
        encoding="utf-8",
    )
    return path


def test_recognized_artifact_is_visible_and_eligible(tmp_path: Path) -> None:
    run_dir = tmp_path / "current"
    _write_current_run(run_dir)

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_CURRENT
    assert resolution.visible is True
    assert resolution.ranking_eligible is True
    assert resolution.comparison_eligible is True
    assert resolution.forward_eligible is True
    assert resolution.promotion_eligible is True


def test_legacy_run_remains_visible_but_is_not_authoritative(tmp_path: Path) -> None:
    run_dir = tmp_path / "legacy"
    _write_legacy_run(run_dir)

    summary = load_run_summary(run_dir)

    assert summary["run_id"] == "legacy"
    assert summary["authority_status"] == "unknown_provenance"
    assert summary["ranking_eligible"] is False
    assert summary["comparison_eligible"] is False
    assert summary["forward_eligible"] is False
    assert summary["promotion_eligible"] is False


def test_exact_external_supersession_is_non_destructive(tmp_path: Path) -> None:
    run_dir = tmp_path / "current"
    metadata, _, _ = _write_current_run(run_dir)
    before = {
        path.name: path.read_bytes()
        for path in run_dir.iterdir()
        if path.is_file()
    }
    _write_registry(
        tmp_path,
        [
            {
                "status": "superseded",
                "reason": "wave_1_calculation_contract_replaced",
                "artifact_identity": metadata["artifact_identity"],
            }
        ],
    )

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_SUPERSEDED
    assert resolution.ranking_eligible is False
    assert {
        path.name: path.read_bytes()
        for path in run_dir.iterdir()
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    "registry_payload",
    [
        "not-json",
        {"schema_version": "1.0", "entries": "not-a-list"},
        {
            "schema_version": "1.0",
            "entries": [{"status": "superseded"}],
        },
    ],
    ids=["malformed-json", "malformed-root", "malformed-entry"],
)
def test_malformed_overlay_fails_closed(
    tmp_path: Path, registry_payload: object
) -> None:
    run_dir = tmp_path / "current"
    _write_current_run(run_dir)
    registry_path = tmp_path / QUANTITATIVE_AUTHORITY_REGISTRY_FILENAME
    if registry_payload == "not-json":
        registry_path.write_text("{", encoding="utf-8")
    else:
        registry_path.write_text(
            json.dumps(registry_payload), encoding="utf-8"
        )

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert (
        resolution.authority_reason
        == "authority_registry_invalid_or_ambiguous"
    )


def test_invalid_registry_precedes_missing_legacy_contract(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "legacy"
    _write_legacy_run(run_dir)
    (tmp_path / QUANTITATIVE_AUTHORITY_REGISTRY_FILENAME).write_text(
        "{",
        encoding="utf-8",
    )

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert (
        resolution.authority_reason
        == "authority_registry_invalid_or_ambiguous"
    )


@pytest.mark.parametrize("conflict_kind", ["duplicate", "conflicting_digest"])
def test_duplicate_or_conflicting_overlay_fails_closed(
    tmp_path: Path, conflict_kind: str
) -> None:
    run_dir = tmp_path / "current"
    metadata, _, _ = _write_current_run(run_dir)
    first = {
        "status": "superseded",
        "reason": "first",
        "artifact_identity": metadata["artifact_identity"],
    }
    second = json.loads(json.dumps(first))
    second["reason"] = "second"
    if conflict_kind == "conflicting_digest":
        second["artifact_identity"]["quantitative_evidence_digest"] = "b" * 64
    _write_registry(tmp_path, [first, second])

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert (
        resolution.authority_reason
        == "authority_registry_invalid_or_ambiguous"
    )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        (
            lambda contract: contract["policies"].pop("fee_and_slippage"),
            "policy_missing:fee_and_slippage",
        ),
        (
            lambda contract: contract["policies"]["fee_and_slippage"].update(
                {"version": "unknown"}
            ),
            "policy_version_unknown:fee_and_slippage",
        ),
        (
            lambda contract: contract["policies"]["fee_and_slippage"].update(
                {"applicability": "not_applicable"}
            ),
            "policy_applicability_invalid:fee_and_slippage",
        ),
    ],
    ids=["required-missing", "unknown-version", "invalid-not-applicable"],
)
def test_missing_unknown_or_inapplicable_required_policy_is_rejected(
    mutation, expected_error: str
) -> None:
    contract = build_quantitative_contract("run")
    mutation(contract)

    assert expected_error in validate_quantitative_contract(contract)


def test_not_applicable_is_accepted_only_by_artifact_policy_matrix() -> None:
    run_contract = build_quantitative_contract("run")
    walkforward_contract = build_quantitative_contract("walkforward")
    forward_contract = build_quantitative_contract(
        "forward", forward_resume_applied=True
    )

    assert validate_quantitative_contract(run_contract) == []
    assert (
        run_contract["policies"]["oos_equity_stitching"]["applicability"]
        == "not_applicable"
    )
    assert validate_quantitative_contract(walkforward_contract) == []
    assert (
        walkforward_contract["policies"]["oos_equity_stitching"][
            "applicability"
        ]
        == "applied"
    )
    assert validate_quantitative_contract(forward_contract) == []
    assert (
        forward_contract["policies"]["forward_resume_accounting"][
            "applicability"
        ]
        == "applied"
    )


def test_digest_is_canonical_and_ignores_administrative_location_fields() -> None:
    contract = build_quantitative_contract("run")
    identity = {
        "run_id": "run-a",
        "relative_run_path": "run-a",
        "source_git_commit": SOURCE_COMMIT,
    }
    metrics_a = {
        "summary": {
            "total_return": 0.2,
            "sharpe_simple": 1.5,
            "generated_at": "2026-01-01T00:00:00",
            "filesystem_path": "/private/a",
        },
        "leaderboard_size": 1,
    }
    metrics_b = {
        "leaderboard_size": 1,
        "summary": {
            "filesystem_path": "/different/root",
            "generated_at": "2027-01-01T00:00:00",
            "sharpe_simple": 1.5,
            "total_return": 0.2,
        },
    }

    digest_a = compute_quantitative_evidence_digest(
        artifact_identity_without_digest=identity,
        quantitative_contract=contract,
        canonical_metric_payload=build_canonical_metric_payload(metrics_a),
    )
    digest_b = compute_quantitative_evidence_digest(
        artifact_identity_without_digest=dict(reversed(list(identity.items()))),
        quantitative_contract=json.loads(
            json.dumps(contract, sort_keys=False)
        ),
        canonical_metric_payload=build_canonical_metric_payload(metrics_b),
    )

    assert digest_a == digest_b


@pytest.mark.parametrize(
    "changed_component",
    ["metrics", "policy", "applicability", "identity", "commit"],
)
def test_digest_changes_for_real_quantitative_or_identity_change(
    changed_component: str,
) -> None:
    contract = build_quantitative_contract("forward")
    metrics = {"summary": {"total_return": 0.2, "sharpe_simple": 1.5}}
    identity = {
        "run_id": "run-a",
        "relative_run_path": "run-a",
        "source_git_commit": SOURCE_COMMIT,
    }

    def digest() -> str:
        return compute_quantitative_evidence_digest(
            artifact_identity_without_digest=identity,
            quantitative_contract=contract,
            canonical_metric_payload=build_canonical_metric_payload(metrics),
        )

    original = digest()
    if changed_component == "metrics":
        metrics["summary"]["total_return"] = 0.21
    elif changed_component == "policy":
        contract["policies"]["fee_and_slippage"]["version"] = "changed"
    elif changed_component == "applicability":
        contract["policies"]["forward_resume_accounting"][
            "applicability"
        ] = "applied"
    elif changed_component == "identity":
        identity["relative_run_path"] = "run-b"
    else:
        identity["source_git_commit"] = "b" * 40

    assert digest() != original


def test_metric_tampering_is_detected(tmp_path: Path) -> None:
    run_dir = tmp_path / "current"
    _write_current_run(run_dir)
    metrics_path = run_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["summary"]["total_return"] = 99.0
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert resolution.authority_reason == "canonical_metric_payload_mismatch"


def test_report_tampering_is_detected_even_when_metrics_are_unchanged(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "current"
    _write_current_run(run_dir)
    report_path = run_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["results"][0]["sharpe_simple"] = 99.0
    report_path.write_text(json.dumps(report), encoding="utf-8")

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert resolution.authority_reason == "canonical_metric_payload_mismatch"


def test_editable_authority_status_cannot_make_legacy_artifact_current(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "legacy"
    _write_legacy_run(run_dir)
    metadata_path = run_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["authority_status"] = "current"
    metadata["ranking_eligible"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert resolution.ranking_eligible is False


def test_runs_index_exposes_all_authority_states(tmp_path: Path) -> None:
    current_dir = tmp_path / "current"
    superseded_dir = tmp_path / "superseded"
    legacy_dir = tmp_path / "legacy"
    _write_current_run(current_dir)
    superseded_metadata, _, _ = _write_current_run(superseded_dir)
    _write_legacy_run(legacy_dir)
    _write_registry(
        tmp_path,
        [
            {
                "status": "superseded",
                "reason": "replaced",
                "artifact_identity": superseded_metadata["artifact_identity"],
            }
        ],
    )

    payload = build_runs_index(tmp_path)
    indexed = {row["run_id"]: row for row in payload["runs"]}

    assert indexed["current"]["authority_status"] == AUTHORITY_CURRENT
    assert indexed["superseded"]["authority_status"] == AUTHORITY_SUPERSEDED
    assert indexed["legacy"]["authority_status"] == AUTHORITY_UNKNOWN
    assert indexed["current"]["ranking_eligible"] is True
    assert indexed["superseded"]["ranking_eligible"] is False
    assert indexed["legacy"]["promotion_eligible"] is False


def test_compare_runs_excludes_legacy_evidence_from_normal_ranking(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_legacy_run(first, sharpe=3.0)
    _write_legacy_run(second, sharpe=2.0)

    payload = compare_runs([first, second])

    assert payload["n_runs"] == 0
    assert payload["best_run_id"] is None
    assert payload["excluded_non_authoritative"] == 2


def test_runs_best_does_not_select_legacy_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_legacy_run(tmp_path / "legacy")
    args = SimpleNamespace(
        runs_list=None,
        runs_show=None,
        runs_best=str(tmp_path),
        metric="sharpe_simple",
    )

    assert handle_runs_commands(args) is True

    output = capsys.readouterr().out
    assert "No authoritative runs" in output
    assert "Best run" not in output


def test_forward_candidate_loading_rejects_legacy_evidence(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "legacy"
    _write_legacy_run(run_dir)

    with pytest.raises(ValueError, match="not authoritative"):
        load_candidate_from_run(run_dir)


def test_robustness_rejects_legacy_evidence(tmp_path: Path) -> None:
    _write_legacy_run(tmp_path)
    pd.DataFrame(
        [
            {
                "split_name": "s1",
                "avg_test_return_topk": 0.1,
                "avg_test_sharpe_topk": 1.1,
            },
            {
                "split_name": "s2",
                "avg_test_return_topk": 0.2,
                "avg_test_sharpe_topk": 1.2,
            },
            {
                "split_name": "s3",
                "avg_test_return_topk": 0.3,
                "avg_test_sharpe_topk": 1.3,
            },
        ]
    ).to_csv(tmp_path / "walkforward_summary.csv", index=False)

    with pytest.raises(WalkforwardRobustnessError, match="not authoritative"):
        evaluate_walkforward_robustness(tmp_path)


def test_portfolio_ranking_excludes_legacy_forward_session(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "legacy_forward"
    session_dir.mkdir()
    (session_dir / "portfolio_state.json").write_text(
        json.dumps({"session_id": "legacy_forward", "starting_cash": 1000.0})
    )
    pd.DataFrame(
        {
            "timestamp": ["2026-01-01", "2026-01-02"],
            "equity": [1.0, 1.1],
        }
    ).to_csv(session_dir / "forward_equity_curve.csv", index=False)

    sessions, stats = get_eligible_sessions([session_dir], top_n=1)

    assert sessions == []
    assert stats["sessions_excluded_non_authoritative"] == 1


def test_paper_promotion_excludes_legacy_session(tmp_path: Path) -> None:
    session_dir = tmp_path / "legacy_paper"
    session_dir.mkdir()
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": "legacy_paper",
                "mode": "paper",
                "status": "success",
            }
        )
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": "legacy_paper",
                "status": "success",
                "terminal": True,
            }
        )
    )
    (session_dir / "report.json").write_text(
        json.dumps(
            {
                "status": "success",
                "machine_contract": {
                    "contract_type": "quantlab.paper.result",
                },
            }
        )
    )

    report = build_paper_sessions_promotion_report(tmp_path)

    assert report["promotion_ready_count"] == 0
    assert report["promotion_blocked_count"] == 1
    assert (
        "quantitative_authority_unknown_provenance"
        in report["blocked_sessions"][0]["broker_promotion_blockers"]
    )
