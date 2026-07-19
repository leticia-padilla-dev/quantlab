from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "hardening" / "gates.yaml"
LOCK_INPUTS = (
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "desktop" / "package-lock.json",
)


def _run(command: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _git_output(*args: str) -> str:
    result = _run(["git", *args], timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result.stdout.strip()


def _load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("gates"), dict):
        raise ValueError("hardening/gates.yaml must contain a 'gates' mapping")
    return manifest


def _dependency_lock_digest() -> str:
    digest = hashlib.sha256()
    found = False
    for path in LOCK_INPUTS:
        if not path.exists():
            continue
        found = True
        digest.update(path.relative_to(REPO_ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest() if found else "unavailable"


def _ensure_clean_tree(*, allow_dirty: bool) -> None:
    if allow_dirty or os.environ.get("CI"):
        return
    status = _git_output("status", "--porcelain")
    if status:
        raise RuntimeError(
            "working tree is not clean; commit or discard changes, use --allow-dirty for an explicit local exception, or run in CI"
        )


def _evidence_path(manifest: dict[str, Any], gate_id: str, gate: dict[str, Any], commit: str) -> Path:
    root = REPO_ROOT / str(manifest.get("evidence_root", "outputs/hardening"))
    configured = gate.get("evidence_file")
    if configured:
        return root / commit / str(configured)
    return root / commit / gate_id.replace(".", "/") / "result.json"


def _write_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute one QuantLab v0.1-hardening gate and write commit-bound JSON evidence."
    )
    parser.add_argument("gate_id", nargs="?", help="Gate identifier from hardening/gates.yaml")
    parser.add_argument("--list", action="store_true", help="List available gate identifiers")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved command without executing it")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow execution with a dirty working tree. Evidence still records the evaluated commit.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    manifest = _load_manifest()
    gates: dict[str, Any] = manifest["gates"]

    if args.list:
        for gate_id in sorted(gates):
            print(gate_id)
        return 0

    if not args.gate_id:
        print("ERROR: gate_id is required unless --list is used", file=sys.stderr)
        return 2
    if args.gate_id not in gates:
        print(f"ERROR: unknown hardening gate: {args.gate_id}", file=sys.stderr)
        return 2

    gate = gates[args.gate_id]
    if not isinstance(gate, dict):
        print(f"ERROR: invalid gate definition for {args.gate_id}", file=sys.stderr)
        return 2

    command = gate.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        print(f"ERROR: gate {args.gate_id} must define command as a non-empty string list", file=sys.stderr)
        return 2

    expected_exit_code = int(gate.get("expected_exit_code", 0))
    timeout_seconds = int(gate.get("timeout_seconds", 1800))
    commit = _git_output("rev-parse", "HEAD")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "gate_id": args.gate_id,
                    "commit": commit,
                    "command": command,
                    "expected_exit_code": expected_exit_code,
                    "timeout_seconds": timeout_seconds,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    _ensure_clean_tree(allow_dirty=args.allow_dirty)
    started_at = datetime.now(timezone.utc)

    try:
        result = _run(command, timeout=timeout_seconds)
        timed_out = False
        actual_exit_code: int | None = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        actual_exit_code = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

    finished_at = datetime.now(timezone.utc)
    passed = not timed_out and actual_exit_code == expected_exit_code
    evidence_path = _evidence_path(manifest, args.gate_id, gate, commit)
    payload = {
        "schema_version": manifest.get("schema_version", "1.0"),
        "gate_id": args.gate_id,
        "wave": gate.get("wave"),
        "description": gate.get("description"),
        "commit": commit,
        "verified_at": finished_at.isoformat(),
        "verified_by": os.environ.get("GITHUB_ACTOR") or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "platform": platform.platform(),
        "python": sys.version,
        "dependency_lock_digest": _dependency_lock_digest(),
        "command": command,
        "expected_exit_code": expected_exit_code,
        "actual_exit_code": actual_exit_code,
        "timed_out": timed_out,
        "duration_seconds": (finished_at - started_at).total_seconds(),
        "acceptance": gate.get("acceptance", []),
        "result": "passed" if passed else "failed",
        "stdout": stdout,
        "stderr": stderr,
    }
    _write_evidence(evidence_path, payload)

    print(json.dumps({"gate_id": args.gate_id, "result": payload["result"], "evidence": str(evidence_path)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
