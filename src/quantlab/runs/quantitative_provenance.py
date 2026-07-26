"""Quantitative artifact provenance, integrity, and authority resolution.

This module is the single source of truth for the calculation-contract
metadata attached to new quantitative artifacts.  It also owns the canonical
metric digest and the fail-closed authority resolver used by ranking and
promotion consumers.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
from importlib import metadata as importlib_metadata
from importlib import util as importlib_util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlparse

from quantlab.runs.artifacts import (
    CANONICAL_METADATA_FILENAME,
    CANONICAL_METRICS_FILENAME,
    CANONICAL_REPORT_FILENAME,
    PAPER_SESSION_METADATA_FILENAME,
)


QUANTITATIVE_CONTRACT_VERSION = "1.0"
QUANTITATIVE_AUTHORITY_REGISTRY_FILENAME = (
    "quantitative_authority_registry.json"
)
QUANTITATIVE_AUTHORITY_REGISTRY_VERSION = "1.0"

AUTHORITY_CURRENT = "current"
AUTHORITY_SUPERSEDED = "superseded"
AUTHORITY_UNKNOWN = "unknown_provenance"

POLICY_VERSIONS = {
    "oos_equity_stitching": "continuous_compounding_v1",
    "forward_resume_accounting": "exactly_once_v1",
    "fee_and_slippage": "notional_adverse_price_v1",
    "annualization": "interval_timestamp_validated_v1",
}

_ARTIFACT_TYPES = {"run", "sweep", "walkforward", "paper", "forward"}
_CANONICAL_METRIC_FIELDS = (
    "summary",
    "best_result",
    "bound_quantitative_inputs",
    "leaderboard_size",
    "n_runs",
    "n_train_runs",
    "n_selected",
    "n_test_runs",
)
_DIGEST_EXCLUDED_FIELDS = {
    "quantitative_evidence_digest",
    "generated_at",
    "filesystem_path",
}
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
_BOUND_INPUT_SCHEMA_VERSION = "1.0"
_BOUND_QUANTITATIVE_INPUTS = {
    "leaderboard.csv",
    "experiments.csv",
    "oos_leaderboard.csv",
    "walkforward_summary.csv",
    "portfolio_state.json",
    "forward_equity_curve.csv",
}


def resolve_source_git_commit() -> str:
    """Resolve the exact source commit from a verifiable source.

    Non-editable builds embed the commit in ``quantlab._build_info``.  An
    operator may alternatively supply a full commit or an explicit repository
    path.  Checkout execution finally accepts the current working tree when it
    is inside a Git repository.  Package installation paths are never treated
    as repository roots.
    """

    explicit_commit = os.environ.get("QUANTLAB_SOURCE_GIT_COMMIT")
    if explicit_commit is not None:
        return _validated_commit(
            explicit_commit,
            source="QUANTLAB_SOURCE_GIT_COMMIT",
        )

    explicit_repository = os.environ.get("QUANTLAB_SOURCE_REPOSITORY")
    if explicit_repository:
        return _git_commit_from_repository(
            Path(explicit_repository),
            source="QUANTLAB_SOURCE_REPOSITORY",
        )

    github_sha = os.environ.get("GITHUB_SHA")
    if (
        os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"
        and github_sha is not None
    ):
        return _validated_commit(
            github_sha,
            source="GitHub Actions GITHUB_SHA",
        )

    try:
        from quantlab._build_info import SOURCE_GIT_COMMIT
    except (ImportError, AttributeError):
        SOURCE_GIT_COMMIT = None
    if SOURCE_GIT_COMMIT is not None:
        return _validated_commit(
            SOURCE_GIT_COMMIT,
            source="embedded package build metadata",
        )

    editable_repository = _editable_install_repository()
    if editable_repository is not None:
        return _git_commit_from_repository(
            editable_repository,
            source="editable installation metadata",
        )

    try:
        repository_root = subprocess.check_output(
            ["git", "-C", str(Path.cwd()), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        repository_root = ""
    if repository_root:
        return _git_commit_from_repository(
            Path(repository_root),
            source="current working checkout",
        )

    raise RuntimeError(
        "Cannot identify the source Git commit for a new quantitative "
        "artifact"
    )


def _editable_install_repository() -> Path | None:
    try:
        direct_url_text = importlib_metadata.distribution("quantlab").read_text(
            "direct_url.json"
        )
        direct_url = json.loads(direct_url_text or "")
    except (
        importlib_metadata.PackageNotFoundError,
        json.JSONDecodeError,
        TypeError,
    ):
        return None
    if not isinstance(direct_url, dict):
        return None
    directory_info = direct_url.get("dir_info")
    if (
        not isinstance(directory_info, dict)
        or directory_info.get("editable") is not True
    ):
        return None
    parsed = urlparse(str(direct_url.get("url") or ""))
    if parsed.scheme != "file":
        return None
    repository = Path(unquote(parsed.path)).resolve()
    spec = importlib_util.find_spec("quantlab")
    origin = Path(spec.origin).resolve() if spec and spec.origin else None
    if origin is None or repository not in origin.parents:
        return None
    return repository


def _validated_commit(value: Any, *, source: str) -> str:
    commit = str(value).strip()
    if not _COMMIT_RE.fullmatch(commit):
        raise RuntimeError(
            f"{source} did not provide a full 40-character Git SHA"
        )
    return commit.lower()


def _git_commit_from_repository(path: Path, *, source: str) -> str:
    try:
        repository_root = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        commit = subprocess.check_output(
            ["git", "-C", repository_root, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            f"{source} is not a readable Git checkout"
        ) from exc
    return _validated_commit(commit, source=source)


@dataclass(frozen=True)
class AuthorityResolution:
    """Derived authority and eligibility for one artifact directory."""

    authority_status: str
    authority_reason: str
    quantitative_contract_version: str | None
    quantitative_evidence_digest: str | None
    visible: bool
    ranking_eligible: bool
    comparison_eligible: bool
    forward_eligible: bool
    promotion_eligible: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for indexes and reports."""

        return asdict(self)


@dataclass(frozen=True)
class _JsonSurface:
    state: str
    payload: dict[str, Any]


def build_quantitative_contract(
    artifact_type: str,
    *,
    annualization_applicability: str = "applied",
    annualization_reason: str | None = None,
    forward_resume_applied: bool = False,
) -> dict[str, Any]:
    """Build the recognized calculation contract for an artifact type."""

    normalized_type = str(artifact_type).strip().lower()
    if normalized_type not in _ARTIFACT_TYPES:
        raise ValueError(
            f"Unknown quantitative artifact type: {artifact_type!r}"
        )
    if annualization_applicability not in {"applied", "unavailable"}:
        raise ValueError(
            "annualization_applicability must be 'applied' or 'unavailable'"
        )
    if (
        annualization_applicability == "unavailable"
        and not str(annualization_reason or "").strip()
    ):
        raise ValueError(
            "annualization_reason is required when annualization is unavailable"
        )
    if annualization_applicability == "applied":
        annualization_reason = None

    policies = {
        "oos_equity_stitching": {
            "version": POLICY_VERSIONS["oos_equity_stitching"],
            "applicability": (
                "applied"
                if normalized_type == "walkforward"
                else "not_applicable"
            ),
        },
        "forward_resume_accounting": {
            "version": POLICY_VERSIONS["forward_resume_accounting"],
            "applicability": (
                "applied"
                if normalized_type == "forward" and forward_resume_applied
                else "not_applicable"
            ),
        },
        "fee_and_slippage": {
            "version": POLICY_VERSIONS["fee_and_slippage"],
            "applicability": "applied",
        },
        "annualization": {
            "version": POLICY_VERSIONS["annualization"],
            "applicability": annualization_applicability,
            "reason": annualization_reason,
        },
    }
    return {
        "version": QUANTITATIVE_CONTRACT_VERSION,
        "artifact_type": normalized_type,
        "policies": policies,
    }


def validate_quantitative_contract(contract: Any) -> list[str]:
    """Return deterministic validation errors for an embedded contract."""

    if not isinstance(contract, dict):
        return ["quantitative_contract_missing"]
    errors: list[str] = []
    if contract.get("version") != QUANTITATIVE_CONTRACT_VERSION:
        errors.append("quantitative_contract_version_unknown")

    artifact_type = contract.get("artifact_type")
    if artifact_type not in _ARTIFACT_TYPES:
        errors.append("quantitative_artifact_type_unknown")

    policies = contract.get("policies")
    if not isinstance(policies, dict):
        return errors + ["quantitative_contract_policies_missing"]

    for name, version in POLICY_VERSIONS.items():
        policy = policies.get(name)
        if not isinstance(policy, dict):
            errors.append(f"policy_missing:{name}")
            continue
        if policy.get("version") != version:
            errors.append(f"policy_version_unknown:{name}")
        applicability = policy.get("applicability")
        allowed = _allowed_applicability(str(artifact_type), name)
        if applicability not in allowed:
            errors.append(f"policy_applicability_invalid:{name}")
        if name == "annualization":
            reason = policy.get("reason")
            if applicability == "unavailable":
                if not isinstance(reason, str) or not reason.strip():
                    errors.append("policy_reason_missing:annualization")
            elif reason not in (None, ""):
                errors.append("policy_reason_unexpected:annualization")

    unexpected = sorted(set(policies) - set(POLICY_VERSIONS))
    errors.extend(f"policy_unknown:{name}" for name in unexpected)
    return errors


def build_canonical_metric_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Select and normalize the metric-bearing fields used by the digest."""

    selected = {
        field: payload[field]
        for field in _CANONICAL_METRIC_FIELDS
        if field in payload
    }
    if not selected and any(
        field in payload
        for field in (
            "total_return",
            "sharpe_simple",
            "max_drawdown",
            "trades",
            "win_rate",
            "annualized_volatility",
        )
    ):
        selected["summary"] = dict(payload)
    return _canonicalize(selected)


def build_quantitative_input_manifest(
    artifact_dir: str | Path,
    filenames: Iterable[str],
) -> dict[str, Any]:
    """Canonically bind quantitative input files consumed after authority.

    CSV files are represented as ordered columns and rows; JSON inputs must be
    objects.  The resulting manifest is itself part of the canonical metric
    payload, so every consumer verifies the same representation and digest.
    """

    root = Path(artifact_dir)
    files: dict[str, Any] = {}
    for filename in sorted(set(str(name) for name in filenames)):
        if filename not in _BOUND_QUANTITATIVE_INPUTS:
            raise ValueError(
                f"Unsupported bound quantitative input: {filename}"
            )
        representation, input_format, record_count = (
            _canonical_quantitative_input(root / filename)
        )
        serialized = json.dumps(
            representation,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        files[filename] = {
            "format": input_format,
            "record_count": record_count,
            "sha256": hashlib.sha256(serialized).hexdigest(),
        }
    return {
        "schema_version": _BOUND_INPUT_SCHEMA_VERSION,
        "files": files,
    }


def derive_annualization_provenance(
    metric_payload: Mapping[str, Any],
) -> dict[str, str | None]:
    """Derive contract applicability from authoritative metric diagnostics."""

    candidates: list[Mapping[str, Any]] = []
    best_result = metric_payload.get("best_result")
    summary = metric_payload.get("summary")
    if isinstance(best_result, Mapping):
        candidates.append(best_result)
    if isinstance(summary, Mapping):
        candidates.append(summary)
    candidates.append(metric_payload)

    status: Any = None
    reason: Any = None
    for candidate in candidates:
        if "annualization_status" in candidate:
            status = candidate.get("annualization_status")
            reason = candidate.get("annualization_reason")
            break

    if status == "valid":
        return {
            "annualization_applicability": "applied",
            "annualization_reason": None,
        }
    if status == "unavailable":
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                "Unavailable annualization metrics require a reason"
            )
        return {
            "annualization_applicability": "unavailable",
            "annualization_reason": reason.strip(),
        }
    if status in (None, ""):
        return {
            "annualization_applicability": "unavailable",
            "annualization_reason": "annualization_evidence_missing",
        }
    raise ValueError(f"Unknown metric annualization status: {status!r}")


def compute_quantitative_evidence_digest(
    *,
    artifact_identity_without_digest: Mapping[str, Any],
    quantitative_contract: Mapping[str, Any],
    canonical_metric_payload: Mapping[str, Any],
) -> str:
    """Return the SHA-256 digest of the canonical quantitative evidence."""

    payload = _canonicalize(
        {
            "artifact_identity": dict(artifact_identity_without_digest),
            "quantitative_contract": dict(quantitative_contract),
            "canonical_metric_payload": dict(canonical_metric_payload),
        }
    )
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def build_artifact_identity(
    *,
    run_id: str | None,
    relative_run_path: str,
    source_git_commit: str,
    quantitative_contract: Mapping[str, Any],
    canonical_metric_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a compound identity and bind it to the evidence digest."""

    identity_without_digest = {
        "run_id": str(run_id) if run_id not in (None, "") else None,
        "relative_run_path": normalize_relative_run_path(relative_run_path),
        "source_git_commit": str(source_git_commit).strip(),
    }
    digest = compute_quantitative_evidence_digest(
        artifact_identity_without_digest=identity_without_digest,
        quantitative_contract=quantitative_contract,
        canonical_metric_payload=canonical_metric_payload,
    )
    return {
        **identity_without_digest,
        "quantitative_evidence_digest": digest,
    }


def attach_quantitative_provenance(
    metadata: Mapping[str, Any],
    metrics: Mapping[str, Any],
    *,
    artifact_type: str,
    relative_run_path: str,
    source_git_commit: str,
    run_id: str | None = None,
    annualization_applicability: str | None = None,
    annualization_reason: str | None = None,
    forward_resume_applied: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Attach one shared contract and identity to metadata and metrics."""

    if annualization_applicability is None:
        annualization = derive_annualization_provenance(metrics)
        annualization_applicability = str(
            annualization["annualization_applicability"]
        )
        annualization_reason = annualization["annualization_reason"]
    contract = build_quantitative_contract(
        artifact_type,
        annualization_applicability=annualization_applicability,
        annualization_reason=annualization_reason,
        forward_resume_applied=forward_resume_applied,
    )
    canonical_metrics = build_canonical_metric_payload(metrics)
    identity = build_artifact_identity(
        run_id=run_id,
        relative_run_path=relative_run_path,
        source_git_commit=source_git_commit,
        quantitative_contract=contract,
        canonical_metric_payload=canonical_metrics,
    )
    metadata_payload = dict(metadata)
    metrics_payload = dict(metrics)
    for payload in (metadata_payload, metrics_payload):
        payload["quantitative_contract"] = contract
        payload["artifact_identity"] = identity
        payload["canonical_metric_payload"] = canonical_metrics
    return metadata_payload, metrics_payload


def attach_report_quantitative_provenance(
    report: Mapping[str, Any],
    *,
    artifact_type: str,
    relative_run_path: str,
    source_git_commit: str,
    run_id: str | None,
    metric_payload: Mapping[str, Any],
    annualization_applicability: str | None = None,
    annualization_reason: str | None = None,
    forward_resume_applied: bool = False,
) -> dict[str, Any]:
    """Attach provenance directly to a report-only artifact producer."""

    if annualization_applicability is None:
        annualization = derive_annualization_provenance(metric_payload)
        annualization_applicability = str(
            annualization["annualization_applicability"]
        )
        annualization_reason = annualization["annualization_reason"]
    contract = build_quantitative_contract(
        artifact_type,
        annualization_applicability=annualization_applicability,
        annualization_reason=annualization_reason,
        forward_resume_applied=forward_resume_applied,
    )
    identity = build_artifact_identity(
        run_id=run_id,
        relative_run_path=relative_run_path,
        source_git_commit=source_git_commit,
        quantitative_contract=contract,
        canonical_metric_payload=build_canonical_metric_payload(metric_payload),
    )
    payload = dict(report)
    payload["quantitative_contract"] = contract
    payload["artifact_identity"] = identity
    canonical_metrics = build_canonical_metric_payload(metric_payload)
    payload["canonical_metric_payload"] = canonical_metrics
    machine_contract = payload.get("machine_contract")
    if isinstance(machine_contract, dict):
        machine_payload = dict(machine_contract)
        machine_payload["quantitative_contract"] = contract
        machine_payload["artifact_identity"] = identity
        machine_payload["canonical_metric_payload"] = canonical_metrics
        payload["machine_contract"] = machine_payload
    return payload


def propagate_quantitative_provenance_to_report(
    report: Mapping[str, Any],
    metadata: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Copy matching producer provenance into the canonical report."""

    meta_contract = metadata.get("quantitative_contract")
    metrics_contract = metrics.get("quantitative_contract")
    meta_identity = metadata.get("artifact_identity")
    metrics_identity = metrics.get("artifact_identity")
    meta_canonical_metrics = metadata.get("canonical_metric_payload")
    metrics_canonical_metrics = metrics.get("canonical_metric_payload")
    if not any(
        value is not None
        for value in (
            meta_contract,
            metrics_contract,
            meta_identity,
            metrics_identity,
            meta_canonical_metrics,
            metrics_canonical_metrics,
        )
    ):
        return dict(report)
    if (
        meta_contract != metrics_contract
        or meta_identity != metrics_identity
        or meta_canonical_metrics != metrics_canonical_metrics
    ):
        raise ValueError("Quantitative provenance mismatch between artifacts")

    payload = dict(report)
    payload["quantitative_contract"] = meta_contract
    payload["artifact_identity"] = meta_identity
    payload["canonical_metric_payload"] = meta_canonical_metrics
    machine_contract = payload.get("machine_contract")
    if isinstance(machine_contract, dict):
        machine_payload = dict(machine_contract)
        machine_payload["quantitative_contract"] = meta_contract
        machine_payload["artifact_identity"] = meta_identity
        machine_payload["canonical_metric_payload"] = meta_canonical_metrics
        payload["machine_contract"] = machine_payload
    return payload


def resolve_quantitative_authority(
    artifact_dir: str | Path,
    *,
    overlay_path: str | Path | None = None,
    required_inputs: Iterable[str] = (),
) -> AuthorityResolution:
    """Derive artifact authority without trusting an embedded status field."""

    root = Path(artifact_dir)
    surfaces = {
        filename: _load_json_surface(root / filename)
        for filename in (
            CANONICAL_METADATA_FILENAME,
            CANONICAL_METRICS_FILENAME,
            CANONICAL_REPORT_FILENAME,
            PAPER_SESSION_METADATA_FILENAME,
        )
    }
    for filename, surface in surfaces.items():
        if surface.state == "present_invalid":
            return _unknown(f"canonical_surface_invalid:{filename}")

    metadata = (
        surfaces[CANONICAL_METADATA_FILENAME].payload
        or surfaces[PAPER_SESSION_METADATA_FILENAME].payload
    )
    metrics = surfaces[CANONICAL_METRICS_FILENAME].payload
    report = surfaces[CANONICAL_REPORT_FILENAME].payload

    identities = _collect_embedded_blocks(
        "artifact_identity", metadata, metrics, report
    )
    identity = (
        identities[0]
        if identities
        and _all_equal(identities)
        and isinstance(identities[0], dict)
        else {}
    )

    registry_path = (
        Path(overlay_path)
        if overlay_path is not None
        else root.parent / QUANTITATIVE_AUTHORITY_REGISTRY_FILENAME
    )
    registry_status, matching_entry = _resolve_registry(
        registry_path, identity
    )
    if registry_status == "invalid":
        return _unknown("authority_registry_invalid_or_ambiguous")
    if matching_entry is not None:
        return _resolution(
            AUTHORITY_SUPERSEDED,
            str(matching_entry.get("reason") or "explicitly_superseded"),
            contract=(
                _collect_embedded_blocks(
                    "quantitative_contract", metadata, metrics, report
                )
                or [None]
            )[0],
            identity=identity,
        )

    contracts = _collect_embedded_blocks(
        "quantitative_contract", metadata, metrics, report
    )
    canonical_metric_blocks = _collect_embedded_blocks(
        "canonical_metric_payload", metadata, metrics, report
    )
    if not contracts or not identities or not canonical_metric_blocks:
        return _unknown("quantitative_provenance_missing")
    if (
        not _all_equal(contracts)
        or not _all_equal(identities)
        or not _all_equal(canonical_metric_blocks)
    ):
        return _unknown("embedded_quantitative_provenance_mismatch")

    contract = contracts[0]
    identity = identities[0]
    canonical_metrics = canonical_metric_blocks[0]
    if not isinstance(identity, dict):
        return _unknown("artifact_identity_missing")
    if not isinstance(canonical_metrics, dict):
        return _unknown("canonical_metric_payload_missing")
    if not _metric_surfaces_match(
        canonical_metrics,
        metadata=metadata,
        metrics=metrics,
        report=report,
    ):
        return _unknown(
            "canonical_metric_payload_mismatch",
            contract=contract,
            identity=identity,
        )

    contract_errors = validate_quantitative_contract(contract)
    if contract_errors:
        return _unknown(contract_errors[0], contract=contract, identity=identity)
    annualization_error = _validate_annualization_metric_consistency(
        contract,
        canonical_metrics,
    )
    if annualization_error:
        return _unknown(
            annualization_error,
            contract=contract,
            identity=identity,
        )

    identity_error = _validate_artifact_identity(
        identity,
        root,
        metadata=metadata,
        report=report,
    )
    if identity_error:
        return _unknown(identity_error, contract=contract, identity=identity)

    if metrics:
        if build_canonical_metric_payload(metrics) != canonical_metrics:
            return _unknown(
                "canonical_metric_payload_mismatch",
                contract=contract,
                identity=identity,
            )
    elif report:
        if build_canonical_metric_payload(report) != canonical_metrics:
            return _unknown(
                "canonical_metric_payload_mismatch",
                contract=contract,
                identity=identity,
            )
    else:
        return _unknown(
            "canonical_metric_payload_missing",
            contract=contract,
            identity=identity,
        )
    identity_without_digest = {
        key: identity.get(key)
        for key in ("run_id", "relative_run_path", "source_git_commit")
    }
    expected_digest = compute_quantitative_evidence_digest(
        artifact_identity_without_digest=identity_without_digest,
        quantitative_contract=contract,
        canonical_metric_payload=canonical_metrics,
    )
    if identity.get("quantitative_evidence_digest") != expected_digest:
        return _unknown(
            "quantitative_evidence_digest_mismatch",
            contract=contract,
            identity=identity,
        )
    input_error = _validate_quantitative_input_manifest(
        root,
        canonical_metrics,
        required_inputs=required_inputs,
    )
    if input_error:
        return _unknown(
            input_error,
            contract=contract,
            identity=identity,
        )
    return _resolution(
        AUTHORITY_CURRENT,
        "recognized_contract_and_digest",
        contract=contract,
        identity=identity,
    )


def normalize_relative_run_path(value: str) -> str:
    """Normalize and validate a path relative to its canonical artifact root."""

    raw = str(value).strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or raw in {".", ".."}
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("relative_run_path must be a safe POSIX relative path")
    return path.as_posix()


def _allowed_applicability(
    artifact_type: str, policy_name: str
) -> set[str]:
    if policy_name == "oos_equity_stitching":
        return (
            {"applied"}
            if artifact_type == "walkforward"
            else {"not_applicable"}
        )
    if policy_name == "forward_resume_accounting":
        return (
            {"applied", "not_applicable"}
            if artifact_type == "forward"
            else {"not_applicable"}
        )
    if policy_name == "fee_and_slippage":
        return {"applied"}
    if policy_name == "annualization":
        return {"applied", "unavailable"}
    return set()


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key) not in _DIGEST_EXCLUDED_FIELDS
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _canonical_quantitative_input(
    path: Path,
) -> tuple[Any, str, int]:
    if not path.is_file():
        raise ValueError(f"Bound quantitative input is missing: {path.name}")
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Bound JSON input is invalid: {path.name}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(
                f"Bound JSON input must contain an object: {path.name}"
            )
        return _canonicalize(payload), "canonical_json_object_v1", 1
    if path.suffix == ".csv":
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            raise ValueError(
                f"Bound CSV input is invalid: {path.name}"
            ) from exc
        if not rows or not rows[0]:
            raise ValueError(f"Bound CSV input has no header: {path.name}")
        columns = rows[0]
        if (
            any(not column for column in columns)
            or len(columns) != len(set(columns))
            or any(len(row) != len(columns) for row in rows[1:])
        ):
            raise ValueError(
                f"Bound CSV input has an invalid tabular shape: {path.name}"
            )
        representation = {
            "columns": columns,
            "rows": rows[1:],
        }
        return representation, "canonical_csv_rows_v1", len(rows) - 1
    raise ValueError(f"Unsupported quantitative input format: {path.name}")


def _load_json_surface(path: Path) -> _JsonSurface:
    if not path.exists():
        if path.is_symlink():
            return _JsonSurface("present_invalid", {})
        return _JsonSurface("absent", {})
    if not path.is_file():
        return _JsonSurface("present_invalid", {})
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _JsonSurface("present_invalid", {})
    if not isinstance(payload, dict):
        return _JsonSurface("present_invalid", {})
    return _JsonSurface("present_valid", payload)


def _validate_annualization_metric_consistency(
    contract: Any,
    canonical_metrics: Mapping[str, Any],
) -> str | None:
    if not isinstance(contract, Mapping):
        return "quantitative_contract_missing"
    try:
        expected = derive_annualization_provenance(canonical_metrics)
    except ValueError:
        return "annualization_metric_evidence_invalid"
    policies = contract.get("policies")
    annualization = (
        policies.get("annualization")
        if isinstance(policies, Mapping)
        else None
    )
    if not isinstance(annualization, Mapping):
        return "policy_missing:annualization"
    if (
        annualization.get("applicability")
        != expected["annualization_applicability"]
        or annualization.get("reason") != expected["annualization_reason"]
    ):
        return "annualization_metric_contradiction"
    return None


def _validate_quantitative_input_manifest(
    root: Path,
    canonical_metrics: Mapping[str, Any],
    *,
    required_inputs: Iterable[str],
) -> str | None:
    required = sorted(set(str(name) for name in required_inputs))
    if any(name not in _BOUND_QUANTITATIVE_INPUTS for name in required):
        return "quantitative_input_requirement_unknown"

    manifest = canonical_metrics.get("bound_quantitative_inputs")
    if manifest is None:
        return (
            f"quantitative_input_unbound:{required[0]}"
            if required
            else None
        )
    if (
        not isinstance(manifest, Mapping)
        or set(manifest) != {"schema_version", "files"}
        or manifest.get("schema_version") != _BOUND_INPUT_SCHEMA_VERSION
        or not isinstance(manifest.get("files"), Mapping)
    ):
        return "quantitative_input_manifest_invalid"

    files = manifest["files"]
    if any(name not in files for name in required):
        missing = next(name for name in required if name not in files)
        return f"quantitative_input_unbound:{missing}"
    if any(
        not isinstance(name, str)
        or name not in _BOUND_QUANTITATIVE_INPUTS
        for name in files
    ):
        return "quantitative_input_manifest_invalid"

    for filename, expected in sorted(files.items()):
        if (
            not isinstance(expected, Mapping)
            or set(expected) != {"format", "record_count", "sha256"}
            or expected.get("format")
            not in {"canonical_json_object_v1", "canonical_csv_rows_v1"}
            or not isinstance(expected.get("record_count"), int)
            or not isinstance(expected.get("sha256"), str)
            or not re.fullmatch(
                r"[0-9a-f]{64}",
                expected["sha256"],
                re.IGNORECASE,
            )
        ):
            return f"quantitative_input_manifest_invalid:{filename}"
        try:
            actual = build_quantitative_input_manifest(root, [filename])[
                "files"
            ][filename]
        except ValueError:
            return f"quantitative_input_invalid:{filename}"
        if actual != expected:
            return f"quantitative_input_digest_mismatch:{filename}"
    return None


def _collect_embedded_blocks(
    field: str, *payloads: Mapping[str, Any]
) -> list[Any]:
    blocks: list[Any] = []
    for payload in payloads:
        if field in payload:
            blocks.append(payload[field])
        machine_contract = payload.get("machine_contract")
        if isinstance(machine_contract, dict) and field in machine_contract:
            blocks.append(machine_contract[field])
    return blocks


def _metric_surfaces_match(
    canonical_metrics: Mapping[str, Any],
    *,
    metadata: Mapping[str, Any],
    metrics: Mapping[str, Any],
    report: Mapping[str, Any],
) -> bool:
    for payload in (metadata, metrics):
        for field, expected in canonical_metrics.items():
            if field in payload and _canonicalize(payload[field]) != expected:
                return False

    expected_summary = canonical_metrics.get("summary")
    if expected_summary is not None:
        report_summary = report.get("summary")
        if isinstance(report_summary, dict):
            if _canonicalize(report_summary) != expected_summary:
                return False
        elif isinstance(report.get("kpi_summary"), dict):
            if _canonicalize(report["kpi_summary"]) != expected_summary:
                return False

    expected_best = canonical_metrics.get("best_result")
    if expected_best is not None:
        machine_contract = report.get("machine_contract")
        if (
            isinstance(machine_contract, dict)
            and "best_result" in machine_contract
        ):
            if _canonicalize(machine_contract["best_result"]) != expected_best:
                return False
        else:
            rows = report.get("results") or report.get("oos_leaderboard")
            if isinstance(rows, list) and rows:
                if _canonicalize(rows[0]) != expected_best:
                    return False
    return True


def _all_equal(values: list[Any]) -> bool:
    first = values[0]
    return all(value == first for value in values[1:])


def _validate_artifact_identity(
    identity: Mapping[str, Any],
    root: Path,
    *,
    metadata: Mapping[str, Any],
    report: Mapping[str, Any],
) -> str | None:
    try:
        relative_path = normalize_relative_run_path(
            str(identity.get("relative_run_path") or "")
        )
    except ValueError:
        return "artifact_relative_path_invalid"
    if relative_path != root.name:
        return "artifact_relative_path_mismatch"
    source_commit = str(identity.get("source_git_commit") or "")
    if not _COMMIT_RE.fullmatch(source_commit):
        return "artifact_source_git_commit_invalid"
    embedded_commits = [
        value
        for value in (
            metadata.get("git_commit"),
            report.get("header", {}).get("git_commit")
            if isinstance(report.get("header"), dict)
            else None,
        )
        if value not in (None, "")
    ]
    if any(str(value) != source_commit for value in embedded_commits):
        return "artifact_source_git_commit_mismatch"
    digest = identity.get("quantitative_evidence_digest")
    if not isinstance(digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", digest, re.IGNORECASE
    ):
        return "quantitative_evidence_digest_invalid"
    return None


def _resolve_registry(
    path: Path, identity: Mapping[str, Any]
) -> tuple[str, dict[str, Any] | None]:
    if not path.exists():
        return "absent", None
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "invalid", None
    if (
        not isinstance(registry, dict)
        or registry.get("schema_version")
        != QUANTITATIVE_AUTHORITY_REGISTRY_VERSION
        or not isinstance(registry.get("entries"), list)
    ):
        return "invalid", None

    seen_exact: set[str] = set()
    seen_location: dict[tuple[Any, Any, Any], str] = {}
    matches: list[dict[str, Any]] = []
    for entry in registry["entries"]:
        if not _valid_registry_entry(entry):
            return "invalid", None
        entry_identity = entry["artifact_identity"]
        exact_key = json.dumps(
            _canonicalize(entry_identity), sort_keys=True, separators=(",", ":")
        )
        if exact_key in seen_exact:
            return "invalid", None
        seen_exact.add(exact_key)

        location_key = (
            entry_identity.get("run_id"),
            entry_identity.get("relative_run_path"),
            entry_identity.get("source_git_commit"),
        )
        digest = entry_identity["quantitative_evidence_digest"]
        previous = seen_location.get(location_key)
        if previous is not None and previous != digest:
            return "invalid", None
        seen_location[location_key] = digest
        if entry_identity == identity:
            matches.append(entry)

    if len(matches) > 1:
        return "invalid", None
    return "valid", matches[0] if matches else None


def _valid_registry_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("status") != AUTHORITY_SUPERSEDED:
        return False
    reason = entry.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return False
    identity = entry.get("artifact_identity")
    if not isinstance(identity, dict):
        return False
    if set(identity) != {
        "run_id",
        "relative_run_path",
        "source_git_commit",
        "quantitative_evidence_digest",
    }:
        return False
    try:
        normalize_relative_run_path(str(identity["relative_run_path"]))
    except ValueError:
        return False
    if not _COMMIT_RE.fullmatch(str(identity["source_git_commit"])):
        return False
    return bool(
        re.fullmatch(
            r"[0-9a-f]{64}",
            str(identity["quantitative_evidence_digest"]),
            re.IGNORECASE,
        )
    )


def _resolution(
    status: str,
    reason: str,
    *,
    contract: Any = None,
    identity: Any = None,
) -> AuthorityResolution:
    eligible = status == AUTHORITY_CURRENT
    contract_version = (
        contract.get("version") if isinstance(contract, dict) else None
    )
    digest = (
        identity.get("quantitative_evidence_digest")
        if isinstance(identity, dict)
        else None
    )
    return AuthorityResolution(
        authority_status=status,
        authority_reason=reason,
        quantitative_contract_version=contract_version,
        quantitative_evidence_digest=digest,
        visible=True,
        ranking_eligible=eligible,
        comparison_eligible=eligible,
        forward_eligible=eligible,
        promotion_eligible=eligible,
    )


def _unknown(
    reason: str,
    *,
    contract: Any = None,
    identity: Any = None,
) -> AuthorityResolution:
    return _resolution(
        AUTHORITY_UNKNOWN,
        reason,
        contract=contract,
        identity=identity,
    )
