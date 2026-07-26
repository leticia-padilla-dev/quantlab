from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
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
    build_quantitative_input_manifest,
    build_quantitative_contract,
    compute_quantitative_evidence_digest,
    propagate_quantitative_provenance_to_report,
    resolve_source_git_commit,
    resolve_quantitative_authority,
    validate_quantitative_contract,
)
from quantlab.experiments.runner import _save_reproducibility_pack


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
    metadata_filename: str = "metadata.json",
    bound_input_filenames: tuple[str, ...] = (),
    annualization_status: str | None = None,
    annualization_reason: str | None = None,
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
    if annualization_status is not None:
        metrics["best_result"]["annualization_status"] = (
            annualization_status
        )
        metrics["best_result"]["annualization_reason"] = annualization_reason
    if bound_input_filenames:
        metrics["bound_quantitative_inputs"] = (
            build_quantitative_input_manifest(
                run_dir,
                bound_input_filenames,
            )
        )
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
        (metadata_filename, metadata),
        ("metrics.json", metrics),
        ("report.json", report),
    ):
        (run_dir / filename).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    return metadata, metrics, report


def _write_candidate_csv(path: Path, *, sharpe: float = 1.5) -> None:
    pd.DataFrame(
        [
            {
                "strategy_name": "rsi_ma_cross_v2",
                "ticker": "BTC-USD",
                "interval": "1d",
                "sharpe_simple": sharpe,
                "total_return": 0.2,
            }
        ]
    ).to_csv(path, index=False)


def _write_forward_inputs(session_dir: Path) -> None:
    (session_dir / "portfolio_state.json").write_text(
        json.dumps(
            {
                "session_id": session_dir.name,
                "starting_cash": 1000.0,
                "candidate": {
                    "ticker": "BTC-USD",
                    "strategy_name": "rsi_ma_cross_v2",
                },
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "timestamp": ["2026-01-01", "2026-01-02"],
            "equity": [1.0, 1.1],
        }
    ).to_csv(session_dir / "forward_equity_curve.csv", index=False)


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


def test_source_commit_resolves_from_a_non_editable_install(
    tmp_path: Path,
) -> None:
    wheel_dir = tmp_path / "wheel"
    site_packages = tmp_path / "site-packages"
    outside_checkout = tmp_path / "outside-checkout"
    repository_root = Path(__file__).resolve().parents[1]
    wheel_dir.mkdir()
    outside_checkout.mkdir()

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
            str(repository_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(wheel_dir.glob("quantlab-*.whl"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(site_packages),
            str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(site_packages)
    environment.pop("QUANTLAB_SOURCE_GIT_COMMIT", None)
    environment.pop("QUANTLAB_SOURCE_REPOSITORY", None)
    environment.pop("GITHUB_ACTIONS", None)
    environment.pop("GITHUB_SHA", None)
    resolved = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from quantlab.runs.quantitative_provenance "
                "import resolve_source_git_commit; "
                "print(resolve_source_git_commit())"
            ),
        ],
        cwd=outside_checkout,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert resolved == resolve_source_git_commit()
    assert len(resolved) == 40

    (site_packages / "quantlab" / "_build_info.py").unlink()
    unresolved = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from quantlab.runs.quantitative_provenance "
                "import resolve_source_git_commit; "
                "print(resolve_source_git_commit())"
            ),
        ],
        cwd=outside_checkout,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert unresolved.returncode != 0
    assert "Cannot identify the source Git commit" in unresolved.stderr


def test_source_commit_accepts_an_explicit_verified_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QUANTLAB_SOURCE_GIT_COMMIT", raising=False)
    monkeypatch.setenv(
        "QUANTLAB_SOURCE_REPOSITORY",
        str(Path(__file__).resolve().parents[1]),
    )

    assert resolve_source_git_commit() == subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    ).strip()


def test_source_commit_accepts_the_github_actions_evaluated_sha(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evaluated_sha = "b" * 40
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QUANTLAB_SOURCE_GIT_COMMIT", raising=False)
    monkeypatch.delenv("QUANTLAB_SOURCE_REPOSITORY", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SHA", evaluated_sha)

    assert resolve_source_git_commit() == evaluated_sha


@pytest.mark.parametrize(
    ("surface", "artifact_type", "invalid_content"),
    [
        ("metadata.json", "run", "{"),
        ("metrics.json", "run", "not-json"),
        ("report.json", "run", "[]"),
        ("session_metadata.json", "paper", "null"),
    ],
)
def test_present_invalid_canonical_surface_fails_closed(
    tmp_path: Path,
    surface: str,
    artifact_type: str,
    invalid_content: str,
) -> None:
    run_dir = tmp_path / f"invalid-{surface.replace('.', '-')}"
    metadata_filename = (
        "session_metadata.json"
        if surface == "session_metadata.json"
        else "metadata.json"
    )
    _write_current_run(
        run_dir,
        artifact_type=artifact_type,
        metadata_filename=metadata_filename,
    )
    (run_dir / surface).write_text(invalid_content, encoding="utf-8")

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert resolution.authority_reason == f"canonical_surface_invalid:{surface}"


def test_unreadable_broken_canonical_surface_fails_closed(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "broken-canonical-surface"
    _write_current_run(run_dir)
    report_path = run_dir / "report.json"
    report_path.unlink()
    report_path.symlink_to(run_dir / "missing-report-target.json")

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert (
        resolution.authority_reason
        == "canonical_surface_invalid:report.json"
    )


@pytest.mark.parametrize(
    "filename",
    ["leaderboard.csv", "experiments.csv", "oos_leaderboard.csv"],
)
def test_forward_candidate_rejects_tampered_bound_input(
    tmp_path: Path,
    filename: str,
) -> None:
    run_dir = tmp_path / f"candidate-{filename}"
    run_dir.mkdir()
    _write_candidate_csv(run_dir / filename)
    _write_current_run(
        run_dir,
        artifact_type=(
            "walkforward" if filename == "oos_leaderboard.csv" else "sweep"
        ),
        bound_input_filenames=(filename,),
    )

    assert load_candidate_from_run(run_dir).selection_value == 1.5

    _write_candidate_csv(run_dir / filename, sharpe=9.0)

    with pytest.raises(ValueError, match="not authoritative"):
        load_candidate_from_run(run_dir)


def test_walkforward_robustness_rejects_tampered_bound_summary(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "split_name": f"s{index}",
            "avg_test_return_topk": 0.1,
            "avg_test_sharpe_topk": 1.1,
        }
        for index in range(1, 4)
    ]
    pd.DataFrame(rows).to_csv(
        tmp_path / "walkforward_summary.csv",
        index=False,
    )
    _write_current_run(
        tmp_path,
        artifact_type="walkforward",
        bound_input_filenames=("walkforward_summary.csv",),
    )

    assert evaluate_walkforward_robustness(tmp_path)["status"] == "review"

    rows[0]["avg_test_return_topk"] = -0.9
    pd.DataFrame(rows).to_csv(
        tmp_path / "walkforward_summary.csv",
        index=False,
    )

    with pytest.raises(WalkforwardRobustnessError, match="not authoritative"):
        evaluate_walkforward_robustness(tmp_path)


@pytest.mark.parametrize(
    "filename",
    ["portfolio_state.json", "forward_equity_curve.csv"],
)
def test_portfolio_selection_rejects_tampered_bound_input(
    tmp_path: Path,
    filename: str,
) -> None:
    session_dir = tmp_path / f"forward-{filename}"
    session_dir.mkdir()
    _write_forward_inputs(session_dir)
    _write_current_run(
        session_dir,
        artifact_type="forward",
        bound_input_filenames=(
            "portfolio_state.json",
            "forward_equity_curve.csv",
        ),
    )

    sessions, _ = get_eligible_sessions([session_dir])
    assert len(sessions) == 1

    if filename.endswith(".json"):
        state = json.loads(
            (session_dir / filename).read_text(encoding="utf-8")
        )
        state["starting_cash"] = 999_999.0
        (session_dir / filename).write_text(
            json.dumps(state),
            encoding="utf-8",
        )
    else:
        pd.DataFrame(
            {
                "timestamp": ["2026-01-01", "2026-01-02"],
                "equity": [1.0, 99.0],
            }
        ).to_csv(session_dir / filename, index=False)

    sessions, stats = get_eligible_sessions([session_dir])

    assert sessions == []
    assert stats["sessions_excluded_non_authoritative"] == 1


@pytest.mark.parametrize(
    ("mode", "annualization_status", "annualization_reason", "expected"),
    [
        ("grid", "valid", None, ("applied", None)),
        (
            "grid",
            "unavailable",
            "interval_timestamp_mismatch",
            ("unavailable", "interval_timestamp_mismatch"),
        ),
        ("walkforward", "valid", None, ("applied", None)),
        (
            "walkforward",
            "unavailable",
            "insufficient_timestamp_evidence",
            ("unavailable", "insufficient_timestamp_evidence"),
        ),
    ],
)
def test_sweep_and_walkforward_derive_annualization_from_metrics(
    tmp_path: Path,
    mode: str,
    annualization_status: str,
    annualization_reason: str | None,
    expected: tuple[str, str | None],
) -> None:
    run_dir = tmp_path / f"{mode}-{annualization_status}"
    run_dir.mkdir()
    if mode == "grid":
        input_names = ("leaderboard.csv", "experiments.csv")
        for name in input_names:
            _write_candidate_csv(run_dir / name)
    else:
        input_names = ("walkforward_summary.csv", "oos_leaderboard.csv")
        _write_candidate_csv(run_dir / "oos_leaderboard.csv")
        pd.DataFrame(
            [
                {
                    "split_name": "s1",
                    "avg_test_return_topk": 0.1,
                    "avg_test_sharpe_topk": 1.0,
                }
            ]
        ).to_csv(run_dir / "walkforward_summary.csv", index=False)

    best_result = {
        "strategy_name": "rsi_ma_cross_v2",
        "sharpe_simple": 1.5,
        "total_return": 0.2,
        "annualization_status": annualization_status,
        "annualization_reason": annualization_reason,
    }
    _save_reproducibility_pack(
        run_dir,
        {"ticker": "BTC-USD", "interval": "1d"},
        mode,
        [best_result],
        bound_input_filenames=input_names,
    )

    metrics = json.loads(
        (run_dir / "metrics.json").read_text(encoding="utf-8")
    )
    annualization = metrics["quantitative_contract"]["policies"][
        "annualization"
    ]
    assert (
        annualization["applicability"],
        annualization["reason"],
    ) == expected
    assert resolve_quantitative_authority(run_dir).authority_status == (
        AUTHORITY_CURRENT
    )


def test_annualization_contract_contradiction_fails_closed(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "contradictory-annualization"
    metadata, metrics, report = _write_current_run(
        run_dir,
        artifact_type="sweep",
        annualization_status="unavailable",
        annualization_reason="interval_timestamp_mismatch",
    )
    contradictory = build_quantitative_contract(
        "sweep",
        annualization_applicability="applied",
    )
    canonical = metrics["canonical_metric_payload"]
    identity = build_artifact_identity(
        run_id=run_dir.name,
        relative_run_path=run_dir.name,
        source_git_commit=SOURCE_COMMIT,
        quantitative_contract=contradictory,
        canonical_metric_payload=canonical,
    )
    for filename, payload in (
        ("metadata.json", metadata),
        ("metrics.json", metrics),
        ("report.json", report),
    ):
        payload["quantitative_contract"] = contradictory
        payload["artifact_identity"] = identity
        if isinstance(payload.get("machine_contract"), dict):
            payload["machine_contract"]["quantitative_contract"] = (
                contradictory
            )
            payload["machine_contract"]["artifact_identity"] = identity
        (run_dir / filename).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    resolution = resolve_quantitative_authority(run_dir)

    assert resolution.authority_status == AUTHORITY_UNKNOWN
    assert resolution.authority_reason == "annualization_metric_contradiction"


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
