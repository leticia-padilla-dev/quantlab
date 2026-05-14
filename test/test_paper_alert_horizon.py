from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from quantlab.cli.paper_sessions import build_paper_sessions_alerts
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
) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    updated_at_iso = updated_at.replace(microsecond=0).isoformat()
    _write_json(
        session_dir / PAPER_SESSION_METADATA_FILENAME,
        {
            "session_id": session_id,
            "run_id": session_id,
            "created_at": updated_at_iso,
            "command": "paper",
            "mode": "paper",
            "status": status,
            "request_id": None,
        },
    )
    _write_json(
        session_dir / PAPER_SESSION_STATUS_FILENAME,
        {
            "session_id": session_id,
            "status": status,
            "terminal": terminal,
            "updated_at": updated_at_iso,
            "started_at": updated_at_iso,
            "finished_at": updated_at_iso if terminal else None,
            "status_reason": "completed" if status == "success" else "exception",
            "error_type": "DataError" if status == "failed" else None,
            "message": "error" if status == "failed" else None,
            "duration_seconds": 0.0,
            "command": "paper",
            "mode": "paper",
            "request_id": None,
        },
    )

    if status == "success":
        _write_json(
            session_dir / CANONICAL_REPORT_FILENAME,
            {
                "header": {"run_id": session_id, "mode": "paper"},
                "machine_contract": {"contract_type": "quantlab.paper.result"},
                "status": "success",
            },
        )


def test_alert_horizon_filters_current_window_by_days_and_sessions(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    root.mkdir(parents=True, exist_ok=True)

    now = datetime(2026, 1, 8, 12, 0, 0)

    _make_session(
        root,
        session_id="old_fail",
        status="failed",
        terminal=True,
        updated_at=datetime(2025, 12, 20, 12, 0, 0),
    )
    _make_session(
        root,
        session_id="cutoff_fail",
        status="failed",
        terminal=True,
        updated_at=datetime(2026, 1, 1, 12, 5, 0),
    )
    _make_session(
        root,
        session_id="recent_fail",
        status="failed",
        terminal=True,
        updated_at=datetime(2026, 1, 8, 11, 0, 0),
    )

    for i in range(1, 20):
        _make_session(
            root,
            session_id=f"success_{i:02d}",
            status="success",
            terminal=True,
            updated_at=now - timedelta(minutes=i),
        )

    alerts = build_paper_sessions_alerts(
        root,
        stale_after_minutes=60,
        window_days=7,
        window_sessions=20,
        now=now,
    )

    assert alerts["alert_status"] == "critical"
    assert alerts["alert_counts"]["critical"] == 3
    assert len(alerts["alerts"]) == 3

    assert alerts["horizon"]["mode"] == "and"
    assert alerts["horizon"]["window_days"] == 7
    assert alerts["horizon"]["window_sessions"] == 20

    assert alerts["current_window_alert_status"] == "critical"
    assert alerts["current_window_alert_counts"]["critical"] == 1
    assert len(alerts["current_window_alerts"]) == 1
    assert alerts["current_window_latest_alert_session_id"] == "recent_fail"
