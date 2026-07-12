import http.server
import json
import socketserver
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from urllib.parse import unquote
from uuid import uuid4

PORT = 8000
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESEARCH_UI_STATIC_ROOT = PROJECT_ROOT / "research_ui"
MAX_JSON_BODY_BYTES = 64 * 1024
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def get_local_api_token() -> str:
    return os.environ.get("QUANTLAB_LOCAL_API_TOKEN", "").strip()


# Session management for browser-based research_ui access
_RESEARCH_UI_SESSION_TOKEN: str = ""
_RESEARCH_UI_SESSION_LOCK = Lock()


def _generate_research_ui_session() -> str:
    """Generate a new ephemeral session token for browser access."""
    return secrets.token_urlsafe(32)


def _get_or_create_research_ui_session() -> str:
    """Get existing session or create a new one (single per process)."""
    global _RESEARCH_UI_SESSION_TOKEN
    with _RESEARCH_UI_SESSION_LOCK:
        if not _RESEARCH_UI_SESSION_TOKEN:
            _RESEARCH_UI_SESSION_TOKEN = _generate_research_ui_session()
        return _RESEARCH_UI_SESSION_TOKEN


LAUNCH_HISTORY_LIMIT = 12
LAUNCH_JOBS: list[dict[str, object]] = []
LAUNCH_LOCK = Lock()

from quantlab.cli.broker_order_validations import (
    build_broker_submission_alerts,
    build_broker_submission_health,
)
from quantlab.cli.hyperliquid_submit_sessions import (
    build_hyperliquid_submission_alerts,
    build_hyperliquid_submission_health,
)
from quantlab.cli.paper_sessions import (
    DEFAULT_PAPER_STALE_MINUTES,
    build_paper_sessions_alerts,
    build_paper_sessions_health,
)
from quantlab.pretrade.handoff import (
    PRETRADE_HANDOFF_VALIDATION_CONTRACT_TYPE,
    PRETRADE_HANDOFF_VALIDATION_FILENAME,
)

META_TRADE_PRODUCT_SURFACE_SPECS = [
    {
        "id": "risk_calculator",
        "label": "Risk Calculator",
        "category": "Workspace",
        "path": "index.html",
        "summary": "Browser workbench for capital, risk, entry, stop, target, fees, and slippage.",
    },
    {
        "id": "scenario_comparison",
        "label": "Scenario Comparison",
        "category": "Workspace",
        "path": "web/risk-ui.js",
        "summary": "Saved scenarios table with comparison workflow and persistence.",
    },
    {
        "id": "history",
        "label": "Trade History",
        "category": "Workspace",
        "path": "web/risk-ui.js",
        "summary": "Searchable history with strategy, notes, filters, and timestamps.",
    },
    {
        "id": "trade_plan_exports",
        "label": "Trade Plan Exports",
        "category": "Exports",
        "path": "web/shared.js",
        "summary": "JSON and CSV exports for deterministic trade-plan serialization.",
    },
    {
        "id": "quantlab_handoff",
        "label": "QuantLab Handoff Export",
        "category": "Exports",
        "path": "cli/trade-plan.js",
        "summary": "Bounded handoff generation for downstream QuantLab intake.",
    },
    {
        "id": "mini_backtester",
        "label": "Mini Backtester",
        "category": "Analysis",
        "path": "web/backtest-ui.js",
        "summary": "Visual moving-average backtester with signals, trades, and equity curve.",
    },
]

META_TRADE_ENGINE_MODULE_SPECS = [
    {
        "id": "risk_core_js",
        "label": "Shared JS Risk Core",
        "category": "Core",
        "path": "risk-core.js",
        "summary": "Canonical trade-plan generation and deterministic serialization in JavaScript.",
    },
    {
        "id": "browser_shared",
        "label": "Browser Shared Utilities",
        "category": "Browser",
        "path": "web/shared.js",
        "summary": "Formatting, form reading, persistence, CSV helpers, and file downloads.",
    },
    {
        "id": "browser_risk_ui",
        "label": "Risk UI Module",
        "category": "Browser",
        "path": "web/risk-ui.js",
        "summary": "Main calculator, scenarios, history, and export interactions.",
    },
    {
        "id": "browser_backtester",
        "label": "Backtester Module",
        "category": "Browser",
        "path": "web/backtest-ui.js",
        "summary": "Client-side analytical backtester and chart rendering surface.",
    },
    {
        "id": "browser_bootstrap",
        "label": "Browser Bootstrap",
        "category": "Browser",
        "path": "web/main.js",
        "summary": "Final web bootstrap that wires the bounded browser app together.",
    },
    {
        "id": "headless_cli",
        "label": "Headless CLI",
        "category": "CLI",
        "path": "cli/trade-plan.js",
        "summary": "DOM-free deterministic CLI path for plans and QuantLab handoffs.",
    },
    {
        "id": "cpp_engine",
        "label": "C++ Engine",
        "category": "Parity",
        "path": "cpp/risk_engine.cpp",
        "summary": "Alternate runtime for parity, cross-validation, and deterministic calculations.",
    },
    {
        "id": "cpp_trade_runner",
        "label": "C++ Trade Plan Runner",
        "category": "Parity",
        "path": "cpp/trade_plan_runner.cpp",
        "summary": "Cross-runtime runner for canonical trade-plan parity checks.",
    },
]

META_TRADE_VALIDATION_SURFACES = [
    {
        "id": "js_tests",
        "label": "JS Core Tests",
        "category": "Tests",
        "path": "tests/run_js_tests.js",
        "summary": "Baseline verification for JavaScript risk and trade-plan flows.",
    },
    {
        "id": "cli_tests",
        "label": "CLI Tests",
        "category": "Tests",
        "path": "tests/run_cli_tests.js",
        "summary": "Headless CLI verification without depending on the browser surface.",
    },
    {
        "id": "contract_fixture_tests",
        "label": "Contract Fixture Tests",
        "category": "Tests",
        "path": "tests/run_contract_fixture_tests.js",
        "summary": "Checks deterministic handoff artifacts against canonical fixtures.",
    },
    {
        "id": "cross_runtime_tests",
        "label": "JS/C++ Parity Tests",
        "category": "Parity",
        "path": "tests/run_cross_tests.js",
        "summary": "Cross-runtime parity checks for calculation metrics between JS and C++.",
    },
    {
        "id": "trade_plan_parity",
        "label": "Trade Plan Parity",
        "category": "Parity",
        "path": "tests/run_trade_plan_cross_tests.js",
        "summary": "Trade-plan parity checks between JavaScript and C++ runners.",
    },
    {
        "id": "ui_smoke",
        "label": "UI Smoke Tests",
        "category": "Tests",
        "path": "tests/ui/risk-calculator.spec.js",
        "summary": "Browser smoke coverage for the main workbench interaction path.",
    },
    {
        "id": "ci_contract_parity",
        "label": "Contract & Parity CI",
        "category": "CI",
        "path": ".github/workflows/contract-parity-ci.yml",
        "summary": "CI workflow enforcing contract stability and cross-runtime parity.",
    },
]

META_TRADE_CONTRACT_ARTIFACTS = [
    {
        "id": "workbench_roadmap",
        "label": "Workbench Roadmap",
        "category": "Docs",
        "path": "docs/pretrade-workbench-roadmap.md",
        "summary": "Repository purpose, boundary, and critical path for upstream planning.",
    },
    {
        "id": "quantlab_handoff_contract",
        "label": "QuantLab Handoff Contract",
        "category": "Docs",
        "path": "docs/quantlab-handoff-contract.md",
        "summary": "Bounded contract for the downstream QuantLab handoff JSON.",
    },
    {
        "id": "handoff_example",
        "label": "Handoff Example Request",
        "category": "Examples",
        "path": "examples/quantlab_handoff_request.json",
        "summary": "Example request used for deterministic headless handoff generation.",
    },
    {
        "id": "handoff_fixture",
        "label": "Expected QuantLab Handoff",
        "category": "Fixtures",
        "path": "tests/fixtures/expected_quantlab_handoff.json",
        "summary": "Canonical fixture for validating the emitted QuantLab handoff artifact.",
    },
]


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        request_path = unquote(self.path.split("?", 1)[0].split("#", 1)[0])
        meta_trade_repo = _resolve_meta_trade_repo(PROJECT_ROOT)
        if request_path == '/external/meta-trade' or request_path.startswith('/external/meta-trade/'):
            return self._serve_external_static(meta_trade_repo, '/external/meta-trade/', request_path)
        if request_path.startswith('/api/paper-sessions-health'):
            payload, status = build_paper_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/paper-sessions-alerts'):
            payload, status = build_paper_alerts_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/broker-submissions-health'):
            payload, status = build_broker_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/hyperliquid-surface'):
            payload, status = build_hyperliquid_surface_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/pretrade-handoff-intake'):
            payload, status = build_pretrade_handoff_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/meta-trade-workspace'):
            payload, status = build_meta_trade_workspace_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/launch-control'):
            payload, status = build_launch_control_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)

        # Redirect root to research_ui/index.html to ensure relative asset paths work
        if request_path == '/' or request_path == '':
            self.send_response(302)
            self.send_header('Location', '/research_ui/index.html')
            self.end_headers()
            return
        if request_path == '/research_ui':
            self.send_response(302)
            self.send_header('Location', '/research_ui/index.html')
            self.end_headers()
            return
        if request_path.startswith('/research_ui/'):
            return self._serve_research_ui_static(request_path)
        self.send_error(404, "Not found")

    def do_POST(self):
        request_path = unquote(self.path.split("?", 1)[0].split("#", 1)[0])
        if request_path != "/api/launch-control":
            self.send_error(404, "Not found")
            return

        if not self._origin_is_local():
            self.send_error(403, "Forbidden")
            return

        if not self._require_sensitive_post_auth():
            return

        content_length = self._validate_json_request()
        if content_length is None:
            return

        try:
            body = self._read_json_body(content_length)
        except ValueError as exc:
            return self._send_json({"status": "error", "message": str(exc)}, status=400)

        try:
            job_payload, status = launch_quantlab_job(PROJECT_ROOT, body)
            return self._send_json(job_payload, status=status)
        except ValueError as exc:
            return self._send_json({"status": "error", "message": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"status": "error", "message": str(exc)}, status=500)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _require_sensitive_post_auth(self) -> bool:
        """Validate POST auth: accept either desktop token header OR browser session cookie."""

        # Path 1: Desktop - X-QuantLab-Token header
        provided_header = (self.headers.get("X-QuantLab-Token") or "").strip()
        expected_token = get_local_api_token()

        if provided_header and expected_token:
            if secrets.compare_digest(provided_header, expected_token):
                return True

        # Path 2: Browser - QUANTLAB_SESSION cookie
        cookie_header = (self.headers.get("Cookie") or "").strip()
        if cookie_header:
            for part in cookie_header.split(";"):
                part = part.strip()
                if part.startswith("QUANTLAB_SESSION="):
                    session_value = part[len("QUANTLAB_SESSION=") :].strip()
                    valid_session = _get_or_create_research_ui_session()
                    if secrets.compare_digest(session_value, valid_session):
                        return True

        # Neither valid token nor valid session
        self.send_error(401, "Unauthorized")
        return False

    def _origin_is_local(self):
        origin = (self.headers.get("Origin") or "").strip().lower()
        host = (self.headers.get("Host") or "").strip().lower()
        allowed_origin_prefixes = ("http://127.0.0.1:", "http://localhost:", "http://[::1]:")
        allowed_host_prefixes = ("127.0.0.1:", "localhost:", "[::1]:")

        if origin and origin != "null":
            if not origin.startswith(allowed_origin_prefixes):
                return False

        if host and not host.startswith(allowed_host_prefixes):
            return False

        return True

    def _validate_json_request(self):
        content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self.send_error(415, "Content-Type must be application/json")
            return None

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return None

        if content_length <= 0:
            self.send_error(400, "Request body is required")
            return None

        if content_length > MAX_JSON_BODY_BYTES:
            self.send_error(413, "Request body too large")
            return None

        return content_length

    def _read_json_body(self, content_length: int):
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError("Request body must be valid UTF-8.") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON body: {exc.msg}") from exc

        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")

        return payload

    def _serve_external_static(self, repo_root: Path, prefix: str, request_path: str):
        relative_path = request_path[len(prefix):].lstrip("/")
        repo_root_resolved = repo_root.resolve()
        target = (repo_root_resolved / relative_path) if relative_path else (repo_root_resolved / "index.html")

        try:
            target = target.resolve()
            target.relative_to(repo_root_resolved)
        except Exception:  # noqa: BLE001
            self.send_error(403, "Forbidden")
            return

        if target.is_dir():
            target = target / "index.html"

        if not target.exists() or not target.is_file():
            self.send_error(404, "File not found")
            return

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_research_ui_static(self, request_path: str):
        relative_path = request_path[len('/research_ui/'):].lstrip('/')
        root_resolved = RESEARCH_UI_STATIC_ROOT.resolve()
        target = (root_resolved / relative_path) if relative_path else (root_resolved / "index.html")

        try:
            target = target.resolve()
            relative_parts = target.relative_to(root_resolved).parts
        except Exception:  # noqa: BLE001
            self.send_error(403, "Forbidden")
            return

        if any(part.startswith('.') for part in relative_parts):
            self.send_error(403, "Forbidden")
            return

        if target.is_dir():
            target = target / "index.html"

        if not target.exists() or not target.is_file():
            self.send_error(404, "File not found")
            return

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # Bootstrap session cookie — emitted only on the real research_ui entry points.
        # No Max-Age / Expires is intentional: this is a browser-session-only cookie
        # that expires when the browser session ends. Do not add persistence here.
        _RESEARCH_UI_ENTRY_PATHS = frozenset({
            "/research_ui/",
            "/research_ui/index.html",
        })
        if request_path in _RESEARCH_UI_ENTRY_PATHS and target.name == "index.html":
            session_token = _get_or_create_research_ui_session()
            cookie_value = (
                f"QUANTLAB_SESSION={session_token}; HttpOnly; SameSite=Strict; Path=/"
            )
            self.send_header("Set-Cookie", cookie_value)
        self.end_headers()
        self.wfile.write(body)


def build_paper_health_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    paper_root = root / "outputs" / "paper_sessions"

    if not paper_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(paper_root),
            "message": "No paper session root found yet.",
            "total_sessions": 0,
            "status_counts": {},
            "latest_session_id": None,
            "latest_session_status": None,
            "latest_session_at": None,
            "latest_issue_session_id": None,
            "latest_issue_status": None,
            "latest_issue_at": None,
            "latest_issue_error_type": None,
        }, 200

    try:
        payload = build_paper_sessions_health(paper_root)
        payload["status"] = "ok"
        payload["available"] = True
        return payload, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(paper_root),
            "message": str(exc),
        }, 500


def build_paper_alerts_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    paper_root = root / "outputs" / "paper_sessions"

    if not paper_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(paper_root),
            "message": "No paper session root found yet.",
            "generated_at": None,
            "stale_after_minutes": DEFAULT_PAPER_STALE_MINUTES,
            "total_sessions": 0,
            "status_counts": {},
            "running_sessions": [],
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "latest_success_session_id": None,
            "latest_success_at": None,
            "latest_alert_session_id": None,
            "latest_alert_code": None,
            "latest_alert_at": None,
            "alerts": [],
        }, 200

    try:
        payload = build_paper_sessions_alerts(paper_root)
        payload["status"] = "ok"
        payload["available"] = True
        return payload, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(paper_root),
            "message": str(exc),
        }, 500


def build_broker_health_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    broker_root = root / "outputs" / "broker_order_validations"

    if not broker_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(broker_root),
            "message": "No broker order-validation root found yet.",
            "total_sessions": 0,
            "approved_sessions": 0,
            "submit_gate_sessions": 0,
            "submit_response_sessions": 0,
            "submitted_sessions": 0,
            "order_status_known_sessions": 0,
            "status_counts": {},
            "submit_state_counts": {},
            "order_state_counts": {},
            "latest_submit_session_id": None,
            "latest_submit_state": None,
            "latest_order_state": None,
            "latest_submit_at": None,
            "latest_issue_session_id": None,
            "latest_issue_code": None,
            "latest_issue_at": None,
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "alerts": [],
        }, 200

    try:
        health = build_broker_submission_health(broker_root)
        alerts = build_broker_submission_alerts(broker_root)
        return {
            **health,
            "status": "ok",
            "available": True,
            "alert_status": alerts.get("alert_status", "ok"),
            "has_alerts": alerts.get("has_alerts", False),
            "alert_counts": alerts.get("alert_counts", {}),
            "alerts": alerts.get("alerts", []),
        }, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(broker_root),
            "message": str(exc),
        }, 500


def build_hyperliquid_surface_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    submit_root = root / "outputs" / "hyperliquid_submits"
    search_roots = [
        root / "outputs",
        root / "tmp",
        root.parent / "tmp",
    ]

    surfaces = {
        "preflight": {
            "implemented": True,
            "artifact_name": "broker_preflight.json",
            "summary_key": "market_supported",
        },
        "account_readiness": {
            "implemented": True,
            "artifact_name": "hyperliquid_account_readiness.json",
            "summary_key": "readiness_allowed",
        },
        "signed_action": {
            "implemented": True,
            "artifact_name": "hyperliquid_signed_action.json",
            "summary_key": "readiness_allowed",
        },
        "submit_response": {
            "implemented": True,
            "artifact_name": "hyperliquid_submit_response.json",
            "summary_key": "submit_state",
        },
        "order_status": {
            "implemented": True,
            "artifact_name": "hyperliquid_order_status.json",
            "summary_key": "normalized_state",
        },
        "continuous_supervision": {
            "implemented": True,
            "artifact_name": "hyperliquid_supervision.json",
            "summary_key": "supervision_state",
        },
    }

    latest_artifacts: dict[str, dict[str, object] | None] = {}
    for key, spec in surfaces.items():
        latest_artifacts[key] = _find_latest_hyperliquid_artifact(
            search_roots,
            spec["artifact_name"],
        )

    latest_ready_artifact = next(
        (
            artifact
            for artifact in (
                latest_artifacts["continuous_supervision"],
                latest_artifacts["order_status"],
                latest_artifacts["submit_response"],
                latest_artifacts["signed_action"],
                latest_artifacts["account_readiness"],
                latest_artifacts["preflight"],
            )
            if artifact
        ),
        None,
    )

    if submit_root.exists():
        try:
            submit_health = build_hyperliquid_submission_health(submit_root)
            submit_alerts = build_hyperliquid_submission_alerts(submit_root)
        except Exception as exc:  # noqa: BLE001
            submit_health = {
                "root_dir": str(submit_root),
                "message": str(exc),
                "total_sessions": 0,
                "submit_response_sessions": 0,
                "supervision_sessions": 0,
                "submitted_sessions": 0,
                "order_status_known_sessions": 0,
                "status_counts": {},
                "submit_state_counts": {},
                "order_state_counts": {},
                "latest_submit_session_id": None,
                "latest_submit_state": None,
                "latest_order_state": None,
                "latest_submit_at": None,
                "latest_issue_session_id": None,
                "latest_issue_code": None,
                "latest_issue_at": None,
            }
            submit_alerts = {
                "root_dir": str(submit_root),
                "message": str(exc),
                "generated_at": None,
                "total_sessions": 0,
                "submit_response_sessions": 0,
                "supervision_sessions": 0,
                "submitted_sessions": 0,
                "order_state_counts": {},
                "alert_status": "error",
                "has_alerts": False,
                "alert_counts": {},
                "latest_alert_session_id": None,
                "latest_alert_code": None,
                "latest_alert_at": None,
                "alerts": [],
            }
    else:
        submit_health = {
            "root_dir": str(submit_root),
            "message": "No Hyperliquid submit root found yet.",
            "total_sessions": 0,
            "submit_response_sessions": 0,
            "supervision_sessions": 0,
            "submitted_sessions": 0,
            "order_status_known_sessions": 0,
            "status_counts": {},
            "submit_state_counts": {},
            "order_state_counts": {},
            "latest_submit_session_id": None,
            "latest_submit_state": None,
            "latest_order_state": None,
            "latest_submit_at": None,
            "latest_issue_session_id": None,
            "latest_issue_code": None,
            "latest_issue_at": None,
        }
        submit_alerts = {
            "root_dir": str(submit_root),
            "generated_at": None,
            "total_sessions": 0,
            "submit_response_sessions": 0,
            "supervision_sessions": 0,
            "submitted_sessions": 0,
            "order_state_counts": {},
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "latest_alert_session_id": None,
            "latest_alert_code": None,
            "latest_alert_at": None,
            "alerts": [],
        }

    return {
        "status": "ok",
        "available": True,
        "message": "Hyperliquid now spans venue preflight, signer readiness, local signing, supervised submit, and bounded post-submit supervision.",
        "search_roots": [str(path) for path in search_roots if path.exists()],
        "implemented_surfaces": {
            "preflight": True,
            "account_readiness": True,
            "signed_action_build": True,
            "cryptographic_signing": True,
            "order_submit": True,
            "submit_sessions": True,
            "post_submit_status": True,
            "continuous_supervision": True,
            "submission_health": True,
        },
        "execution_context_pressure": {
            "signer_identity": True,
            "routing_target": True,
            "transport_preference": True,
            "nonce_hint": True,
            "expires_after": True,
        },
        "submit_sessions_available": submit_root.exists(),
        "submit_sessions_root": str(submit_root),
        "submit_health": submit_health,
        "submit_alert_status": submit_alerts.get("alert_status", "ok"),
        "submit_has_alerts": submit_alerts.get("has_alerts", False),
        "submit_alert_counts": submit_alerts.get("alert_counts", {}),
        "submit_alerts": submit_alerts.get("alerts", []),
        "latest_artifacts": latest_artifacts,
        "latest_ready_artifact_type": latest_ready_artifact.get("artifact_type") if latest_ready_artifact else None,
        "latest_ready_generated_at": latest_ready_artifact.get("generated_at") if latest_ready_artifact else None,
        "signature_state": (
            latest_artifacts["signed_action"].get("signature_state")
            if latest_artifacts["signed_action"]
            else "pending_local_artifact"
        ),
    }, 200


def build_pretrade_handoff_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    pretrade_root = root / "outputs" / "pretrade_handoff"

    base_payload = {
        "status": "ok",
        "available": pretrade_root.exists(),
        "has_validation": False,
        "root_dir": str(pretrade_root),
        "surface_model": "read_only_validation_intake",
        "planner_surface": "external_calculator",
        "boundary_note": (
            "The calculator proposes. QuantLab validates, decides, and executes. "
            "This panel remains read-only."
        ),
        "message": None,
    }

    if not pretrade_root.exists():
        return {
            **base_payload,
            "message": "No pre-trade handoff validation root found yet.",
            "latest_validation_path": None,
            "latest_validation_href": None,
            "source_artifact_path": None,
            "source_artifact_href": None,
            "validation_state": "empty",
            "accepted": None,
            "reasons": [],
            "handoff_id": None,
            "symbol": None,
            "venue": None,
            "side": None,
            "planner": None,
            "ready_for_draft_execution_intent": None,
            "hinted_ready_for_draft_execution_intent": None,
            "missing_fields": [],
            "generated_at": None,
        }, 200

    latest_validation = _find_latest_pretrade_validation(pretrade_root, root)
    if latest_validation is None:
        return {
            **base_payload,
            "available": True,
            "message": "No pre-trade handoff validation artifact has been persisted yet.",
            "latest_validation_path": None,
            "latest_validation_href": None,
            "source_artifact_path": None,
            "source_artifact_href": None,
            "validation_state": "empty",
            "accepted": None,
            "reasons": [],
            "handoff_id": None,
            "symbol": None,
            "venue": None,
            "side": None,
            "planner": None,
            "ready_for_draft_execution_intent": None,
            "hinted_ready_for_draft_execution_intent": None,
            "missing_fields": [],
            "generated_at": None,
        }, 200

    payload = latest_validation["payload"]
    return {
        **base_payload,
        "available": True,
        "has_validation": True,
        "message": "Latest bounded pre-trade handoff validation loaded from local QuantLab artifacts.",
        "latest_validation_path": latest_validation["path"],
        "latest_validation_href": latest_validation["href"],
        "source_artifact_path": payload.get("source_artifact_path"),
        "source_artifact_href": _build_local_artifact_href(payload.get("source_artifact_path"), root),
        "validation_state": "accepted" if payload.get("accepted") else "rejected",
        "accepted": bool(payload.get("accepted")),
        "reasons": payload.get("reasons") if isinstance(payload.get("reasons"), list) else [],
        "handoff_id": payload.get("handoff_contract", {}).get("handoff_id"),
        "handoff_generated_at": payload.get("handoff_contract", {}).get("generated_at"),
        "handoff_contract_type": payload.get("handoff_contract", {}).get("contract_type"),
        "handoff_contract_version": payload.get("handoff_contract", {}).get("contract_version"),
        "symbol": payload.get("pretrade_context", {}).get("symbol"),
        "venue": payload.get("pretrade_context", {}).get("venue"),
        "side": payload.get("pretrade_context", {}).get("side"),
        "planner": payload.get("source", {}).get("planner"),
        "ready_for_draft_execution_intent": payload.get("quantlab_boundary", {}).get(
            "ready_for_draft_execution_intent"
        ),
        "hinted_ready_for_draft_execution_intent": payload.get("quantlab_hints", {}).get(
            "ready_for_draft_execution_intent"
        ),
        "missing_fields": payload.get("quantlab_hints", {}).get("missing_fields", []),
        "generated_at": payload.get("generated_at"),
        "policy_owner": payload.get("quantlab_boundary", {}).get("policy_owner"),
        "execution_authority": payload.get("quantlab_boundary", {}).get("execution_authority"),
        "submit_authority": payload.get("quantlab_boundary", {}).get("submit_authority"),
        "quantlab_boundary_note": payload.get("quantlab_hints", {}).get("boundary_note"),
    }, 200


def build_meta_trade_workspace_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    repo = _resolve_meta_trade_repo(root)
    repo_summary = _build_workspace_repo_summary(repo, "pretrade_workbench")
    product_surfaces = _build_meta_trade_entries(repo, META_TRADE_PRODUCT_SURFACE_SPECS)
    product_surface_groups = _group_workspace_entries(
        product_surfaces,
        {
            "Workspace": "Operator-facing planning surfaces that stay upstream of QuantLab.",
            "Exports": "Deterministic serialization and bounded handoff generation.",
            "Analysis": "Auxiliary analytical surfaces that support pre-trade work.",
        },
    )
    engine_modules = _build_meta_trade_entries(repo, META_TRADE_ENGINE_MODULE_SPECS)
    engine_module_groups = _group_workspace_entries(
        engine_modules,
        {
            "Core": "Canonical trade-plan generation and deterministic data structures.",
            "Browser": "Bounded browser modules for the workbench UI.",
            "CLI": "Headless workflow for reproducible trade-plan and handoff generation.",
            "Parity": "Cross-runtime C++ surfaces used for validation and drift control.",
        },
    )
    validation_surfaces = _build_meta_trade_entries(repo, META_TRADE_VALIDATION_SURFACES)
    validation_surface_groups = _group_workspace_entries(
        validation_surfaces,
        {
            "Tests": "Local verification flows for browser, core, and headless paths.",
            "Parity": "Cross-runtime checks to keep JavaScript and C++ aligned.",
            "CI": "Automation that enforces contract and parity confidence.",
        },
    )
    contract_artifacts = _build_meta_trade_entries(repo, META_TRADE_CONTRACT_ARTIFACTS)
    contract_artifact_groups = _group_workspace_entries(
        contract_artifacts,
        {
            "Docs": "Boundary and roadmap documents for the bounded upstream role.",
            "Examples": "Runnable examples for deterministic handoff generation.",
            "Fixtures": "Canonical artifacts consumed by validation and contract tests.",
        },
    )
    package_scripts = _read_package_scripts(repo)

    return {
        "status": "ok",
        "available": bool(repo_summary["present"]),
        "workspace_root": str(repo.parent),
        "boundary_mode": "upstream_pretrade_workbench" if repo_summary["present"] else "missing",
        "live_preview_url": "http://127.0.0.1:4173/",
        "boundary_note": (
            "meta_trade remains an upstream pre-trade workbench. It plans and exports "
            "deterministic artifacts. QuantLab validates, decides, and executes."
        ),
        "repo": repo_summary,
        "workspace_summary": {
            "product_surfaces_present": sum(1 for surface in product_surfaces if surface["present"]),
            "product_surfaces_total": len(product_surfaces),
            "engine_modules_present": sum(1 for module in engine_modules if module["present"]),
            "engine_modules_total": len(engine_modules),
            "validation_surfaces_present": sum(1 for surface in validation_surfaces if surface["present"]),
            "validation_surfaces_total": len(validation_surfaces),
            "contract_artifacts_present": sum(1 for artifact in contract_artifacts if artifact["present"]),
            "contract_artifacts_total": len(contract_artifacts),
            "package_script_total": len(package_scripts),
        },
        "product_surfaces": product_surfaces,
        "product_surface_groups": product_surface_groups,
        "engine_modules": engine_modules,
        "engine_module_groups": engine_module_groups,
        "validation_surfaces": validation_surfaces,
        "validation_surface_groups": validation_surface_groups,
        "contract_artifacts": contract_artifacts,
        "contract_artifact_groups": contract_artifact_groups,
        "package_scripts": package_scripts,
    }, 200


def build_launch_control_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    jobs = _snapshot_launch_jobs(root)
    return {
        "status": "ok",
        "available": True,
        "launcher_root": str(root / "outputs" / "research_ui" / "launches"),
        "python_path": str(_resolve_quantlab_python(root)),
        "supported_commands": ["run", "sweep"],
        "supported_run_fields": ["ticker", "start", "end", "interval", "paper", "initial_cash"],
        "supported_sweep_fields": ["config_path", "out_dir"],
        "jobs": jobs,
    }, 200


def launch_quantlab_job(project_root: Path, request_body: dict[str, object]) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    request_payload = _normalize_launch_request(request_body)
    request_id = request_payload["request_id"]

    launch_dir = root / "outputs" / "research_ui" / "launches" / request_id
    launch_dir.mkdir(parents=True, exist_ok=True)
    signal_file = launch_dir / "signals.jsonl"
    stdout_file = launch_dir / "stdout.log"
    stderr_file = launch_dir / "stderr.log"

    python_path = _resolve_quantlab_python(root)
    command = [
        str(python_path),
        "main.py",
        "--json-request",
        json.dumps(request_payload, ensure_ascii=False),
        "--signal-file",
        str(signal_file),
    ]

    stdout_handle = stdout_file.open("w", encoding="utf-8")
    stderr_handle = stderr_file.open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )
    finally:
        stdout_handle.close()
        stderr_handle.close()

    job = {
        "request_id": request_id,
        "command": request_payload["command"],
        "params": request_payload["params"],
        "status": "running",
        "started_at": _utc_now_iso(),
        "ended_at": None,
        "pid": process.pid,
        "process": process,
        "signal_file": str(signal_file),
        "stdout_path": str(stdout_file),
        "stderr_path": str(stderr_file),
        "artifacts_path": None,
        "report_path": None,
        "run_id": None,
        "error_message": None,
        "exit_code": None,
    }

    with LAUNCH_LOCK:
        LAUNCH_JOBS.insert(0, job)
        del LAUNCH_JOBS[LAUNCH_HISTORY_LIMIT:]

    snapshot = _serialize_launch_job(root, job)
    return {
        "status": "accepted",
        "message": f"{request_payload['command']} launch started.",
        "job": snapshot,
    }, 202


def _normalize_launch_request(request_body: dict[str, object]) -> dict[str, object]:
    command = str(request_body.get("command") or "").strip().lower()
    if command not in {"run", "sweep"}:
        raise ValueError("Only run and sweep are supported from the dashboard launcher.")

    raw_params = request_body.get("params") or {}
    if not isinstance(raw_params, dict):
        raise ValueError("Launcher params must be a JSON object.")

    request_id = str(request_body.get("request_id") or "").strip() or f"req_ui_{uuid4().hex[:12]}"

    if command == "run":
        ticker = str(raw_params.get("ticker") or "").strip()
        start = str(raw_params.get("start") or "").strip()
        end = str(raw_params.get("end") or "").strip()
        if not ticker or not start or not end:
            raise ValueError("Run launches require ticker, start, and end.")

        params: dict[str, object] = {
            "ticker": ticker,
            "start": start,
            "end": end,
        }
        interval = str(raw_params.get("interval") or "").strip()
        if interval:
            params["interval"] = interval
        if "paper" in raw_params:
            params["paper"] = bool(raw_params.get("paper"))
        initial_cash = raw_params.get("initial_cash")
        if initial_cash not in {None, ""}:
            params["initial_cash"] = float(initial_cash)
    else:
        config_path = str(raw_params.get("config_path") or raw_params.get("sweep") or "").strip()
        if not config_path:
            raise ValueError("Sweep launches require config_path.")
        params = {"config_path": config_path}
        out_dir = str(raw_params.get("out_dir") or raw_params.get("sweep_outdir") or "").strip()
        if out_dir:
            params["out_dir"] = out_dir

    return {
        "schema_version": "1.0",
        "request_id": request_id,
        "command": command,
        "params": params,
    }


def _snapshot_launch_jobs(project_root: Path) -> list[dict[str, object]]:
    root = Path(project_root or PROJECT_ROOT)
    with LAUNCH_LOCK:
        jobs = list(LAUNCH_JOBS)

    snapshots: list[dict[str, object]] = []
    for job in jobs:
        _refresh_launch_job(root, job)
        snapshots.append(_serialize_launch_job(root, job))
    return snapshots


def _refresh_launch_job(project_root: Path, job: dict[str, object]) -> None:
    process = job.get("process")
    if process is not None and getattr(process, "poll", None):
        exit_code = process.poll()
        if exit_code is None:
            return
        job["exit_code"] = exit_code

    if job.get("status") != "running":
        return

    signals = _read_signal_events(Path(str(job["signal_file"])))
    completed_event = next((event for event in reversed(signals) if event.get("event") == "SESSION_COMPLETED"), None)
    failed_event = next((event for event in reversed(signals) if event.get("event") == "SESSION_FAILED"), None)

    if completed_event:
        job["status"] = "succeeded"
        job["ended_at"] = completed_event.get("timestamp") or _utc_now_iso()
        job["run_id"] = completed_event.get("run_id")
        job["artifacts_path"] = completed_event.get("artifacts_path")
        job["report_path"] = completed_event.get("report_path")
        return

    if failed_event:
        job["status"] = "failed"
        job["ended_at"] = failed_event.get("timestamp") or _utc_now_iso()
        job["error_message"] = failed_event.get("message") or failed_event.get("error_type")
        job["run_id"] = failed_event.get("run_id")
        return

    if job.get("exit_code") is not None:
        job["status"] = "succeeded" if job["exit_code"] == 0 else "failed"
        job["ended_at"] = _utc_now_iso()
        if job["status"] == "failed" and not job.get("error_message"):
            stderr_tail = _tail_text_file(Path(str(job["stderr_path"])), max_chars=600)
            job["error_message"] = stderr_tail or f"QuantLab exited with code {job['exit_code']}."


def _serialize_launch_job(project_root: Path, job: dict[str, object]) -> dict[str, object]:
    root = Path(project_root or PROJECT_ROOT)
    status = str(job.get("status") or "unknown")
    artifacts_href = _project_relative_href(root, job.get("artifacts_path"))
    report_href = _project_relative_href(root, job.get("report_path"))
    stdout_href = _project_relative_href(root, job.get("stdout_path"))
    stderr_href = _project_relative_href(root, job.get("stderr_path"))
    summary = _summarize_launch_params(str(job.get("command") or ""), job.get("params") or {})

    return {
        "request_id": job.get("request_id"),
        "command": job.get("command"),
        "params": job.get("params"),
        "summary": summary,
        "status": status,
        "started_at": job.get("started_at"),
        "ended_at": job.get("ended_at"),
        "pid": job.get("pid"),
        "run_id": job.get("run_id"),
        "artifacts_path": job.get("artifacts_path"),
        "artifacts_href": artifacts_href,
        "report_path": job.get("report_path"),
        "report_href": report_href,
        "stdout_href": stdout_href,
        "stderr_href": stderr_href,
        "exit_code": job.get("exit_code"),
        "error_message": job.get("error_message"),
    }


def _summarize_launch_params(command: str, params: dict[str, object]) -> str:
    if command == "run":
        ticker = params.get("ticker") or "-"
        start = params.get("start") or "-"
        end = params.get("end") or "-"
        suffix = " · paper" if params.get("paper") else ""
        return f"{ticker} · {start} -> {end}{suffix}"
    config_path = params.get("config_path") or params.get("sweep") or "-"
    return f"Config {config_path}"


def _resolve_quantlab_python(project_root: Path) -> Path:
    root = Path(project_root or PROJECT_ROOT)
    candidates = [
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def _read_signal_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    events: list[dict[str, object]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                events.append(payload)
    except OSError:
        return []
    return events


def _tail_text_file(path: Path, max_chars: int = 400) -> str:
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    content = content.strip()
    return content[-max_chars:] if content else ""


def _project_relative_href(project_root: Path, maybe_path: object) -> str | None:
    if not maybe_path:
        return None
    path = Path(str(maybe_path))
    try:
        relative = path.resolve().relative_to(Path(project_root).resolve())
    except Exception:  # noqa: BLE001
        return None
    return "/" + str(relative).replace("\\", "/")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_workspace_repo_summary(path: Path, role: str) -> dict[str, object]:
    summary: dict[str, object] = {
        "present": path.exists() and path.is_dir(),
        "role": role,
        "path": str(path),
        "branch": None,
        "dirty": None,
        "headline": None,
    }
    if not summary["present"]:
        return summary

    branch, dirty = _read_git_branch_state(path)
    summary["branch"] = branch
    summary["dirty"] = dirty
    summary["headline"] = _read_readme_headline(path)
    return summary


def _resolve_meta_trade_repo(project_root: Path) -> Path:
    candidates = [
        project_root.parent / "meta_trade",
        project_root.parent.parent / "meta_trade",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return candidates[-1]


def _build_meta_trade_entries(repo: Path, specs: list[dict[str, str]]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for spec in specs:
        target = repo / spec["path"]
        entries.append(
            {
                **spec,
                "present": target.exists(),
                "path": str(target),
            }
        )
    return entries


def _read_package_scripts(repo: Path) -> list[dict[str, str]]:
    package_path = repo / "package.json"
    if not package_path.exists():
        return []

    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []

    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return []

    return [
        {
            "name": str(name),
            "command": str(command),
        }
        for name, command in scripts.items()
    ]


def _group_workspace_entries(
    entries: list[dict[str, object]],
    summaries: dict[str, str],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        category = str(entry.get("category") or "Other")
        grouped.setdefault(category, []).append(entry)

    ordered: list[dict[str, object]] = []
    for category, items in grouped.items():
        ordered.append(
            {
                "id": category.lower().replace(" ", "_"),
                "label": category,
                "summary": summaries.get(category),
                "count": len(items),
                "present_count": sum(1 for item in items if item.get("present")),
                "items": items,
            }
        )
    ordered.sort(key=lambda group: group["label"])
    return ordered


def _read_git_branch_state(repo_path: Path) -> tuple[str | None, bool | None]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), "status", "--short", "--branch"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except Exception:  # noqa: BLE001
        return None, None

    branch = None
    if output:
        first = output[0].strip()
        if first.startswith("## "):
            branch = first[3:].split("...")[0].strip() or None
    dirty = any(line.strip() and not line.startswith("## ") for line in output)
    return branch, dirty


def _read_readme_headline(repo_path: Path) -> str | None:
    for candidate in ("README.md", "README.MD"):
        readme_path = repo_path / candidate
        if not readme_path.exists():
            continue
        try:
            for line in readme_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("# "):
                    return stripped[2:].strip()
        except Exception:  # noqa: BLE001
            return None
    return None


def _find_latest_pretrade_validation(pretrade_root: Path, project_root: Path) -> dict[str, object] | None:
    ranked: list[tuple[float, Path, dict[str, object]]] = []
    for candidate in pretrade_root.rglob(PRETRADE_HANDOFF_VALIDATION_FILENAME):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if payload.get("artifact_type") != PRETRADE_HANDOFF_VALIDATION_CONTRACT_TYPE:
            continue
        ranked.append((candidate.stat().st_mtime, candidate, payload))

    if not ranked:
        return None

    _, path, payload = max(ranked, key=lambda item: item[0])
    return {
        "path": str(path),
        "href": _build_local_artifact_href(path, project_root),
        "payload": payload,
    }


def _build_local_artifact_href(path_value: str | Path | None, project_root: Path) -> str | None:
    if not path_value:
        return None

    try:
        path = Path(path_value).resolve()
        relative = path.relative_to(project_root.resolve())
    except Exception:  # noqa: BLE001
        return None

    return "/" + relative.as_posix()


def _find_latest_hyperliquid_artifact(search_roots: list[Path], filename: str) -> dict[str, object] | None:
    candidates: list[Path] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        candidates.extend(search_root.rglob(filename))

    ranked: list[tuple[float, Path, dict[str, object]]] = []
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not _is_hyperliquid_payload(filename, payload):
            continue
        ranked.append((candidate.stat().st_mtime, candidate, payload))

    if not ranked:
        return None

    _, path, payload = max(ranked, key=lambda item: item[0])
    return {
        "path": str(path),
        "artifact_type": payload.get("artifact_type"),
        "generated_at": payload.get("generated_at"),
        "market_supported": payload.get("market_supported"),
        "readiness_allowed": payload.get("readiness_allowed"),
        "signature_state": payload.get("signature_envelope", {}).get("signature_state"),
        "resolved_transport": payload.get("execution_context", {}).get("resolved_transport"),
        "execution_account_role": payload.get("execution_account_role"),
        "submit_state": payload.get("submit_state"),
        "submitted": payload.get("submitted"),
        "response_type": payload.get("response_type"),
        "remote_submit_called": payload.get("remote_submit_called"),
        "order_status_known": payload.get("status_known"),
        "normalized_state": payload.get("normalized_state"),
    }


def _is_hyperliquid_payload(filename: str, payload: dict[str, object]) -> bool:
    adapter_name = payload.get("adapter_name")
    if adapter_name == "hyperliquid":
        return True
    if filename == "hyperliquid_account_readiness.json":
        return "execution_account_role" in payload
    if filename == "hyperliquid_signed_action.json":
        return "signature_envelope" in payload
    if filename == "hyperliquid_submit_response.json":
        return "submit_state" in payload
    if filename == "hyperliquid_order_status.json":
        return "normalized_state" in payload or "status_known" in payload
    if filename == "hyperliquid_supervision.json":
        return "supervision_state" in payload or "polls_completed" in payload
    return False

def run_server():
    port = PORT
    max_retries = 5
    httpd = None

    while max_retries > 0:
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", port), DashboardHandler)
            break
        except OSError:
            print(f"Port {port} is busy, trying {port + 1}...")
            port += 1
            max_retries -= 1

    if not httpd:
        print("Error: Could not find an available port.")
        sys.exit(1)

    print(f"\n--- QuantLab Research Dashboard Dev Server ---")
    print(f"Serving from: {PROJECT_ROOT}")
    print(f"URL: http://127.0.0.1:{port}")
    print(f"Press Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    run_server()
