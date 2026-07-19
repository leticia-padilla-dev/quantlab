from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterator

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "hardening" / "gates.yaml"
NODE_LOCK_PATH = REPO_ROOT / "desktop" / "package-lock.json"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
MAX_LOG_BYTES = 32 * 1024
MAX_INVENTORY_BYTES = 4 * 1024 * 1024
MAX_COMMAND_ARG_CHARS = 2048
READ_CHUNK_BYTES = 8192
CAPTURE_JOIN_TIMEOUT_SECONDS = 1.0
CANONICAL_EVIDENCE_ROOT = Path("outputs/hardening")
FORBIDDEN_GATE_STATE_FIELDS = frozenset({"authoritative", "passed", "result", "status"})
PASSTHROUGH_ENVIRONMENT_NAMES = frozenset(
    {
        "CI",
        "GITHUB_ACTIONS",
        "GITHUB_ACTOR",
        "GITHUB_REF",
        "GITHUB_SHA",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "RUNNER_ARCH",
        "RUNNER_OS",
        "SYSTEMROOT",
        "TZ",
        "WINDIR",
    }
)
RECORDED_ENVIRONMENT_NAMES = ("CI", "GITHUB_ACTIONS", "LANG", "LC_ALL", "TZ")


def _resolve_git_executable() -> Path:
    candidates = [Path("/usr/bin/git")] if os.name == "posix" else []
    discovered = shutil.which("git")
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return resolved
    raise RuntimeError("a trusted Git executable is required")


GIT_EXECUTABLE = _resolve_git_executable()

_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY(?: BLOCK)?-----.*?"
    r"(?:-----END(?: [A-Z0-9]+)* PRIVATE KEY(?: BLOCK)?-----|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_AUTHORIZATION_VALUE = re.compile(
    r"(?P<prefix>\b(?:authorization|proxy-authorization)\s*:\s*(?:bearer|basic)\s+)[^\s,;]+",
    re.IGNORECASE,
)
_BEARER_VALUE = re.compile(r"(?P<prefix>\bbearer\s+)[^\s,;]+", re.IGNORECASE)
_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?P<prefix>"
    r"(?<![A-Z0-9_.-])[\"']?"
    r"(?:[A-Z0-9_.-]{0,48}(?:token|secret|password|passwd|api[_-]?key|private[_-]?key)"
    r"[A-Z0-9_.-]{0,48}|cookie|set-cookie)"
    r"[\"']?\s*[:=]\s*)"
    r"(?P<value>\"[^\"\n]*\"|'[^'\n]*'|[^\s,;\n]+)",
    re.IGNORECASE,
)
_URL_CREDENTIALS = re.compile(
    r"(?P<scheme>[a-z][a-z0-9+.-]*://)[^/@\s:]+:[^/@\s]+@",
    re.IGNORECASE,
)
_GITHUB_TOKEN = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
_GITHUB_FINE_GRAINED_TOKEN = re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")
_NPM_TOKEN = re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b")
_JWT_TOKEN = re.compile(
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
)
_HEX_PRIVATE_KEY = re.compile(r"\b0x[0-9a-fA-F]{64}\b")
_SENSITIVE_FLAG = re.compile(
    r"^--?[A-Z0-9_.-]*(?:token|secret|password|passwd|api[-_]?key|private[-_]?key|authorization|cookie)$",
    re.IGNORECASE,
)
_SENSITIVE_ENVIRONMENT_NAME = re.compile(
    r"(?:^|_)(?:AUTH(?:ORIZATION)?|COOKIE|CREDENTIALS?|PASS(?:WORD|WD)?|SECRET|TOKEN|"
    r"API_?KEY|PRIVATE_?KEY)(?:_|$)",
    re.IGNORECASE,
)


@dataclass
class _BoundedCapture:
    data: bytearray = field(default_factory=bytearray)
    total_bytes: int = 0
    limit: int = MAX_LOG_BYTES
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def append(self, chunk: bytes) -> None:
        with self.lock:
            self.total_bytes += len(chunk)
            remaining = self.limit - len(self.data)
            if remaining > 0:
                self.data.extend(chunk[:remaining])

    def snapshot(self) -> tuple[bytes, int]:
        with self.lock:
            return bytes(self.data), self.total_bytes


@dataclass(frozen=True)
class GateCommandResult:
    actual_exit_code: int | None
    timed_out: bool
    launch_error: str | None
    capture_incomplete: bool
    capture_errors: dict[str, str | None]
    stdout: _BoundedCapture
    stderr: _BoundedCapture


@dataclass
class _DrainState:
    error: str | None = None


def _minimal_executable_path() -> str:
    directories: list[str] = []
    for candidate in (
        str(Path(sys.executable).resolve().parent),
        str(GIT_EXECUTABLE.parent),
        *(os.defpath.split(os.pathsep)),
    ):
        if candidate and candidate not in directories:
            directories.append(candidate)
    for executable_name in ("node", "npm"):
        discovered = shutil.which(executable_name, path=os.environ.get("PATH"))
        if discovered:
            parent = str(Path(discovered).parent)
            if parent not in directories:
                directories.append(parent)
    return os.pathsep.join(directories)


def _execution_environment(
    runtime_root: Path, *, workspace_root: Path | None = None
) -> tuple[dict[str, str], dict[str, Any]]:
    home = runtime_root / "home"
    temporary = runtime_root / "tmp"
    pycache = runtime_root / "pycache"
    for directory in (home, temporary, pycache):
        directory.mkdir(parents=True, exist_ok=True)
    npm_config = home / ".npmrc"
    npm_global_config = home / ".npmrc-global"
    git_config = home / ".gitconfig"
    npm_config.touch(exist_ok=True)
    npm_global_config.touch(exist_ok=True)
    git_config.touch(exist_ok=True)

    environment = {
        name: value
        for name, value in os.environ.items()
        if name in PASSTHROUGH_ENVIRONMENT_NAMES
        and _SENSITIVE_ENVIRONMENT_NAME.search(name) is None
    }
    environment.update(
        {
            "PATH": _minimal_executable_path(),
            "HOME": str(home),
            "XDG_CACHE_HOME": str(runtime_root / "xdg-cache"),
            "XDG_CONFIG_HOME": str(runtime_root / "xdg-config"),
            "TMPDIR": str(temporary),
            "TMP": str(temporary),
            "TEMP": str(temporary),
            "GIT_CONFIG_GLOBAL": str(git_config),
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "NPM_CONFIG_USERCONFIG": str(npm_config),
            "NPM_CONFIG_GLOBALCONFIG": str(npm_global_config),
            "PYTHONNOUSERSITE": "1",
            "PYTHONPYCACHEPREFIX": str(pycache),
            "PYTHONSAFEPATH": "1",
            "PYTHONHASHSEED": "0",
            "PYTHON_DOTENV_DISABLED": "1",
        }
    )
    if workspace_root is not None:
        environment["PYTHONPATH"] = str(workspace_root / "src")

    removed_names = sorted(set(os.environ).difference(environment))
    recorded_values = {
        name: environment[name]
        for name in RECORDED_ENVIRONMENT_NAMES
        if name in environment
    }
    identity = {
        "policy": "allowlist-v1",
        "effective_variable_names": sorted(environment),
        "effective_environment_sha256": _canonical_sha256(environment),
        "effective_variable_count": len(environment),
        "removed_variable_names": removed_names,
        "removed_variable_count": len(removed_names),
        "recorded_values": recorded_values,
        "path_sha256": hashlib.sha256(
            environment.get("PATH", "").encode("utf-8", errors="surrogateescape")
        ).hexdigest(),
    }
    return environment, identity


def _run_small(
    command: list[str],
    *,
    timeout: float = 30,
    environment: dict[str, str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=environment,
    )


def _git_command(*args: str) -> list[str]:
    return [
        str(GIT_EXECUTABLE),
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.excludesFile=/dev/null",
        *args,
    ]


def _git_output(*args: str, environment: dict[str, str], repo_root: Path) -> str:
    result = _run_small(
        _git_command(*args),
        timeout=30,
        environment=environment,
        cwd=repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "git command failed"
        )
    return result.stdout.strip()


def _workspace_content_identity(
    repo_root: Path, environment: dict[str, str]
) -> tuple[str, int]:
    listed = subprocess.run(
        _git_command("ls-files", "-z", "--cached", "--others", "--exclude-standard"),
        cwd=repo_root,
        capture_output=True,
        timeout=30,
        check=False,
        env=environment,
    )
    if listed.returncode != 0:
        raise RuntimeError(
            listed.stderr.decode("utf-8", errors="replace").strip()
            or "git ls-files failed"
        )

    relative_paths = sorted(item for item in listed.stdout.split(b"\0") if item)
    digest = hashlib.sha256()
    for raw_path in relative_paths:
        relative_path = Path(os.fsdecode(raw_path))
        candidate = repo_root / relative_path
        digest.update(len(raw_path).to_bytes(8, "big"))
        digest.update(raw_path)
        try:
            metadata_result = candidate.lstat()
        except FileNotFoundError:
            digest.update(b"missing")
            continue
        digest.update(str(metadata_result.st_mode).encode("ascii"))
        if candidate.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.fsencode(os.readlink(candidate)))
        elif candidate.is_file():
            digest.update(b"file\0")
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(READ_CHUNK_BYTES), b""):
                    digest.update(chunk)
        elif candidate.is_dir():
            # A directory entry can represent a tracked submodule. Its worktree state is
            # still checked by git status; this marker keeps the identity deterministic.
            digest.update(b"directory")
        else:
            digest.update(b"other")
    return digest.hexdigest(), len(relative_paths)


def _tracked_checkout_integrity(
    repo_root: Path, environment: dict[str, str]
) -> dict[str, Any]:
    object_format = _git_output(
        "rev-parse",
        "--show-object-format",
        environment=environment,
        repo_root=repo_root,
    )
    if object_format not in hashlib.algorithms_available:
        raise RuntimeError(f"unsupported Git object format: {object_format}")
    staged = subprocess.run(
        _git_command("ls-files", "--stage", "-z"),
        cwd=repo_root,
        capture_output=True,
        timeout=30,
        check=False,
        env=environment,
    )
    if staged.returncode != 0:
        raise RuntimeError(
            staged.stderr.decode("utf-8", errors="replace").strip()
            or "git ls-files --stage failed"
        )

    mismatch_records: list[bytes] = []
    tracked_records = [item for item in staged.stdout.split(b"\0") if item]
    for record in tracked_records:
        try:
            metadata_bytes, raw_path = record.split(b"\t", 1)
            mode, expected_oid, stage = metadata_bytes.split(b" ", 2)
        except ValueError as exc:
            raise RuntimeError("unexpected git ls-files --stage output") from exc
        candidate = repo_root / Path(os.fsdecode(raw_path))
        if stage != b"0":
            mismatch_records.append(raw_path + b":unmerged")
            continue
        try:
            file_metadata = candidate.lstat()
        except FileNotFoundError:
            mismatch_records.append(raw_path + b":missing")
            continue

        if candidate.is_symlink():
            content = os.fsencode(os.readlink(candidate))
            actual_mode = b"120000"
            digest = hashlib.new(object_format)
            digest.update(f"blob {len(content)}\0".encode("ascii"))
            digest.update(content)
            actual_oid = digest.hexdigest().encode("ascii")
        elif candidate.is_file():
            actual_mode = b"100755" if file_metadata.st_mode & 0o111 else b"100644"
            digest = hashlib.new(object_format)
            digest.update(f"blob {file_metadata.st_size}\0".encode("ascii"))
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(READ_CHUNK_BYTES), b""):
                    digest.update(chunk)
            actual_oid = digest.hexdigest().encode("ascii")
        elif candidate.is_dir() and mode == b"160000":
            actual_mode = b"160000"
            actual_oid = _git_output(
                "rev-parse",
                "HEAD",
                environment=environment,
                repo_root=candidate,
            ).encode("ascii")
        else:
            mismatch_records.append(raw_path + b":unsupported-type")
            continue

        if actual_mode != mode or actual_oid != expected_oid:
            mismatch_records.append(raw_path + b":content-or-mode")

    return {
        "matches_index": not mismatch_records,
        "tracked_file_count": len(tracked_records),
        "mismatch_count": len(mismatch_records),
        "mismatch_sha256": hashlib.sha256(b"\0".join(mismatch_records)).hexdigest(),
        "index_sha256": hashlib.sha256(staged.stdout).hexdigest(),
        "object_format": object_format,
    }


def _git_snapshot(repo_root: Path, environment: dict[str, str]) -> dict[str, Any]:
    status = _run_small(
        _git_command("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        timeout=30,
        environment=environment,
        cwd=repo_root,
    )
    if status.returncode != 0:
        raise RuntimeError(status.stderr.strip() or "git status failed")
    porcelain = status.stdout
    records = [item for item in porcelain.split("\0") if item]
    dependency_mount_record = "?? desktop/node_modules"
    if dependency_mount_record in records:
        mount = repo_root / "desktop" / "node_modules"
        if mount.is_symlink() and mount.resolve().is_dir():
            records.remove(dependency_mount_record)

    index = _run_small(
        _git_command("ls-files", "-v", "-z"),
        timeout=30,
        environment=environment,
        cwd=repo_root,
    )
    if index.returncode != 0:
        raise RuntimeError(index.stderr.strip() or "git ls-files -v failed")
    index_records = [item for item in index.stdout.split("\0") if item]
    special_index_records = [
        item for item in index_records if not item.startswith("H ")
    ]
    workspace_sha256, workspace_file_count = _workspace_content_identity(
        repo_root, environment
    )
    tracked_integrity = _tracked_checkout_integrity(repo_root, environment)
    return {
        "commit": _git_output(
            "rev-parse", "HEAD", environment=environment, repo_root=repo_root
        ),
        "tree": _git_output(
            "rev-parse", "HEAD^{tree}", environment=environment, repo_root=repo_root
        ),
        "clean": (
            not records
            and not special_index_records
            and tracked_integrity["matches_index"]
        ),
        "porcelain_record_count": len(records),
        "porcelain_sha256": hashlib.sha256(
            porcelain.encode("utf-8", errors="replace")
        ).hexdigest(),
        "special_index_record_count": len(special_index_records),
        "special_index_sha256": _canonical_sha256(special_index_records),
        "workspace_content_sha256": workspace_sha256,
        "workspace_file_count": workspace_file_count,
        "tracked_checkout": tracked_integrity,
    }


def _load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("gates"), dict):
        raise ValueError("hardening/gates.yaml must contain a 'gates' mapping")
    for gate_id, gate in manifest["gates"].items():
        if not isinstance(gate_id, str) or not isinstance(gate, dict):
            raise ValueError("every hardening gate must be a named mapping")
        forbidden = FORBIDDEN_GATE_STATE_FIELDS.intersection(gate)
        if forbidden:
            fields = ", ".join(sorted(forbidden))
            raise ValueError(
                f"gate {gate_id} contains manually authoritative field(s): {fields}"
            )
    return manifest


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        return "unavailable"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tool_version(
    command: list[str], *, environment: dict[str, str], cwd: Path
) -> dict[str, Any]:
    executable = shutil.which(command[0], path=environment.get("PATH")) or "unavailable"
    try:
        resolved_command = (
            [executable, *command[1:]] if executable != "unavailable" else command
        )
        result = _run_small(
            resolved_command,
            timeout=15,
            environment=environment,
            cwd=cwd,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": False,
            "version": "unavailable",
            "executable": executable,
            "error": type(exc).__name__,
        }
    output = (result.stdout or result.stderr).strip().splitlines()
    version, redactions = _redact_text(output[0] if output else "unavailable")
    return {
        "available": result.returncode == 0,
        "version": version,
        "executable": executable,
        "executable_sha256": (
            _sha256_file(Path(executable))
            if executable != "unavailable"
            else "unavailable"
        ),
        "exit_code": result.returncode,
        "redactions": redactions,
    }


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _collect_environment(
    execution_environment: dict[str, str],
    process_environment: dict[str, Any],
    *,
    cwd: Path,
) -> dict[str, Any]:
    inventory_script = """
import json
import platform
import sys
from importlib import metadata

installed = {
    (str(dist.metadata.get("Name") or "").strip(), str(dist.version or "").strip())
    for dist in metadata.distributions()
}
installed = sorted(
    ({"name": name, "version": version} for name, version in installed if name),
    key=lambda item: (item["name"].casefold(), item["version"]),
)
print(json.dumps({
    "runtime": {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
    },
    "distributions": installed,
}, sort_keys=True))
"""
    inventory = _run_small(
        [sys.executable, "-c", inventory_script],
        timeout=30,
        environment=execution_environment,
        cwd=cwd,
    )
    if inventory.returncode != 0:
        raise RuntimeError(
            inventory.stderr.strip() or "unable to inventory Python environment"
        )
    try:
        python_environment = json.loads(inventory.stdout)
        python_runtime = python_environment["runtime"]
        distributions = python_environment["distributions"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("invalid Python environment inventory") from exc
    python_environment = {
        "runtime": python_runtime,
        "distributions": distributions,
    }
    git_tool = _tool_version(
        [str(GIT_EXECUTABLE), "--version"],
        environment=execution_environment,
        cwd=cwd,
    )
    return {
        "python": python_runtime,
        "python_executable_sha256": _sha256_file(Path(sys.executable)),
        "python_distributions": distributions,
        "python_environment_sha256": _canonical_sha256(python_environment),
        "pyproject_sha256": _sha256_file(cwd / "pyproject.toml"),
        "git": git_tool,
        "node": _tool_version(
            ["node", "--version"], environment=execution_environment, cwd=cwd
        ),
        "npm": _tool_version(
            ["npm", "--version"], environment=execution_environment, cwd=cwd
        ),
        "node_lock_sha256": _sha256_file(cwd / "desktop" / "package-lock.json"),
        "process_environment": process_environment,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
    }


def _drain_stream(stream: BinaryIO, capture: _BoundedCapture) -> None:
    try:
        while True:
            chunk = stream.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            capture.append(chunk)
    finally:
        stream.close()


def _drain_stream_guarded(
    stream: BinaryIO, capture: _BoundedCapture, state: _DrainState
) -> None:
    try:
        _drain_stream(stream, capture)
    except BaseException as exc:  # a broken log reader must fail the gate closed
        state.error = type(exc).__name__


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    process.kill()


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    if os.name != "posix":
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass


def _run_gate_command(
    command: list[str],
    *,
    timeout: float,
    environment: dict[str, str],
    cwd: Path,
    capture_limit: int = MAX_LOG_BYTES,
) -> GateCommandResult:
    stdout = _BoundedCapture(limit=capture_limit)
    stderr = _BoundedCapture(limit=capture_limit)
    popen_kwargs: dict[str, Any] = (
        {"start_new_session": True} if os.name == "posix" else {}
    )
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            env=environment,
            **popen_kwargs,
        )
    except OSError as exc:
        stderr.append(str(exc).encode("utf-8", errors="replace"))
        return GateCommandResult(
            actual_exit_code=None,
            timed_out=False,
            launch_error=type(exc).__name__,
            capture_incomplete=False,
            capture_errors={"stdout": None, "stderr": None},
            stdout=stdout,
            stderr=stderr,
        )

    assert process.stdout is not None
    assert process.stderr is not None
    stdout_state = _DrainState()
    stderr_state = _DrainState()
    stdout_thread = threading.Thread(
        target=_drain_stream_guarded,
        args=(process.stdout, stdout, stdout_state),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_drain_stream_guarded,
        args=(process.stderr, stderr, stderr_state),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process(process)
        process.wait()

    capture_deadline = time.monotonic() + CAPTURE_JOIN_TIMEOUT_SECONDS
    for capture_thread in (stdout_thread, stderr_thread):
        capture_thread.join(max(0.0, capture_deadline - time.monotonic()))
    capture_incomplete = (
        stdout_thread.is_alive()
        or stderr_thread.is_alive()
        or stdout_state.error is not None
        or stderr_state.error is not None
    )
    if capture_incomplete:
        # A descendant may have inherited a pipe after the gate process exited. Kill
        # the original process group, but never let that descendant block the runner.
        _kill_process_group(process)
        cleanup_deadline = time.monotonic() + 0.1
        for capture_thread in (stdout_thread, stderr_thread):
            capture_thread.join(max(0.0, cleanup_deadline - time.monotonic()))

    return GateCommandResult(
        actual_exit_code=None if timed_out else process.returncode,
        timed_out=timed_out,
        launch_error=None,
        capture_incomplete=capture_incomplete,
        capture_errors={
            "stdout": stdout_state.error,
            "stderr": stderr_state.error,
        },
        stdout=stdout,
        stderr=stderr,
    )


def _redact_text(value: str) -> tuple[str, int]:
    redactions = 0

    def replace_entire(match: re.Match[str]) -> str:
        nonlocal redactions
        redactions += 1
        return "[REDACTED]"

    def preserve_prefix(match: re.Match[str]) -> str:
        nonlocal redactions
        redactions += 1
        return f"{match.group('prefix')}[REDACTED]"

    def replace_url_credentials(match: re.Match[str]) -> str:
        nonlocal redactions
        redactions += 1
        return f"{match.group('scheme')}[REDACTED]@"

    value = _PRIVATE_KEY_BLOCK.sub(replace_entire, value)
    value = _AUTHORIZATION_VALUE.sub(preserve_prefix, value)
    value = _BEARER_VALUE.sub(preserve_prefix, value)
    value = _SENSITIVE_ASSIGNMENT.sub(preserve_prefix, value)
    value = _URL_CREDENTIALS.sub(replace_url_credentials, value)
    value, count = _GITHUB_TOKEN.subn("[REDACTED]", value)
    redactions += count
    value, count = _GITHUB_FINE_GRAINED_TOKEN.subn("[REDACTED]", value)
    redactions += count
    value, count = _NPM_TOKEN.subn("[REDACTED]", value)
    redactions += count
    value, count = _JWT_TOKEN.subn("[REDACTED]", value)
    redactions += count
    value, count = _HEX_PRIVATE_KEY.subn("[REDACTED]", value)
    redactions += count
    return value, redactions


def _redact_payload(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, list):
        redacted_items: list[Any] = []
        redactions = 0
        for item in value:
            redacted, count = _redact_payload(item)
            redacted_items.append(redacted)
            redactions += count
        return redacted_items, redactions
    if isinstance(value, dict):
        redacted_mapping: dict[Any, Any] = {}
        redactions = 0
        for key, item in value.items():
            redacted, count = _redact_payload(item)
            redacted_mapping[key] = redacted
            redactions += count
        return redacted_mapping, redactions
    return value, 0


def _sanitize_capture(capture: _BoundedCapture) -> tuple[str, dict[str, Any]]:
    captured, total_bytes = capture.snapshot()
    decoded = captured.decode("utf-8", errors="replace")
    redacted, redactions = _redact_text(decoded)
    return redacted, {
        "total_bytes": total_bytes,
        "stored_bytes": len(captured),
        "truncated": total_bytes > len(captured),
        "redactions": redactions,
        "limit_bytes": capture.limit,
    }


def _sanitize_command(command: list[str]) -> tuple[list[str], dict[str, Any]]:
    sanitized: list[str] = []
    redactions = 0
    truncated = False
    redact_next = False
    for item in command:
        if redact_next:
            redacted = "[REDACTED]"
            redactions += 1
            redact_next = False
        else:
            redacted, count = _redact_text(item)
            redactions += count
            redact_next = _SENSITIVE_FLAG.fullmatch(item) is not None
        if len(redacted) > MAX_COMMAND_ARG_CHARS:
            redacted = redacted[:MAX_COMMAND_ARG_CHARS] + "...[TRUNCATED]"
            truncated = True
        sanitized.append(redacted)
    return sanitized, {
        "redactions": redactions,
        "truncated": truncated,
        "argument_limit_chars": MAX_COMMAND_ARG_CHARS,
    }


def _resolve_within(root: Path, relative: Path) -> Path:
    if relative.is_absolute():
        raise ValueError("evidence paths must be relative")
    resolved_root = root.resolve()
    candidate = (resolved_root / relative).resolve()
    if not candidate.is_relative_to(resolved_root):
        raise ValueError("evidence path escapes its configured root")
    return candidate


def _evidence_path(
    manifest: dict[str, Any],
    gate_id: str,
    gate: dict[str, Any],
    commit: str,
    *,
    authoritative: bool,
    run_id: str,
) -> Path:
    configured_root = Path(str(manifest.get("evidence_root", CANONICAL_EVIDENCE_ROOT)))
    if configured_root != CANONICAL_EVIDENCE_ROOT:
        raise ValueError(
            f"evidence_root must be exactly {CANONICAL_EVIDENCE_ROOT.as_posix()}"
        )
    evidence_root = _resolve_within(REPO_ROOT, configured_root)
    commit_root = _resolve_within(evidence_root, Path(commit))
    if authoritative:
        configured = Path(
            str(gate.get("evidence_file") or f"{gate_id.replace('.', '/')}/result.json")
        )
        return _resolve_within(commit_root, configured)
    diagnostic_root = _resolve_within(
        commit_root, Path("diagnostics") / Path(*gate_id.split("."))
    )
    return _resolve_within(diagnostic_root, Path(f"{run_id}.json"))


def _evidence_path_is_ignored(path: Path, *, environment: dict[str, str]) -> bool:
    try:
        relative_path = path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError("evidence path is outside the repository") from exc
    result = _run_small(
        _git_command("check-ignore", "--quiet", "--", relative_path.as_posix()),
        timeout=30,
        environment=environment,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr.strip() or "git check-ignore failed")
    return result.returncode == 0


def _validate_evidence_paths(
    manifest: dict[str, Any],
    gate_id: str,
    gate: dict[str, Any],
    commit: str,
    *,
    run_id: str,
    environment: dict[str, str],
) -> dict[str, Path]:
    paths = {
        "authoritative": _evidence_path(
            manifest,
            gate_id,
            gate,
            commit,
            authoritative=True,
            run_id=run_id,
        ),
        "diagnostic": _evidence_path(
            manifest,
            gate_id,
            gate,
            commit,
            authoritative=False,
            run_id=run_id,
        ),
    }
    for path in paths.values():
        temporary_probe = path.with_name(f".{path.name}.probe.tmp")
        if not _evidence_path_is_ignored(path, environment=environment) or not (
            _evidence_path_is_ignored(temporary_probe, environment=environment)
        ):
            raise ValueError(
                "evidence and temporary paths must be ignored by Git before gate execution"
            )
    return paths


def _assert_no_symlink_ancestors(path: Path) -> None:
    try:
        relative = path.relative_to(REPO_ROOT)
    except ValueError:
        return
    current = REPO_ROOT
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError("evidence directory hierarchy cannot contain symlinks")


@contextmanager
def _isolated_worktree(
    commit: str,
    *,
    runtime_root: Path,
    environment: dict[str, str],
) -> Iterator[tuple[Path, dict[str, Any]]]:
    worktree = runtime_root / "worktree"
    added = _run_small(
        _git_command("worktree", "add", "--detach", str(worktree), commit),
        timeout=120,
        environment=environment,
        cwd=REPO_ROOT,
    )
    if added.returncode != 0:
        raise RuntimeError(
            added.stderr.strip() or added.stdout.strip() or "git worktree add failed"
        )

    dependency_mounts: dict[str, Any] = {
        "external_mounts": [],
        "desktop_node_modules": {"present": False},
    }
    try:
        yield worktree, dependency_mounts
    finally:
        removed = _run_small(
            _git_command("worktree", "remove", "--force", str(worktree)),
            timeout=120,
            environment=environment,
            cwd=REPO_ROOT,
        )
        if removed.returncode != 0:
            shutil.rmtree(worktree, ignore_errors=True)
            _run_small(
                _git_command("worktree", "prune"),
                timeout=30,
                environment=environment,
                cwd=REPO_ROOT,
            )


def _write_evidence_atomic(path: Path, payload: dict[str, Any]) -> None:
    _assert_no_symlink_ancestors(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_ancestors(path)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        if hasattr(os, "O_DIRECTORY"):
            directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    finally:
        temporary_path.unlink(missing_ok=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute one QuantLab v0.1-hardening gate and write commit-bound JSON evidence."
    )
    parser.add_argument(
        "gate_id", nargs="?", help="Gate identifier from hardening/gates.yaml"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available gate identifiers"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved command without executing it",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Run in diagnostic mode even when the tree is dirty. Diagnostic evidence is always "
            "non-authoritative and never overwrites the canonical result.json."
        ),
    )
    return parser


def _validated_gate(
    manifest: dict[str, Any], gate_id: str
) -> tuple[dict[str, Any], list[str], int, float]:
    gates: dict[str, Any] = manifest["gates"]
    if gate_id not in gates:
        raise KeyError(f"unknown hardening gate: {gate_id}")
    gate = gates[gate_id]
    command = gate.get("command")
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(item, str) for item in command)
    ):
        raise ValueError(
            f"gate {gate_id} must define command as a non-empty string list"
        )
    expected_exit_code = int(gate.get("expected_exit_code", 0))
    timeout_seconds = float(gate.get("timeout_seconds", 1800))
    if timeout_seconds <= 0:
        raise ValueError(f"gate {gate_id} timeout_seconds must be positive")
    return gate, command, expected_exit_code, timeout_seconds


def _resolve_command(command: list[str], *, environment: dict[str, str]) -> list[str]:
    resolved = list(command)
    if resolved[0] == "{python}":
        resolved[0] = sys.executable
    elif "{python}" in resolved:
        raise ValueError("{python} is only valid as the gate executable")

    if not Path(resolved[0]).is_absolute():
        executable = shutil.which(resolved[0], path=environment.get("PATH"))
        if executable is not None:
            resolved[0] = executable
    return resolved


def _empty_command_result(error: str) -> GateCommandResult:
    return GateCommandResult(
        actual_exit_code=None,
        timed_out=False,
        launch_error=error,
        capture_incomplete=False,
        capture_errors={"stdout": None, "stderr": None},
        stdout=_BoundedCapture(),
        stderr=_BoundedCapture(),
    )


def _normalize_npm_inventory(value: Any) -> Any:
    if isinstance(value, dict):
        omitted = {"path", "resolved", "link", "realpath", "_id"}
        return {
            key: _normalize_npm_inventory(item)
            for key, item in sorted(value.items())
            if key not in omitted
        }
    if isinstance(value, list):
        normalized = [_normalize_npm_inventory(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))
    return value


def _count_npm_packages(value: Any) -> int:
    if not isinstance(value, dict):
        return 0
    dependencies = value.get("dependencies")
    if not isinstance(dependencies, dict):
        return 1 if value.get("version") else 0
    return (1 if value.get("version") else 0) + sum(
        _count_npm_packages(item) for item in dependencies.values()
    )


def _npm_inventory_summary(value: Any) -> dict[str, Any]:
    normalized = _normalize_npm_inventory(value)
    canonical = json.dumps(
        normalized, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return {
        "format": "npm-ls-normalized-v1",
        "package_count": _count_npm_packages(normalized),
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _provision_desktop_dependencies(
    gate: dict[str, Any],
    *,
    workspace_root: Path,
    environment: dict[str, str],
    timeout: float,
) -> tuple[dict[str, Any], bool]:
    profile = str(gate.get("dependency_profile", "none"))
    if profile == "none":
        return {
            "profile": "none",
            "provisioning": {"result": "forbidden", "external_mounts": []},
            "inventory": None,
        }, True
    if profile != "desktop_locked":
        raise ValueError(f"unknown dependency profile: {profile}")

    npm_command = _resolve_command(
        ["npm", "--prefix", "desktop", "ci", "--ignore-scripts"],
        environment=environment,
    )
    provisioning_result = _run_gate_command(
        npm_command,
        timeout=timeout,
        environment=environment,
        cwd=workspace_root,
    )
    provisioning_passed = (
        not provisioning_result.timed_out
        and provisioning_result.launch_error is None
        and not provisioning_result.capture_incomplete
        and provisioning_result.actual_exit_code == 0
    )
    provisioning_stdout, provisioning_stdout_meta = _sanitize_capture(
        provisioning_result.stdout
    )
    provisioning_stderr, provisioning_stderr_meta = _sanitize_capture(
        provisioning_result.stderr
    )
    provisioning = {
        "command": _sanitize_command(npm_command)[0],
        "exit_code": provisioning_result.actual_exit_code,
        "timed_out": provisioning_result.timed_out,
        "result": "passed" if provisioning_passed else "failed",
        "stdout": provisioning_stdout,
        "stderr": provisioning_stderr,
        "log_metadata": {
            "stdout": provisioning_stdout_meta,
            "stderr": provisioning_stderr_meta,
        },
    }
    if not provisioning_passed:
        return {
            "profile": profile,
            "provisioning": provisioning,
            "inventory": None,
        }, False

    inventory_command = _resolve_command(
        ["npm", "--prefix", "desktop", "ls", "--all", "--json"],
        environment=environment,
    )
    inventory_result = _run_gate_command(
        inventory_command,
        timeout=min(timeout, 300),
        environment=environment,
        cwd=workspace_root,
        capture_limit=MAX_INVENTORY_BYTES,
    )
    raw_inventory, _ = inventory_result.stdout.snapshot()
    raw_inventory_text = raw_inventory.decode("utf-8", errors="replace")
    inventory_stdout, inventory_stdout_meta = _sanitize_capture(inventory_result.stdout)
    inventory_stderr, inventory_stderr_meta = _sanitize_capture(inventory_result.stderr)
    inventory_valid = False
    inventory_summary: dict[str, Any] | None = None
    if (
        not inventory_result.timed_out
        and inventory_result.launch_error is None
        and not inventory_result.capture_incomplete
        and inventory_result.actual_exit_code == 0
    ):
        try:
            inventory_summary = _npm_inventory_summary(json.loads(raw_inventory_text))
            inventory_valid = True
        except (TypeError, ValueError, json.JSONDecodeError):
            inventory_valid = False
    inventory_summary = inventory_summary or {
        "format": "npm-ls-normalized-v1",
        "package_count": 0,
        "sha256": "unavailable",
    }
    return {
        "profile": profile,
        "provisioning": provisioning,
        "inventory_provisioning": {
            "command": _sanitize_command(inventory_command)[0],
            "exit_code": inventory_result.actual_exit_code,
            "timed_out": inventory_result.timed_out,
            "result": "passed" if inventory_valid else "failed",
            "stdout": inventory_stdout,
            "stderr": inventory_stderr,
            "log_metadata": {
                "stdout": inventory_stdout_meta,
                "stderr": inventory_stderr_meta,
            },
        },
        "inventory": inventory_summary,
    }, inventory_valid


def _execute_gate(
    args: argparse.Namespace, manifest: dict[str, Any], runtime_root: Path
) -> int:
    try:
        gate, manifest_command, expected_exit_code, timeout_seconds = _validated_gate(
            manifest, args.gate_id
        )
        base_environment, _ = _execution_environment(runtime_root)
        dry_run_command = _resolve_command(
            manifest_command, environment=base_environment
        )
        invocation_before = _git_snapshot(REPO_ROOT, base_environment)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(
            json.dumps(
                {
                    "gate_id": args.gate_id,
                    "commit": invocation_before["commit"],
                    "tree_clean": invocation_before["clean"],
                    "diagnostic": bool(args.allow_dirty),
                    "command": _sanitize_command(dry_run_command)[0],
                    "manifest_command": _sanitize_command(manifest_command)[0],
                    "expected_exit_code": expected_exit_code,
                    "timeout_seconds": timeout_seconds,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if not invocation_before["clean"] and not args.allow_dirty:
        print(
            "ERROR: working tree is not clean; authoritative gate evidence requires a clean tree. "
            "Use --allow-dirty only for explicitly non-authoritative diagnostics.",
            file=sys.stderr,
        )
        return 2

    run_started_at = datetime.now(timezone.utc)
    run_id = f"{run_started_at.strftime('%Y%m%dT%H%M%S%fZ')}-{os.getpid()}"
    try:
        evidence_paths = _validate_evidence_paths(
            manifest,
            args.gate_id,
            gate,
            invocation_before["commit"],
            run_id=run_id,
            environment=base_environment,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"ERROR: invalid hardening evidence storage: {exc}", file=sys.stderr)
        return 2

    try:
        with _isolated_worktree(
            invocation_before["commit"],
            runtime_root=runtime_root,
            environment=base_environment,
        ) as (workspace_root, dependency_mounts):
            execution_environment, process_environment = _execution_environment(
                runtime_root, workspace_root=workspace_root
            )
            command = _resolve_command(
                manifest_command, environment=execution_environment
            )
            execution_before = _git_snapshot(workspace_root, execution_environment)
            if (
                not execution_before["clean"]
                or execution_before["commit"] != invocation_before["commit"]
                or execution_before["tree"] != invocation_before["tree"]
            ):
                raise RuntimeError(
                    "isolated execution checkout does not exactly match the evaluated commit"
                )

            environment = _collect_environment(
                execution_environment,
                process_environment,
                cwd=workspace_root,
            )
            dependency_details, provisioning_ok = _provision_desktop_dependencies(
                gate,
                workspace_root=workspace_root,
                environment=execution_environment,
                timeout=min(timeout_seconds, 900),
            )
            dependency_details["external_mounts"] = dependency_mounts.get(
                "external_mounts", []
            )
            environment["node_dependencies"] = dependency_details
            started_at = datetime.now(timezone.utc)
            if provisioning_ok:
                command_result = _run_gate_command(
                    command,
                    timeout=timeout_seconds,
                    environment=execution_environment,
                    cwd=workspace_root,
                )
            else:
                command_result = _empty_command_result("dependency_provisioning_failed")
            finished_at = datetime.now(timezone.utc)
            execution_after = _git_snapshot(workspace_root, execution_environment)
            invocation_after = _git_snapshot(REPO_ROOT, base_environment)
    except (
        OSError,
        RuntimeError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: hardening gate infrastructure failed: {exc}", file=sys.stderr)
        return 2

    integrity_errors: list[str] = []
    if not invocation_before["clean"]:
        integrity_errors.append("tree_dirty_before_gate")
    if not execution_after["clean"]:
        integrity_errors.append("tree_dirty_after_gate")
    if not invocation_after["clean"]:
        integrity_errors.append("invocation_tree_dirty_after_gate")
    node_dependencies = environment.get("node_dependencies", {})
    if node_dependencies.get("profile") == "desktop_locked":
        if node_dependencies.get("provisioning", {}).get("result") != "passed":
            integrity_errors.append("dependency_provisioning_failed")
        inventory = node_dependencies.get("inventory") or {}
        if inventory.get("sha256") == "unavailable":
            integrity_errors.append("dependency_inventory_failed")
    if node_dependencies.get("external_mounts"):
        integrity_errors.append("external_dependency_mounts_present")
    if execution_before["commit"] != execution_after["commit"]:
        integrity_errors.append("head_changed_during_gate")
    if execution_before["tree"] != execution_after["tree"]:
        integrity_errors.append("head_tree_changed_during_gate")
    if invocation_before["commit"] != invocation_after["commit"]:
        integrity_errors.append("invocation_head_changed_during_gate")
    if invocation_before["tree"] != invocation_after["tree"]:
        integrity_errors.append("invocation_head_tree_changed_during_gate")
    if (
        execution_before["workspace_content_sha256"]
        != execution_after["workspace_content_sha256"]
    ):
        integrity_errors.append("workspace_content_changed_during_gate")
    if (
        invocation_before["workspace_content_sha256"]
        != invocation_after["workspace_content_sha256"]
    ):
        integrity_errors.append("invocation_content_changed_during_gate")

    authoritative = not args.allow_dirty and not integrity_errors
    command_passed = (
        not command_result.timed_out
        and command_result.launch_error is None
        and not command_result.capture_incomplete
        and command_result.actual_exit_code == expected_exit_code
    )
    passed = authoritative and command_passed
    sanitized_command, command_log = _sanitize_command(command)
    stdout, stdout_log = _sanitize_capture(command_result.stdout)
    stderr, stderr_log = _sanitize_capture(command_result.stderr)
    evidence_path = evidence_paths["authoritative" if authoritative else "diagnostic"]

    try:
        payload: dict[str, Any] = {
            "schema_version": manifest.get("schema_version", "1.1"),
            "gate_id": args.gate_id,
            "wave": gate.get("wave"),
            "description": gate.get("description"),
            "commit": invocation_before["commit"],
            "verified_at": finished_at.isoformat(),
            "verified_by": execution_environment.get("GITHUB_ACTOR") or "unknown",
            "authoritative": authoritative,
            "evidence_kind": "authoritative" if authoritative else "diagnostic",
            "result": "passed" if passed else "failed",
            "command_result": "passed" if command_passed else "failed",
            "command": sanitized_command,
            "manifest_command": _sanitize_command(manifest_command)[0],
            "command_metadata": command_log,
            "expected_exit_code": expected_exit_code,
            "actual_exit_code": command_result.actual_exit_code,
            "timed_out": command_result.timed_out,
            "launch_error": command_result.launch_error,
            "capture_incomplete": command_result.capture_incomplete,
            "capture_errors": command_result.capture_errors,
            "duration_seconds": (finished_at - started_at).total_seconds(),
            "acceptance_claims": gate.get("acceptance", []),
            "source": {
                "before": execution_before,
                "after": execution_after,
                "invocation_checkout": {
                    "before": invocation_before,
                    "after": invocation_after,
                },
                "execution_isolation": "detached_worktree",
                "integrity_errors": integrity_errors,
            },
            "environment": environment,
            "evidence_storage": {
                "atomic_replace": True,
                "git_ignored": True,
                "prevalidated": True,
            },
            "stdout": stdout,
            "stderr": stderr,
            "log_metadata": {
                "stdout": stdout_log,
                "stderr": stderr_log,
            },
        }
        redacted_payload, artifact_redactions = _redact_payload(payload)
        if not isinstance(redacted_payload, dict):
            raise TypeError("redacted evidence payload must remain a mapping")
        payload = redacted_payload
        payload["redaction_summary"] = {
            "artifact_redactions": artifact_redactions,
            "policy": "secrets-v2",
        }
        _write_evidence_atomic(evidence_path, payload)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(
            f"ERROR: unable to write hardening evidence atomically: {exc}",
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "gate_id": args.gate_id,
                "result": payload["result"],
                "authoritative": authoritative,
                "evidence": str(evidence_path),
            },
            indent=2,
        )
    )
    if passed:
        return 0
    if args.allow_dirty and command_passed:
        return 3
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        manifest = _load_manifest()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    gates: dict[str, Any] = manifest["gates"]
    if args.list:
        for gate_id in sorted(gates):
            print(gate_id)
        return 0
    if not args.gate_id:
        print("ERROR: gate_id is required unless --list is used", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="quantlab-hardening-") as temporary:
        return _execute_gate(args, manifest, Path(temporary))


if __name__ == "__main__":
    raise SystemExit(main())
