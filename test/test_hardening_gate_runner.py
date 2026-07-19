from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
import yaml


RUNNER_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "verify_hardening_gate.py"
)
SPEC = importlib.util.spec_from_file_location(
    "quantlab_hardening_gate_runner", RUNNER_PATH
)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _gate(
    command: list[str],
    *,
    expected_exit_code: int = 0,
    timeout_seconds: float = 5,
    evidence_file: str = "test/gate/result.json",
    **extra: Any,
) -> dict[str, Any]:
    gate = {
        "wave": "test",
        "description": "temporary test gate",
        "command": command,
        "expected_exit_code": expected_exit_code,
        "timeout_seconds": timeout_seconds,
        "evidence_file": evidence_file,
        "acceptance": ["test_claim"],
    }
    gate.update(extra)
    return gate


def _create_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    gates: dict[str, dict[str, Any]],
) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "quantlab-tests@example.invalid")
    _git(repo, "config", "user.name", "QuantLab Tests")

    (repo / "hardening").mkdir()
    (repo / "desktop").mkdir()
    (repo / "hardening" / "gates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.1",
                "evidence_root": "outputs/hardening",
                "gates": gates,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (repo / "desktop" / "package-lock.json").write_text(
        '{"lockfileVersion": 3}\n', encoding="utf-8"
    )
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "gate-fixture"\nversion = "0.0.0"\n', encoding="utf-8"
    )
    (repo / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "test fixture")
    commit = _git(repo, "rev-parse", "HEAD")

    monkeypatch.setattr(runner, "REPO_ROOT", repo)
    monkeypatch.setattr(runner, "MANIFEST_PATH", repo / "hardening" / "gates.yaml")
    monkeypatch.setattr(
        runner, "NODE_LOCK_PATH", repo / "desktop" / "package-lock.json"
    )
    monkeypatch.setattr(runner, "PYPROJECT_PATH", repo / "pyproject.toml")
    return repo, commit


def _stub_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runner,
        "_collect_environment",
        lambda *_args, **_kwargs: {
            "python": {
                "version": "3.test",
                "implementation": "CPython",
                "executable": sys.executable,
            },
            "python_distributions": [{"name": "pytest", "version": "test"}],
            "python_environment_sha256": "python-environment-digest",
            "pyproject_sha256": "pyproject-digest",
            "node": {"available": True, "version": "v22.test", "exit_code": 0},
            "npm": {"available": True, "version": "10.test", "exit_code": 0},
            "node_lock_sha256": "node-lock-digest",
            "process_environment": {
                "policy": "sanitized-v1",
                "effective_environment_sha256": "environment-digest",
            },
            "platform": {"system": "test"},
        },
    )


def _canonical_evidence(
    repo: Path, commit: str, relative: str = "test/gate/result.json"
) -> Path:
    return repo / "outputs" / "hardening" / commit / relative


def _diagnostic_evidence(repo: Path, commit: str, gate_id: str) -> Path:
    matches = list(
        (
            repo
            / "outputs"
            / "hardening"
            / commit
            / "diagnostics"
            / Path(*gate_id.split("."))
        ).glob("*.json")
    )
    assert len(matches) == 1
    return matches[0]


def test_unknown_gate_returns_2_without_execution_or_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _ = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.success": _gate([sys.executable, "-c", "raise SystemExit(0)"])},
    )
    monkeypatch.setattr(
        runner,
        "_run_gate_command",
        lambda *args, **kwargs: pytest.fail("unknown gate must not execute a command"),
    )

    assert runner.main(["test.unknown"]) == 2
    assert not (repo / "outputs").exists()


def test_failed_command_returns_nonzero_and_writes_authoritative_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.failure": _gate([sys.executable, "-c", "raise SystemExit(7)"])},
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.failure"]) == 1
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    assert evidence["result"] == "failed"
    assert evidence["command_result"] == "failed"
    assert evidence["actual_exit_code"] == 7
    assert evidence["timed_out"] is False
    assert evidence["authoritative"] is True


def test_timeout_returns_nonzero_and_writes_bounded_failure_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.timeout": _gate(
                [
                    sys.executable,
                    "-c",
                    "import time; print('started', flush=True); time.sleep(5)",
                ],
                timeout_seconds=0.2,
            )
        },
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.timeout"]) == 1
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    assert evidence["result"] == "failed"
    assert evidence["timed_out"] is True
    assert evidence["actual_exit_code"] is None
    assert evidence["authoritative"] is True
    assert "started" in evidence["stdout"]


def test_inherited_pipe_cannot_block_runner_or_pass_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.capture": _gate([sys.executable, "-c", "raise SystemExit(0)"])},
    )
    _stub_environment(monkeypatch)
    monkeypatch.setattr(runner, "CAPTURE_JOIN_TIMEOUT_SECONDS", 0.05)

    def delayed_drain(*_args: Any) -> None:
        time.sleep(0.5)

    monkeypatch.setattr(runner, "_drain_stream", delayed_drain)
    started = time.monotonic()
    assert runner.main(["test.capture"]) == 1
    assert time.monotonic() - started < 2.0

    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    assert evidence["capture_incomplete"] is True
    assert evidence["command_result"] == "failed"
    assert evidence["result"] == "failed"
    assert evidence["authoritative"] is True


@pytest.mark.parametrize("ci_value", [None, "true"])
def test_dirty_tree_is_rejected_even_when_ci_is_true(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ci_value: str | None,
) -> None:
    repo, _ = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.sentinel": _gate(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('sentinel').write_text('ran')",
                ]
            )
        },
    )
    _stub_environment(monkeypatch)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    if ci_value is None:
        monkeypatch.delenv("CI", raising=False)
    else:
        monkeypatch.setenv("CI", ci_value)

    assert runner.main(["test.sentinel"]) == 2
    assert not (repo / "sentinel").exists()
    assert not (repo / "outputs").exists()


@pytest.mark.parametrize("index_flag", ["--assume-unchanged", "--skip-worktree"])
def test_index_flags_cannot_hide_a_dirty_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    index_flag: str,
) -> None:
    repo, _ = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.sentinel": _gate(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('sentinel').write_text('ran')",
                ]
            )
        },
    )
    _stub_environment(monkeypatch)
    _git(repo, "update-index", index_flag, "tracked.txt")
    (repo / "tracked.txt").write_text("hidden dirty content\n", encoding="utf-8")
    assert _git(repo, "status", "--short") == ""

    assert runner.main(["test.sentinel"]) == 2
    assert not (repo / "sentinel").exists()
    assert not (repo / "outputs").exists()


@pytest.mark.parametrize("dirty", [False, True])
def test_allow_dirty_is_always_non_authoritative_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dirty: bool,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.success": _gate([sys.executable, "-c", "raise SystemExit(0)"])},
    )
    _stub_environment(monkeypatch)
    if dirty:
        (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    assert runner.main(["test.success", "--allow-dirty"]) == 3
    evidence = json.loads(
        _diagnostic_evidence(repo, commit, "test.success").read_text(encoding="utf-8")
    )
    assert evidence["authoritative"] is False
    assert evidence["evidence_kind"] == "diagnostic"
    assert evidence["result"] == "failed"
    assert evidence["command_result"] == "passed"
    assert not _canonical_evidence(repo, commit).exists()


def test_gate_that_dirties_tree_cannot_produce_authoritative_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.dirtying": _gate(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('tracked.txt').write_text('changed')",
                ]
            )
        },
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.dirtying"]) == 1
    evidence = json.loads(
        _diagnostic_evidence(repo, commit, "test.dirtying").read_text(encoding="utf-8")
    )
    assert evidence["authoritative"] is False
    assert evidence["command_result"] == "passed"
    assert "tree_dirty_after_gate" in evidence["source"]["integrity_errors"]


def test_gate_that_changes_head_cannot_produce_authoritative_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.commit": _gate(
                ["git", "commit", "--allow-empty", "-m", "gate changed head"]
            )
        },
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.commit"]) == 1
    evidence = json.loads(
        _diagnostic_evidence(repo, commit, "test.commit").read_text(encoding="utf-8")
    )
    assert evidence["authoritative"] is False
    assert evidence["source"]["before"]["commit"] == commit
    assert evidence["source"]["after"]["commit"] != commit
    assert "head_changed_during_gate" in evidence["source"]["integrity_errors"]


def test_manual_result_fields_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _ = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.manual": _gate(
                [sys.executable, "-c", "raise SystemExit(0)"],
                result="passed",
                authoritative=True,
            )
        },
    )

    assert runner.main(["test.manual"]) == 2
    assert not (repo / "outputs").exists()


def test_atomic_write_failure_preserves_previous_result_and_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result_path = tmp_path / "evidence" / "result.json"
    result_path.parent.mkdir()
    result_path.write_text('{"previous": true}\n', encoding="utf-8")
    previous = result_path.read_bytes()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated atomic replace failure")

    monkeypatch.setattr(runner.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        runner._write_evidence_atomic(result_path, {"replacement": True})

    assert result_path.read_bytes() == previous
    assert not list(result_path.parent.glob(".result.json.*.tmp"))


def test_evidence_records_exact_commit_tree_and_resolved_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.success": _gate([sys.executable, "-c", "raise SystemExit(0)"])},
    )

    assert runner.main(["test.success"]) == 0
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    environment = evidence["environment"]
    assert evidence["authoritative"] is True
    assert evidence["result"] == "passed"
    assert evidence["commit"] == commit
    assert evidence["source"]["before"]["commit"] == commit
    assert evidence["source"]["after"]["commit"] == commit
    assert evidence["source"]["before"]["clean"] is True
    assert evidence["source"]["after"]["clean"] is True
    assert environment["python"]["version"]
    assert environment["python"]["implementation"]
    assert environment["python"]["executable"] == sys.executable
    assert environment["python_distributions"] == sorted(
        environment["python_distributions"],
        key=lambda item: (item["name"].casefold(), item["version"]),
    )
    expected_python_digest = runner._canonical_sha256(
        {
            "runtime": environment["python"],
            "distributions": environment["python_distributions"],
        }
    )
    assert environment["python_environment_sha256"] == expected_python_digest
    assert environment["node"]["version"]
    assert environment["node"]["executable"]
    assert environment["npm"]["version"]
    assert environment["npm"]["executable"]
    expected_node_lock = hashlib.sha256(
        (repo / "desktop" / "package-lock.json").read_bytes()
    ).hexdigest()
    assert environment["node_lock_sha256"] == expected_node_lock
    assert environment["node_lock_sha256"] != environment["python_environment_sha256"]
    assert environment["platform"]["system"]


def test_python_placeholder_and_sanitized_process_environment_are_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    variables = [
        "PYTHONPATH",
        "PYTEST_ADDOPTS",
        "NODE_OPTIONS",
        "NPM_CONFIG_USERCONFIG",
        "EXAMPLE_API_TOKEN",
    ]
    script = (
        "import os; "
        f"print('|'.join('missing' if os.getenv(name) is None else 'present' "
        f"for name in {variables!r}))"
    )
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.environment": _gate(["{python}", "-c", script])},
    )
    for name in variables:
        monkeypatch.setenv(name, f"injected-{name.lower()}")

    assert runner.main(["test.environment"]) == 0
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    process_environment = evidence["environment"]["process_environment"]
    assert evidence["manifest_command"][0] == "{python}"
    assert evidence["command"][0] == sys.executable
    child_values = evidence["stdout"].strip().split("|")
    assert child_values[0] != "injected-pythonpath"
    assert child_values[1] == "missing"
    assert child_values[2] == "missing"
    assert child_values[3] != "injected-npm_config_userconfig"
    assert child_values[4] == "missing"
    assert {"NODE_OPTIONS", "PYTEST_ADDOPTS", "EXAMPLE_API_TOKEN"}.issubset(
        process_environment["removed_variable_names"]
    )
    assert "PYTEST_ADDOPTS" not in process_environment["effective_variable_names"]
    assert "NODE_OPTIONS" not in process_environment["effective_variable_names"]
    assert "EXAMPLE_API_TOKEN" not in process_environment["effective_variable_names"]
    assert process_environment["effective_environment_sha256"]


def test_dependency_free_gate_does_not_mount_source_node_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.node-free": _gate(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; print(Path('desktop/node_modules').exists())",
                ],
                dependency_profile="none",
            )
        },
    )
    (repo / ".git" / "info" / "exclude").write_text(
        "desktop/node_modules/\n", encoding="utf-8"
    )
    (repo / "desktop" / "node_modules").mkdir()
    (repo / "desktop" / "node_modules" / "marker").write_text(
        "tampered", encoding="utf-8"
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.node-free"]) == 0
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    assert evidence["stdout"].strip() == "False"
    assert evidence["environment"]["node_dependencies"]["profile"] == "none"
    assert evidence["environment"]["node_dependencies"]["external_mounts"] == []


def test_tampered_source_node_modules_cannot_influence_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.node-free": _gate(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; print(Path('desktop/node_modules/evil.py').exists())",
                ],
                dependency_profile="none",
            )
        },
    )
    (repo / ".git" / "info" / "exclude").write_text(
        "desktop/node_modules/\n", encoding="utf-8"
    )
    (repo / "desktop" / "node_modules").mkdir()
    (repo / "desktop" / "node_modules" / "evil.py").write_text(
        "raise SystemExit(99)\n", encoding="utf-8"
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.node-free"]) == 0
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    assert evidence["stdout"].strip() == "False"


def test_desktop_locked_profile_provisions_inside_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.desktop-locked": _gate(
                [sys.executable, "-c", "raise SystemExit(0)"],
                dependency_profile="desktop_locked",
            )
        },
    )
    _stub_environment(monkeypatch)
    calls: list[tuple[list[str], Path]] = []

    def fake_run(
        command: list[str], *, cwd: Path, **_kwargs: Any
    ) -> runner.GateCommandResult:
        calls.append((command, cwd))
        if "ci" in command:
            (cwd / "desktop" / "node_modules").mkdir()
        stdout = runner._BoundedCapture()
        if "ls" in command:
            stdout.append(b'{"name":"fixture","version":"1.0.0","dependencies":{}}')
        return runner.GateCommandResult(
            actual_exit_code=0,
            timed_out=False,
            launch_error=None,
            capture_incomplete=False,
            capture_errors={"stdout": None, "stderr": None},
            stdout=stdout,
            stderr=runner._BoundedCapture(),
        )

    monkeypatch.setattr(runner, "_run_gate_command", fake_run)
    assert runner.main(["test.desktop-locked"]) == 0
    assert len(calls) == 3
    assert all(repo not in cwd.parents for _, cwd in calls)
    assert all("desktop/node_modules" not in str(cwd) for _, cwd in calls)
    evidence = json.loads(_canonical_evidence(repo, commit).read_text(encoding="utf-8"))
    assert evidence["environment"]["node_dependencies"]["profile"] == "desktop_locked"
    assert (
        evidence["environment"]["node_dependencies"]["inventory"]["package_count"] == 1
    )


def test_failed_dependency_provisioning_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.desktop-locked": _gate(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('must-not-run').write_text('ran')",
                ],
                dependency_profile="desktop_locked",
            )
        },
    )
    _stub_environment(monkeypatch)
    calls = 0

    def failed_provisioning(*_args: Any, **_kwargs: Any) -> runner.GateCommandResult:
        nonlocal calls
        calls += 1
        return runner.GateCommandResult(
            actual_exit_code=17,
            timed_out=False,
            launch_error=None,
            capture_incomplete=False,
            capture_errors={"stdout": None, "stderr": None},
            stdout=runner._BoundedCapture(),
            stderr=runner._BoundedCapture(),
        )

    monkeypatch.setattr(runner, "_run_gate_command", failed_provisioning)
    assert runner.main(["test.desktop-locked"]) == 1
    assert calls == 1
    assert not (repo / "must-not-run").exists()
    evidence = json.loads(
        _diagnostic_evidence(repo, commit, "test.desktop-locked").read_text()
    )
    assert evidence["authoritative"] is False
    assert evidence["result"] == "failed"
    assert "dependency_provisioning_failed" in evidence["source"]["integrity_errors"]


def test_resolved_node_dependency_inventory_is_deterministic_and_recorded() -> None:
    first = {
        "name": "fixture",
        "version": "1.0.0",
        "path": "/tmp/one/desktop",
        "dependencies": {"z": {"version": "2.0.0", "path": "/tmp/one/z"}},
    }
    second = {
        "dependencies": {"z": {"path": "/var/other/z", "version": "2.0.0"}},
        "path": "/var/other/desktop",
        "version": "1.0.0",
        "name": "fixture",
    }
    assert runner._npm_inventory_summary(first) == runner._npm_inventory_summary(second)
    changed = dict(second)
    changed["version"] = "1.0.1"
    assert (
        runner._npm_inventory_summary(changed)["sha256"]
        != runner._npm_inventory_summary(second)["sha256"]
    )


def test_noncanonical_or_tracked_evidence_root_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _ = _create_repo(
        tmp_path,
        monkeypatch,
        {"test.success": _gate([sys.executable, "-c", "raise SystemExit(0)"])},
    )
    _stub_environment(monkeypatch)
    manifest_path = repo / "hardening" / "gates.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["evidence_root"] = "evidence"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    _git(repo, "add", "hardening/gates.yaml")
    _git(repo, "commit", "-m", "configure unsafe evidence root")

    assert runner.main(["test.success"]) == 2
    assert not (repo / "evidence").exists()

    manifest["evidence_root"] = "outputs/hardening"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    (repo / ".gitignore").write_text("", encoding="utf-8")
    _git(repo, "add", "hardening/gates.yaml", ".gitignore")
    _git(repo, "commit", "-m", "track evidence root")

    assert runner.main(["test.success"]) == 2
    assert not (repo / "outputs").exists()


def test_logs_and_command_are_redacted_and_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "supersecretvalue"
    bearer_secret = "bearer-secret-value"
    stderr_secret = "stderr-password-value"
    split_argument_secret = "opaque-value-without-a-sensitive-name"
    script = (
        "import sys;"
        f"print('API_KEY={secret}');"
        f"print('Authorization: Bearer {bearer_secret}');"
        f"print('password={stderr_secret}', file=sys.stderr);"
        f"print('X' * {runner.MAX_LOG_BYTES + 4096})"
    )
    repo, commit = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.logs": _gate(
                [
                    sys.executable,
                    "-c",
                    script,
                    "--api-key",
                    split_argument_secret,
                ]
            )
        },
    )
    _stub_environment(monkeypatch)

    assert runner.main(["test.logs"]) == 0
    evidence_path = _canonical_evidence(repo, commit)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    serialized = evidence_path.read_text(encoding="utf-8")
    assert secret not in serialized
    assert bearer_secret not in serialized
    assert stderr_secret not in serialized
    assert split_argument_secret not in serialized
    assert "[REDACTED]" in serialized
    assert evidence["log_metadata"]["stdout"]["truncated"] is True
    assert evidence["log_metadata"]["stdout"]["stored_bytes"] <= runner.MAX_LOG_BYTES
    assert evidence["log_metadata"]["stderr"]["stored_bytes"] <= runner.MAX_LOG_BYTES
    assert evidence["command_metadata"]["redactions"] >= 2


def test_list_only_prints_known_gates_without_writing_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _ = _create_repo(
        tmp_path,
        monkeypatch,
        {
            "test.beta": _gate([sys.executable, "-c", "raise SystemExit(0)"]),
            "test.alpha": _gate([sys.executable, "-c", "raise SystemExit(0)"]),
        },
    )

    assert runner.main(["--list"]) == 0
    assert capsys.readouterr().out.splitlines() == ["test.alpha", "test.beta"]
    assert not (repo / "outputs").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_node_modules_symlink_is_never_ignored_by_git_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _create_repo(tmp_path, monkeypatch, {"test.ok": _gate([sys.executable, "-c", "pass"])})
    target = tmp_path / "external-node-modules"
    target.mkdir()
    (repo / "desktop" / "node_modules").symlink_to(target, target_is_directory=True)
    env, _ = runner._execution_environment(tmp_path / "runtime")
    snapshot = runner._git_snapshot(repo, env)
    assert snapshot["clean"] is False
    assert snapshot["porcelain_record_count"] > 0


def test_sanitized_path_prefers_selected_node_and_npm_over_system_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = tmp_path / "selected-bin"
    system = tmp_path / "system-bin"
    selected.mkdir()
    system.mkdir()
    for directory, version in ((selected, "selected"), (system, "system")):
        for executable in ("node", "npm"):
            path = directory / executable
            path.write_text(f"#!/bin/sh\nprintf '%s\\n' {version}\n", encoding="utf-8")
            path.chmod(0o755)
    monkeypatch.setenv("PATH", os.pathsep.join((str(selected), str(system))))
    environment, _ = runner._execution_environment(tmp_path / "runtime")
    assert environment["PATH"].split(os.pathsep)[0] == str(selected)
    assert environment["SELECTED_NODE"] == str(selected / "node")
    assert environment["SELECTED_NPM"] == str(selected / "npm")
    assert runner.shutil.which("node", path=environment["PATH"]) == str(selected / "node")
    assert runner.shutil.which("npm", path=environment["PATH"]) == str(selected / "npm")


def test_truncated_npm_inventory_is_rejected_before_json_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _create_repo(tmp_path, monkeypatch, {"test.ok": _gate([sys.executable, "-c", "pass"])})
    valid_json = b'{"name":"fixture","version":"1.0.0"}'
    capture = runner._BoundedCapture(limit=len(valid_json))
    capture.append(valid_json)
    capture.append(b"additional-output")
    stored, total = capture.snapshot()
    assert stored == valid_json
    assert total > len(stored)
    empty = runner._BoundedCapture()
    calls = iter([
        runner.GateCommandResult(0, False, None, False, {}, runner._BoundedCapture(), runner._BoundedCapture()),
        runner.GateCommandResult(0, False, None, False, {}, capture, empty),
    ])
    monkeypatch.setattr(runner, "_resolve_command", lambda command, environment: command)
    monkeypatch.setattr(runner, "_run_gate_command", lambda *args, **kwargs: next(calls))
    details, ok = runner._provision_desktop_dependencies(
        {"dependency_profile": "desktop_locked"}, workspace_root=repo,
        environment=os.environ.copy(), timeout=10,
    )
    assert ok is False
    assert details["inventory"]["capture"]["truncated"] is True
    assert details["inventory"]["sha256"] == "unavailable"


def test_valid_json_prefix_with_additional_truncated_output_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _create_repo(tmp_path, monkeypatch, {"test.ok": _gate([sys.executable, "-c", "pass"])})
    valid_json = b'{"name":"fixture","version":"1.0.0"}'
    capture = runner._BoundedCapture(limit=len(valid_json))
    capture.append(valid_json)
    capture.append(b"additional-output")
    stored, total = capture.snapshot()
    assert stored == valid_json and total > len(stored)
    empty = runner._BoundedCapture()
    calls = iter([
        runner.GateCommandResult(0, False, None, False, {}, runner._BoundedCapture(), runner._BoundedCapture()),
        runner.GateCommandResult(0, False, None, False, {}, capture, empty),
    ])
    monkeypatch.setattr(runner, "_resolve_command", lambda command, environment: command)
    monkeypatch.setattr(runner, "_run_gate_command", lambda *args, **kwargs: next(calls))
    details, ok = runner._provision_desktop_dependencies(
        {"dependency_profile": "desktop_locked"}, workspace_root=repo,
        environment=os.environ.copy(), timeout=10,
    )
    assert ok is False
    assert details["inventory"]["capture"]["truncated"] is True
    assert details["inventory"]["sha256"] == "unavailable"
    assert details["inventory_provisioning"]["result"] == "failed"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_dependency_free_gate_with_node_modules_symlink_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    script = f"import pathlib; pathlib.Path('desktop/node_modules').symlink_to({str(outside)!r}, target_is_directory=True)"
    repo, commit = _create_repo(tmp_path, monkeypatch, {"test.symlink": _gate([sys.executable, "-c", script])})
    _stub_environment(monkeypatch)
    assert runner.main(["test.symlink"]) != 0
    assert not _canonical_evidence(repo, commit).exists()
    evidence = json.loads(_diagnostic_evidence(repo, commit, "test.symlink").read_text())
    assert evidence["authoritative"] is False
    assert evidence["evidence_kind"] == "diagnostic"
    assert evidence["result"] == "failed"
    assert "node_modules_symlink_detected" in evidence["source"]["integrity_errors"]
    assert "external_node_modules_reference" in evidence["source"]["integrity_errors"]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_gate_created_external_node_modules_symlink_fails_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = "import pathlib; pathlib.Path('desktop/node_modules').mkdir()"
    repo, commit = _create_repo(tmp_path, monkeypatch, {"test.none": _gate([sys.executable, "-c", script], dependency_profile="none")})
    _stub_environment(monkeypatch)
    assert runner.main(["test.none"]) != 0
    assert not _canonical_evidence(repo, commit).exists()
    evidence = json.loads(_diagnostic_evidence(repo, commit, "test.none").read_text())
    assert evidence["authoritative"] is False
    assert "unexpected_node_modules_for_dependency_free_gate" in evidence["source"]["integrity_errors"]
