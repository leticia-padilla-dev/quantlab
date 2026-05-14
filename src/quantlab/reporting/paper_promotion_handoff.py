from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from quantlab.errors import ConfigError
from quantlab.runs.artifacts import canonical_paper_artifact_names

PAPER_PROMOTION_HANDOFF_CONTRACT_TYPE = "quantlab.paper.promotion_handoff"
PAPER_PROMOTION_HANDOFF_CONTRACT_VERSION = "1.0"

PAPER_PROMOTION_HANDOFF_FILENAME = "paper_promotion_handoff.json"
PAPER_PROMOTION_HANDOFF_VALIDATION_FILENAME = "paper_promotion_handoff_validation.json"


def build_paper_promotion_handoff(session_dir: str | Path, *, generated_at: datetime | None = None) -> dict[str, Any]:
    from quantlab.cli.paper_sessions import load_paper_session_summary

    root = Path(session_dir)
    if not root.is_dir():
        raise ConfigError(f"Paper session directory does not exist or is not a directory: {root}")

    summary = load_paper_session_summary(root)
    names = canonical_paper_artifact_names()
    paths = {
        "session_metadata_json": str(root / names["metadata"]),
        "session_status_json": str(root / names["status"]),
        "report_json": str(root / names["report"]),
        "trades_csv": str(root / names["trades"]),
    }
    presence = {key: Path(value).exists() for key, value in paths.items()}

    required_missing = [key for key, present in presence.items() if not present]
    blockers = []
    reasons = []
    if required_missing:
        blockers.append("artifact_pack_incomplete")
        reasons.extend(f"missing_{key}" for key in required_missing)

    status = (summary.get("status") or "unknown").lower()
    terminal = bool(summary.get("terminal", False))
    report_contract = summary.get("report_contract_type")

    if not terminal:
        blockers.append("non_terminal_session")
    if status != "success":
        blockers.append("status_not_success")
    if report_contract != "quantlab.paper.result":
        blockers.append("report_contract_not_paper_result")

    handoff_allowed = not blockers

    created_at = (generated_at or datetime.now()).replace(microsecond=0).isoformat()
    return {
        "artifact_type": PAPER_PROMOTION_HANDOFF_CONTRACT_TYPE,
        "artifact_version": PAPER_PROMOTION_HANDOFF_CONTRACT_VERSION,
        "generated_at": created_at,
        "source": {
            "session_id": summary.get("session_id") or root.name,
            "session_dir": str(root),
        },
        "constraints": {
            "submit_allowed": False,
            "stage_e": "blocked",
            "execution_authority": "none",
        },
        "canonical_summary": {
            "status": summary.get("status"),
            "terminal": summary.get("terminal"),
            "status_reason": summary.get("status_reason"),
            "request_id": summary.get("request_id"),
            "report_contract_type": report_contract,
        },
        "artifact_paths": paths,
        "artifact_presence": presence,
        "handoff_readiness": {
            "handoff_allowed": handoff_allowed,
            "blockers": blockers,
            "reasons": reasons,
        },
    }


def write_paper_promotion_handoff(payload: dict[str, Any], *, outdir: str | Path) -> str:
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / PAPER_PROMOTION_HANDOFF_FILENAME
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
    return str(path)


def load_paper_promotion_handoff(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    if not artifact_path.exists() or not artifact_path.is_file():
        raise ConfigError(f"Paper promotion handoff artifact does not exist or is not a file: {artifact_path}")
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Paper promotion handoff artifact is not valid JSON: {artifact_path}") from exc
    if not isinstance(payload, dict):
        raise ConfigError("Paper promotion handoff artifact root must be a JSON object.")
    return payload


def build_paper_promotion_handoff_validation(
    payload: dict[str, Any],
    *,
    source_artifact_path: str | Path,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    created_at = (generated_at or datetime.now()).replace(microsecond=0).isoformat()
    source_artifact = str(Path(source_artifact_path))
    reasons: list[str] = []

    contract_type = payload.get("artifact_type")
    contract_version = payload.get("artifact_version")
    if contract_type != PAPER_PROMOTION_HANDOFF_CONTRACT_TYPE:
        reasons.append("handoff_contract_type_invalid")
    if contract_version != PAPER_PROMOTION_HANDOFF_CONTRACT_VERSION:
        reasons.append("handoff_contract_version_invalid")

    source = payload.get("source")
    if not isinstance(source, dict):
        source = {}
        reasons.append("source_block_missing")

    session_dir = source.get("session_dir")
    if not isinstance(session_dir, str) or not session_dir.strip():
        reasons.append("source_session_dir_missing")
        session_dir_path = None
    else:
        session_dir_path = Path(session_dir)
        if not session_dir_path.is_dir():
            reasons.append("source_session_dir_invalid")

    presence = payload.get("artifact_presence")
    if not isinstance(presence, dict):
        presence = {}
        reasons.append("artifact_presence_missing")

    required_keys = ("session_metadata_json", "session_status_json", "report_json", "trades_csv")
    for key in required_keys:
        if key not in presence:
            reasons.append(f"missing_presence_key:{key}")
        elif not bool(presence.get(key)):
            reasons.append(f"required_artifact_missing:{key}")

    accepted = not reasons
    return {
        "artifact_type": "quantlab.paper.promotion_handoff_validation",
        "artifact_version": "1.0",
        "generated_at": created_at,
        "source_artifact_path": source_artifact,
        "accepted": accepted,
        "reasons": reasons,
        "source": {
            "session_id": source.get("session_id"),
            "session_dir": session_dir,
        },
        "constraints": payload.get("constraints"),
        "handoff_readiness": payload.get("handoff_readiness"),
    }


def write_paper_promotion_handoff_validation(payload: dict[str, Any], *, outdir: str | Path) -> str:
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / PAPER_PROMOTION_HANDOFF_VALIDATION_FILENAME
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
    return str(path)
