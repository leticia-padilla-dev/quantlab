from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from quantlab.cli.paper_sessions import build_paper_sessions_alerts
from quantlab.runs.artifacts import (
    PAPER_SESSION_METADATA_FILENAME,
    PAPER_SESSION_STATUS_FILENAME,
)


def _write_json(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _make_minimal_session(
    root: Path,
    *,
    session_id: str,
    status: str,
    terminal: bool,
    updated_at: str | None,
) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        session_dir / PAPER_SESSION_METADATA_FILENAME,
        {
            "session_id": session_id,
            "run_id": session_id,
            "created_at": updated_at,
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
            "updated_at": updated_at,
            "started_at": updated_at,
            "finished_at": updated_at if terminal else None,
            "status_reason": "completed" if status == "success" else "exception",
            "error_type": "DataError" if status == "failed" else None,
            "message": "error" if status == "failed" else None,
            "duration_seconds": 0.0,
            "command": "paper",
            "mode": "paper",
            "request_id": None,
        },
    )


def test_alert_horizon_empty_root_is_ok(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    root.mkdir(parents=True, exist_ok=True)

    now = datetime(2026, 1, 8, 12, 0, 0)
    alerts = build_paper_sessions_alerts(
        root,
        stale_after_minutes=60,
        window_days=7,
        window_sessions=20,
        now=now,
    )

    assert alerts["total_sessions"] == 0
    assert alerts["alert_status"] == "ok"
    assert alerts["alerts"] == []
    assert alerts["current_window_total_sessions"] == 0
    assert alerts["current_window_alert_status"] == "ok"
    assert alerts["current_window_alerts"] == []


def test_alert_horizon_excludes_sessions_with_missing_activity_from_current_window(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    root.mkdir(parents=True, exist_ok=True)

    now = datetime(2026, 1, 8, 12, 0, 0)

    _make_minimal_session(
        root,
        session_id="missing_activity_fail",
        status="failed",
        terminal=True,
        updated_at=None,
    )
    _make_minimal_session(
        root,
        session_id="recent_fail",
        status="failed",
        terminal=True,
        updated_at="2026-01-08T11:00:00",
    )

    alerts = build_paper_sessions_alerts(
        root,
        stale_after_minutes=60,
        window_days=7,
        window_sessions=20,
        now=now,
    )

    assert alerts["alert_status"] == "critical"
    assert alerts["alert_counts"]["critical"] == 2

    assert alerts["current_window_alert_status"] == "critical"
    assert alerts["current_window_alert_counts"]["critical"] == 1
    assert len(alerts["current_window_alerts"]) == 1
    assert alerts["current_window_latest_alert_session_id"] == "recent_fail"


def test_alert_horizon_window_sessions_limits_current_window(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    root.mkdir(parents=True, exist_ok=True)

    now = datetime(2026, 1, 8, 12, 0, 0)

    _make_minimal_session(
        root,
        session_id="older_fail",
        status="failed",
        terminal=True,
        updated_at="2026-01-08T10:00:00",
    )
    _make_minimal_session(
        root,
        session_id="newest_fail",
        status="failed",
        terminal=True,
        updated_at="2026-01-08T11:00:00",
    )

    alerts = build_paper_sessions_alerts(
        root,
        stale_after_minutes=60,
        window_days=7,
        window_sessions=1,
        now=now,
    )

    assert alerts["alert_status"] == "critical"
    assert alerts["alert_counts"]["critical"] == 2

    assert alerts["current_window_total_sessions"] == 1
    assert alerts["current_window_alert_status"] == "critical"
    assert alerts["current_window_alert_counts"]["critical"] == 1
    assert len(alerts["current_window_alerts"]) == 1
    assert alerts["current_window_latest_alert_session_id"] == "newest_fail"
