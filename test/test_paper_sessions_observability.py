from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from quantlab.cli.paper_sessions import handle_paper_session_commands
from quantlab.reporting.paper_sessions_observability import (
    PAPER_SESSIONS_ALERTS_JSON_FILENAME,
    PAPER_SESSIONS_HEALTH_JSON_FILENAME,
)
from quantlab.runs.artifacts import (
    CANONICAL_REPORT_FILENAME,
    PAPER_SESSION_METADATA_FILENAME,
    PAPER_SESSION_STATUS_FILENAME,
)


def _write_json(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _make_session(
    root: Path,
    *,
    session_id: str,
    status: str,
    terminal: bool,
    updated_at: datetime,
) -> Path:
    session_dir = root / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        session_dir / PAPER_SESSION_METADATA_FILENAME,
        {
            "session_id": session_id,
            "created_at": updated_at.replace(microsecond=0).isoformat(),
            "status": status,
            "command": "paper",
            "mode": "paper",
        },
    )
    _write_json(
        session_dir / PAPER_SESSION_STATUS_FILENAME,
        {
            "session_id": session_id,
            "status": status,
            "terminal": terminal,
            "updated_at": updated_at.replace(microsecond=0).isoformat(),
            "status_reason": "completed" if status == "success" else "active",
            "message": None,
        },
    )
    _write_json(
        session_dir / CANONICAL_REPORT_FILENAME,
        {
            "header": {"run_id": session_id, "mode": "paper"},
            "machine_contract": {"contract_type": "quantlab.paper.result"},
            "status": status,
        },
    )
    return session_dir


def test_paper_sessions_health_command_persists_health_artifact(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    root.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 1, 1, 12, 0, 0)

    _make_session(root, session_id="sess_success", status="success", terminal=True, updated_at=now)
    _make_session(root, session_id="sess_failed", status="failed", terminal=True, updated_at=now)

    args = SimpleNamespace(paper_sessions_health=str(root))
    assert handle_paper_session_commands(args) is True

    artifact_path = root / PAPER_SESSIONS_HEALTH_JSON_FILENAME
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.paper.sessions.health"
    assert payload["root_dir"].endswith("paper_sessions")
    assert payload["total_sessions"] == 2


def test_paper_sessions_alerts_command_persists_alerts_artifact(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    root.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 1, 1, 12, 0, 0)

    _make_session(root, session_id="sess_failed", status="failed", terminal=True, updated_at=now)
    _make_session(
        root,
        session_id="sess_running_stale",
        status="running",
        terminal=False,
        updated_at=now - timedelta(minutes=120),
    )

    args = SimpleNamespace(paper_sessions_alerts=str(root), paper_stale_minutes=60)
    assert handle_paper_session_commands(args) is True

    artifact_path = root / PAPER_SESSIONS_ALERTS_JSON_FILENAME
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "quantlab.paper.sessions.alerts"
    assert payload["alert_status"] in {"warning", "critical"}
