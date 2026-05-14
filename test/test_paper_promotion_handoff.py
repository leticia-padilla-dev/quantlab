from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from quantlab.cli.paper_sessions import handle_paper_session_commands
from quantlab.reporting.paper_promotion_handoff import (
    PAPER_PROMOTION_HANDOFF_FILENAME,
    PAPER_PROMOTION_HANDOFF_VALIDATION_FILENAME,
)
from quantlab.runs.artifacts import (
    CANONICAL_REPORT_FILENAME,
    PAPER_SESSION_METADATA_FILENAME,
    PAPER_SESSION_STATUS_FILENAME,
)


def _write_json(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _write_trades_csv(path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "side", "price", "qty"])


def test_paper_promotion_handoff_command_writes_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "paper_sessions"
    session_dir = root / "sess_ok"
    session_dir.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 1, 1, 12, 0, 0).replace(microsecond=0).isoformat()

    _write_json(
        session_dir / PAPER_SESSION_METADATA_FILENAME,
        {"session_id": "sess_ok", "created_at": now, "command": "paper", "mode": "paper"},
    )
    _write_json(
        session_dir / PAPER_SESSION_STATUS_FILENAME,
        {"session_id": "sess_ok", "status": "success", "terminal": True, "updated_at": now, "status_reason": "completed"},
    )
    _write_json(
        session_dir / CANONICAL_REPORT_FILENAME,
        {
            "header": {"run_id": "sess_ok", "mode": "paper"},
            "machine_contract": {"contract_type": "quantlab.paper.result"},
            "status": "success",
        },
    )
    _write_trades_csv(session_dir / "trades.csv")

    args = SimpleNamespace(
        paper_promotion_handoff=str(session_dir),
        paper_promotion_handoff_outdir=str(session_dir),
    )
    assert handle_paper_session_commands(args) is True

    handoff_path = session_dir / PAPER_PROMOTION_HANDOFF_FILENAME
    validation_path = session_dir / PAPER_PROMOTION_HANDOFF_VALIDATION_FILENAME
    assert handoff_path.exists()
    assert validation_path.exists()

    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert handoff["artifact_type"] == "quantlab.paper.promotion_handoff"
    assert handoff["handoff_readiness"]["handoff_allowed"] is True

    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert validation["artifact_type"] == "quantlab.paper.promotion_handoff_validation"
    assert validation["accepted"] is True
