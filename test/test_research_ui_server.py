from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "research_ui" / "server.py"
SPEC = importlib.util.spec_from_file_location("research_ui_server", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
research_ui_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research_ui_server)


def _write_session(root: Path, session_id: str, status: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "artifacts").mkdir()
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": session_id,
                "mode": "paper",
                "command": "paper",
                "status": status,
                "created_at": "2026-03-25T18:00:00",
                "request_id": f"req_{session_id}",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "mode": "paper",
                "command": "paper",
                "status": status,
                "request_id": f"req_{session_id}",
                "updated_at": "2026-03-25T18:05:00",
                "error_type": "DataError" if status == "failed" else None,
                "message": "boom" if status == "failed" else None,
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "report.json").write_text(
        json.dumps(
            {
                "status": status,
                "header": {"run_id": session_id, "mode": "paper"},
                "machine_contract": {"contract_type": "quantlab.paper.result"},
            }
        ),
        encoding="utf-8",
    )


def _write_broker_validation_session(root: Path, session_id: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "adapter_name": "kraken",
                "status": "submitted",
                "created_at": "2026-03-26T10:00:00",
                "request_id": f"req_{session_id}",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "submitted",
                "updated_at": "2026-03-26T10:05:00",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_order_validate.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.broker.order_validate",
                "adapter_name": "kraken",
                "remote_validation_called": True,
                "validation_accepted": True,
                "validation_reasons": [],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "approval.json").write_text(
        json.dumps(
            {
                "status": "approved",
                "reviewed_by": "marce",
                "reviewed_at": "2026-03-26T10:06:00",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_submit_gate.json").write_text(
        json.dumps(
            {
                "submit_state": "ready_for_supervised_submit_gate",
                "confirmed_by": "marce",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_submit_response.json").write_text(
        json.dumps(
            {
                "submit_state": "submitted",
                "generated_at": "2026-03-26T10:07:00",
                "submitted": True,
                "remote_submit_called": True,
                "txid": ["ABC123"],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "broker_order_status.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-03-26T10:08:00",
                "status_known": True,
                "normalized_state": "open",
                "matched_txid": ["ABC123"],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )


def _write_hyperliquid_submit_session(root: Path, session_id: str) -> None:
    session_dir = root / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "session_metadata.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "submitted",
                "created_at": "2026-03-27T12:00:00",
                "request_id": f"req_{session_id}",
                "source_signer_id": "0x1111111111111111111111111111111111111111",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "session_status.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "open",
                "updated_at": "2026-03-27T12:06:00",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "order_status_known": True,
                "order_status_state": "open",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_signed_action.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:01:00",
                "readiness_allowed": True,
                "execution_context": {"resolved_transport": "websocket"},
                "signature_envelope": {"signature_state": "signed"},
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_submit_response.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.submit_response",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:05:00",
                "submit_state": "submitted_remote",
                "remote_submit_called": True,
                "submitted": True,
                "response_type": "resting",
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_order_status.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.order_status",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:06:00",
                "status_known": True,
                "normalized_state": "open",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "hyperliquid_supervision.json").write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.hyperliquid.supervision",
                "adapter_name": "hyperliquid",
                "generated_at": "2026-03-27T12:07:00",
                "supervision_state": "active",
                "attention_required": False,
                "polls_completed": 3,
                "monitoring_mode": "websocket_aware_rest_polling",
                "resolved_transport": "websocket",
                "errors": [],
            }
        ),
        encoding="utf-8",
    )


def _write_validation_artifact(target: Path, *, accepted: bool, handoff_id: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "artifact_type": "quantlab.pretrade.handoff_validation",
                "generated_at": "2026-03-27T12:43:38",
                "source_artifact_path": "C:\\Users\\marce\\Documents\\meta_trade\\tests\\fixtures\\expected_quantlab_handoff.json",
                "accepted": accepted,
                "reasons": [] if accepted else ["pretrade_context_side_invalid"],
                "handoff_contract": {
                    "contract_type": "calculadora_riesgo.quantlab_handoff",
                    "contract_version": "1.0",
                    "handoff_id": handoff_id,
                    "generated_at": "2026-03-27T12:00:00.000Z",
                },
                "source": {
                    "planner": "contract-fixture",
                    "trade_plan_contract_type": "calculadora_riesgo.trade_plan",
                    "trade_plan_contract_version": "1.0",
                    "trade_plan_id": handoff_id,
                },
                "pretrade_context": {
                    "symbol": "ETH-USD",
                    "venue": "hyperliquid",
                    "side": "buy",
                    "accountId": "acct_demo_001",
                    "strategyId": "breakout_v1",
                },
                "quantlab_hints": {
                    "ready_for_draft_execution_intent": accepted,
                    "missing_fields": [],
                    "boundary_note": "This handoff artifact is for bounded QuantLab ingestion only.",
                },
                "trade_plan": {
                    "contract_type": "calculadora_riesgo.trade_plan",
                    "contract_version": "1.0",
                    "plan_id": handoff_id,
                },
                "quantlab_boundary": {
                    "ready_for_draft_execution_intent": accepted,
                    "policy_owner": "quantlab",
                    "execution_authority": "quantlab",
                    "submit_authority": "quantlab",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_build_paper_health_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_paper_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0


def test_build_paper_health_payload_summarizes_existing_sessions(tmp_path: Path):
    paper_root = tmp_path / "outputs" / "paper_sessions"
    _write_session(paper_root, "paper_001", "success")
    _write_session(paper_root, "paper_002", "failed")

    payload, status = research_ui_server.build_paper_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 2
    assert payload["status_counts"]["success"] == 1
    assert payload["status_counts"]["failed"] == 1


def test_build_paper_alerts_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_paper_alerts_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0
    assert payload["has_alerts"] is False
    assert payload["alerts"] == []


def test_build_paper_alerts_payload_summarizes_existing_alerts(tmp_path: Path):
    paper_root = tmp_path / "outputs" / "paper_sessions"
    _write_session(paper_root, "paper_001", "success")
    _write_session(paper_root, "paper_002", "failed")

    payload, status = research_ui_server.build_paper_alerts_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 2
    assert payload["has_alerts"] is True
    assert payload["alert_status"] == "critical"
    assert payload["latest_success_session_id"] == "paper_001"
    assert payload["latest_alert_session_id"] == "paper_002"
    assert payload["latest_alert_code"] == "PAPER_SESSION_FAILED"
    assert payload["alert_counts"]["critical"] == 1


def test_build_broker_health_payload_returns_zero_state_when_root_missing(tmp_path: Path):
    payload, status = research_ui_server.build_broker_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is False
    assert payload["total_sessions"] == 0
    assert payload["has_alerts"] is False


def test_build_broker_health_payload_summarizes_existing_sessions(tmp_path: Path):
    broker_root = tmp_path / "outputs" / "broker_order_validations"
    _write_broker_validation_session(broker_root, "broker_001")

    payload, status = research_ui_server.build_broker_health_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["total_sessions"] == 1
    assert payload["submitted_sessions"] == 1
    assert payload["order_status_known_sessions"] == 1
    assert payload["latest_submit_session_id"] == "broker_001"


def test_build_hyperliquid_surface_payload_detects_latest_artifacts(tmp_path: Path):
    outputs_root = tmp_path / "outputs" / "hyperliquid"
    outputs_root.mkdir(parents=True)
    (outputs_root / "hyperliquid_account_readiness.json").write_text(
        json.dumps(
            {
                "adapter_name": "hyperliquid",
                "artifact_type": "quantlab.hyperliquid.account_readiness",
                "generated_at": "2026-03-26T12:00:00",
                "readiness_allowed": True,
                "execution_account_role": "user",
            }
        ),
        encoding="utf-8",
    )
    (outputs_root / "hyperliquid_signed_action.json").write_text(
        json.dumps(
            {
                "adapter_name": "hyperliquid",
                "artifact_type": "quantlab.hyperliquid.signed_action",
                "generated_at": "2026-03-26T12:05:00",
                "readiness_allowed": True,
                "execution_context": {"resolved_transport": "websocket"},
                "signature_envelope": {"signature_state": "pending_signer_backend"},
            }
        ),
        encoding="utf-8",
    )
    _write_hyperliquid_submit_session(tmp_path / "outputs" / "hyperliquid_submits", "hyper_001")

    payload, status = research_ui_server.build_hyperliquid_surface_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["implemented_surfaces"]["signed_action_build"] is True
    assert payload["implemented_surfaces"]["order_submit"] is True
    assert payload["implemented_surfaces"]["continuous_supervision"] is True
    assert payload["submit_health"]["total_sessions"] == 1
    assert payload["submit_has_alerts"] is False
    assert payload["latest_artifacts"]["order_status"]["normalized_state"] == "open"
    assert payload["latest_ready_artifact_type"] == "quantlab.hyperliquid.supervision"
    assert payload["signature_state"] in {"pending_signer_backend", "signed"}


def test_build_meta_trade_workspace_payload_detects_external_repo(tmp_path: Path):
    project_root = tmp_path / "quant_lab"
    project_root.mkdir()
    meta_trade = tmp_path / "meta_trade"
    meta_trade.mkdir()
    (meta_trade / "README.md").write_text("# Trading Risk Calculator\n", encoding="utf-8")
    (meta_trade / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (meta_trade / "risk-core.js").write_text("module.exports = {};\n", encoding="utf-8")
    (meta_trade / "package.json").write_text(
        json.dumps({"scripts": {"dev": "node scripts/serve-static.js", "test": "node tests/run_js_tests.js"}}),
        encoding="utf-8",
    )
    (meta_trade / "web").mkdir()
    (meta_trade / "web" / "risk-ui.js").write_text("export {};\n", encoding="utf-8")
    (meta_trade / "cli").mkdir()
    (meta_trade / "cli" / "trade-plan.js").write_text("#!/usr/bin/env node\n", encoding="utf-8")
    (meta_trade / "tests" / "fixtures").mkdir(parents=True)
    (meta_trade / "tests" / "run_js_tests.js").write_text("console.log('ok')\n", encoding="utf-8")
    (meta_trade / "tests" / "fixtures" / "expected_quantlab_handoff.json").write_text("{}", encoding="utf-8")
    (meta_trade / "docs").mkdir()
    (meta_trade / "docs" / "quantlab-handoff-contract.md").write_text("# contract\n", encoding="utf-8")

    payload, status = research_ui_server.build_meta_trade_workspace_payload(project_root)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["repo"]["present"] is True
    assert payload["workspace_summary"]["product_surfaces_present"] >= 2
    assert payload["workspace_summary"]["engine_modules_present"] >= 2
    assert payload["workspace_summary"]["package_script_total"] == 2
    assert any(group["label"] == "Workspace" for group in payload["product_surface_groups"])
    assert any(group["label"] == "Core" for group in payload["engine_module_groups"])


def test_build_pretrade_handoff_payload_returns_empty_when_root_is_missing(tmp_path: Path):
    payload, status = research_ui_server.build_pretrade_handoff_payload(tmp_path)

    assert status == 200
    assert payload["available"] is False
    assert payload["has_validation"] is False
    assert payload["validation_state"] == "empty"


def test_build_pretrade_handoff_payload_returns_empty_when_root_has_no_artifacts(tmp_path: Path):
    (tmp_path / "outputs" / "pretrade_handoff").mkdir(parents=True)

    payload, status = research_ui_server.build_pretrade_handoff_payload(tmp_path)

    assert status == 200
    assert payload["available"] is True
    assert payload["has_validation"] is False
    assert payload["validation_state"] == "empty"


def test_build_pretrade_handoff_payload_selects_latest_validation_artifact(tmp_path: Path):
    older = tmp_path / "outputs" / "pretrade_handoff" / "older" / "pretrade_handoff_validation.json"
    newer = tmp_path / "outputs" / "pretrade_handoff" / "newer" / "pretrade_handoff_validation.json"

    _write_validation_artifact(older, accepted=False, handoff_id="handoff-older")
    _write_validation_artifact(newer, accepted=True, handoff_id="handoff-newer")

    os.utime(older, (older.stat().st_atime, older.stat().st_mtime - 30))
    os.utime(newer, None)

    payload, status = research_ui_server.build_pretrade_handoff_payload(tmp_path)

    assert status == 200
    assert payload["available"] is True
    assert payload["has_validation"] is True
    assert payload["accepted"] is True
    assert payload["validation_state"] == "accepted"
    assert payload["handoff_id"] == "handoff-newer"
    assert payload["latest_validation_path"] == str(newer)
    assert payload["latest_validation_href"] == "/outputs/pretrade_handoff/newer/pretrade_handoff_validation.json"
    assert payload["source_artifact_path"] == "C:\\Users\\marce\\Documents\\meta_trade\\tests\\fixtures\\expected_quantlab_handoff.json"
    assert payload["source_artifact_href"] is None


def test_normalize_launch_request_accepts_run_payload():
    payload = research_ui_server._normalize_launch_request(
        {
            "command": "run",
            "params": {
                "ticker": "ETH-USD",
                "start": "2024-01-01",
                "end": "2024-12-31",
                "interval": "1d",
                "paper": True,
                "initial_cash": 2500,
            },
        }
    )

    assert payload["schema_version"] == "1.0"
    assert payload["command"] == "run"
    assert payload["params"]["ticker"] == "ETH-USD"
    assert payload["params"]["paper"] is True
    assert payload["params"]["initial_cash"] == 2500.0


def test_normalize_launch_request_rejects_invalid_sweep_payload():
    try:
        research_ui_server._normalize_launch_request(
            {
                "command": "sweep",
                "params": {},
            }
        )
    except ValueError as exc:
        assert "config_path" in str(exc)
    else:
        raise AssertionError("Expected invalid sweep payload to raise ValueError")


def test_build_launch_control_payload_reports_supported_commands(tmp_path: Path):
    payload, status = research_ui_server.build_launch_control_payload(tmp_path)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["supported_commands"] == ["run", "sweep"]
    assert payload["jobs"] == []


def test_launch_quantlab_job_registers_running_job(tmp_path: Path, monkeypatch):
    class _FakeProcess:
        pid = 4321

        @staticmethod
        def poll():
            return None

    def _fake_popen(command, cwd, stdout, stderr, text):  # noqa: ANN001
        assert command[1] == "main.py"
        assert "--json-request" in command
        assert cwd == tmp_path
        return _FakeProcess()

    monkeypatch.setattr(research_ui_server, "_resolve_quantlab_python", lambda root: root / ".venv" / "Scripts" / "python.exe")
    monkeypatch.setattr(research_ui_server.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(research_ui_server, "LAUNCH_JOBS", [])

    response, status = research_ui_server.launch_quantlab_job(
        tmp_path,
        {
            "command": "run",
            "params": {
                "ticker": "BTC-USD",
                "start": "2024-01-01",
                "end": "2024-06-30",
            },
        },
    )

    assert status == 202
    assert response["status"] == "accepted"
    assert response["job"]["status"] == "running"
    assert response["job"]["command"] == "run"
    assert response["job"]["stdout_href"].startswith("/outputs/research_ui/launches/")


def test_removed_workspace_helpers_are_absent_from_research_ui():
    removed_provider = "step" + "bit"
    assert not hasattr(research_ui_server, f"build_{removed_provider}_workspace_payload")
    assert not hasattr(research_ui_server, f"start_{removed_provider}_workspace")


def test_get_local_api_token_from_env(monkeypatch):
    """Test that get_local_api_token reads from environment."""
    monkeypatch.setenv("QUANTLAB_LOCAL_API_TOKEN", "test_token_123")
    token = research_ui_server.get_local_api_token()
    assert token == "test_token_123"


def test_get_local_api_token_empty_when_not_set(monkeypatch):
    """Test that get_local_api_token returns empty string when not set."""
    monkeypatch.delenv("QUANTLAB_LOCAL_API_TOKEN", raising=False)
    token = research_ui_server.get_local_api_token()
    assert token == ""


def test_max_json_body_bytes_constant_is_set():
    """Test that MAX_JSON_BODY_BYTES constant is defined."""
    assert research_ui_server.MAX_JSON_BODY_BYTES == 64 * 1024


def test_dashboard_handler_has_required_methods():
    """Test that DashboardHandler has all required validation methods."""
    handler_class = research_ui_server.DashboardHandler
    assert hasattr(handler_class, "_require_sensitive_post_auth")
    assert hasattr(handler_class, "_origin_is_local")
    assert hasattr(handler_class, "_validate_json_request")
    assert hasattr(handler_class, "_read_json_body")


# ── Headless handler harness ──────────────────────────────────────────────────

class _HeadlessHandler(research_ui_server.DashboardHandler):
    """DashboardHandler with all network I/O stubbed for unit tests.

    Does NOT call BaseHTTPRequestHandler.__init__ (that requires a live socket).
    Only the methods under test are exercised; everything else is stubbed.
    """

    def __init__(self, headers: dict | None = None) -> None:  # noqa: D107
        # Bypass the socket-dependent parent __init__ entirely.
        self._headers_in: dict = headers or {}
        self._response_code: int | None = None
        self._error_code: int | None = None
        self._error_msg: str | None = None
        self._sent_headers: list[tuple[str, str]] = []
        self.wfile: io.BytesIO = io.BytesIO()
        self.rfile: io.BytesIO = io.BytesIO()

    class _Headers:
        def __init__(self, d: dict) -> None:
            self._d = d

        def get(self, key: str, default=None):  # type: ignore[override]
            return self._d.get(key, default)

    @property
    def headers(self):  # type: ignore[override]
        return self._Headers(self._headers_in)

    def send_response(self, code, message=None) -> None:  # type: ignore[override]
        self._response_code = code

    def send_error(self, code, message=None) -> None:  # type: ignore[override]
        self._error_code = code
        self._error_msg = message

    def send_header(self, keyword, value) -> None:  # type: ignore[override]
        self._sent_headers.append((keyword, value))

    def end_headers(self) -> None:  # type: ignore[override]
        pass

    def guess_type(self, path) -> str:  # type: ignore[override]
        p = str(path)
        if p.endswith(".html"):
            return "text/html"
        if p.endswith(".css"):
            return "text/css"
        return "application/octet-stream"

    def log_message(self, format, *args) -> None:  # noqa: A002
        pass  # suppress output during tests


# ── Session bootstrap tests ───────────────────────────────────────────────────

def test_generate_research_ui_session_returns_nonempty_string():
    """_generate_research_ui_session produces a non-trivial token."""
    token = research_ui_server._generate_research_ui_session()
    assert isinstance(token, str)
    assert len(token) > 20


def test_get_or_create_research_ui_session_is_stable_within_process(monkeypatch):
    """Same process returns the same session token after first creation."""
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", "")
    first = research_ui_server._get_or_create_research_ui_session()
    second = research_ui_server._get_or_create_research_ui_session()
    assert first == second
    assert len(first) > 20


# ── Set-Cookie emission tests ─────────────────────────────────────────────────

def test_serve_research_ui_index_emits_set_cookie(tmp_path: Path, monkeypatch):
    """GET /research_ui/index.html must emit exactly one Set-Cookie header."""
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(research_ui_server, "RESEARCH_UI_STATIC_ROOT", tmp_path)
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", "")

    handler = _HeadlessHandler()
    handler._serve_research_ui_static("/research_ui/index.html")

    cookie_headers = [v for k, v in handler._sent_headers if k == "Set-Cookie"]
    assert len(cookie_headers) == 1, "Expected exactly one Set-Cookie header"


def test_serve_research_ui_index_cookie_has_required_attributes(tmp_path: Path, monkeypatch):
    """The emitted cookie must carry HttpOnly, SameSite=Strict, Path=/, QUANTLAB_SESSION=."""
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(research_ui_server, "RESEARCH_UI_STATIC_ROOT", tmp_path)
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", "")

    handler = _HeadlessHandler()
    handler._serve_research_ui_static("/research_ui/index.html")

    cookie_headers = [v for k, v in handler._sent_headers if k == "Set-Cookie"]
    assert cookie_headers, "Expected a Set-Cookie header"
    cookie = cookie_headers[0]
    assert "QUANTLAB_SESSION=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Strict" in cookie
    assert "Path=/" in cookie
    # No Max-Age / Expires: intentional session-only cookie
    assert "Max-Age" not in cookie
    assert "Expires" not in cookie


def test_serve_research_ui_index_cookie_does_not_contain_api_token(tmp_path: Path, monkeypatch):
    """The Set-Cookie value must never contain QUANTLAB_LOCAL_API_TOKEN."""
    secret = "super_secret_desktop_token_xyz"
    monkeypatch.setenv("QUANTLAB_LOCAL_API_TOKEN", secret)
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(research_ui_server, "RESEARCH_UI_STATIC_ROOT", tmp_path)
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", "")

    handler = _HeadlessHandler()
    handler._serve_research_ui_static("/research_ui/index.html")

    cookie_headers = [v for k, v in handler._sent_headers if k == "Set-Cookie"]
    assert cookie_headers, "Expected a Set-Cookie header"
    assert secret not in cookie_headers[0], "API token must not appear in Set-Cookie"


def test_serve_research_ui_static_asset_does_not_emit_set_cookie(tmp_path: Path, monkeypatch):
    """Static assets (CSS, JS) must not trigger a Set-Cookie header."""
    (tmp_path / "styles.css").write_text("body {}", encoding="utf-8")
    monkeypatch.setattr(research_ui_server, "RESEARCH_UI_STATIC_ROOT", tmp_path)

    handler = _HeadlessHandler()
    handler._serve_research_ui_static("/research_ui/styles.css")

    cookie_headers = [v for k, v in handler._sent_headers if k == "Set-Cookie"]
    assert cookie_headers == [], "Static assets must not emit Set-Cookie"


# ── _require_sensitive_post_auth tests ────────────────────────────────────────

def test_require_sensitive_post_auth_accepts_valid_header_token(monkeypatch):
    """Desktop path: a correct X-QuantLab-Token header must be accepted."""
    token = "valid_desktop_token_abc123"
    monkeypatch.setenv("QUANTLAB_LOCAL_API_TOKEN", token)
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", "")

    handler = _HeadlessHandler(headers={"X-QuantLab-Token": token})
    result = handler._require_sensitive_post_auth()

    assert result is True
    assert handler._error_code is None


def test_require_sensitive_post_auth_accepts_valid_session_cookie(monkeypatch):
    """Browser path: a correct QUANTLAB_SESSION cookie must be accepted."""
    session = "valid_session_token_abc123"
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", session)
    monkeypatch.delenv("QUANTLAB_LOCAL_API_TOKEN", raising=False)

    handler = _HeadlessHandler(headers={"Cookie": f"QUANTLAB_SESSION={session}"})
    result = handler._require_sensitive_post_auth()

    assert result is True
    assert handler._error_code is None


def test_require_sensitive_post_auth_rejects_invalid_cookie(monkeypatch):
    """A wrong cookie value must result in 401 — not fall through silently."""
    session = "valid_session_token_abc123"
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", session)
    monkeypatch.delenv("QUANTLAB_LOCAL_API_TOKEN", raising=False)

    handler = _HeadlessHandler(headers={"Cookie": "QUANTLAB_SESSION=wrong_token_value"})
    result = handler._require_sensitive_post_auth()

    assert result is False
    assert handler._error_code == 401


def test_require_sensitive_post_auth_rejects_no_token_no_cookie(monkeypatch):
    """Base case: neither header token nor cookie present must yield 401."""
    monkeypatch.delenv("QUANTLAB_LOCAL_API_TOKEN", raising=False)
    # Even with a valid session in memory, an empty request has no credentials.
    monkeypatch.setattr(research_ui_server, "_RESEARCH_UI_SESSION_TOKEN", "some_valid_session")

    handler = _HeadlessHandler(headers={})
    result = handler._require_sensitive_post_auth()

    assert result is False
    assert handler._error_code == 401
