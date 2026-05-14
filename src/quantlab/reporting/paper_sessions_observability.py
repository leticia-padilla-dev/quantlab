from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PAPER_SESSIONS_HEALTH_JSON_FILENAME = "paper_sessions_health.json"
PAPER_SESSIONS_ALERTS_JSON_FILENAME = "paper_sessions_alerts.json"


def write_paper_sessions_health(root_dir: str | Path, payload: dict[str, Any]) -> str:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / PAPER_SESSIONS_HEALTH_JSON_FILENAME
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
    return str(path)


def write_paper_sessions_alerts(root_dir: str | Path, payload: dict[str, Any]) -> str:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / PAPER_SESSIONS_ALERTS_JSON_FILENAME
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
    return str(path)
