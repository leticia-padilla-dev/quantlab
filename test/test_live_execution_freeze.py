from __future__ import annotations

import sys

import pytest

from quantlab import app
from quantlab.cli.app_args import build_argument_parser
from quantlab.cli.live_execution import (
    LIVE_EXECUTION_DISABLED,
    enforce_live_execution_freeze,
    requested_live_mutations,
)
from quantlab.errors import ConfigError


@pytest.mark.parametrize(
    ("argv", "expected_flag"),
    [
        (
            ["--hyperliquid-submit-signed-action", "outputs/action.json"],
            "--hyperliquid-submit-signed-action",
        ),
        (
            ["--hyperliquid-submit-session", "outputs/action.json"],
            "--hyperliquid-submit-session",
        ),
        (
            ["--hyperliquid-submit-sessions-cancel", "outputs/session"],
            "--hyperliquid-submit-sessions-cancel",
        ),
        (
            ["--broker-order-validations-submit-real", "outputs/session"],
            "--broker-order-validations-submit-real",
        ),
    ],
)
def test_known_live_mutation_routes_fail_closed(argv, expected_flag):
    args = build_argument_parser().parse_args(argv)

    assert requested_live_mutations(args) == (expected_flag,)
    with pytest.raises(ConfigError) as exc_info:
        enforce_live_execution_freeze(args)

    message = str(exc_info.value)
    assert LIVE_EXECUTION_DISABLED in message
    assert expected_flag in message


@pytest.mark.parametrize(
    "argv",
    [
        ["--paper"],
        ["--kraken-dry-run-session"],
        ["--broker-order-validations-submit-stub", "outputs/session"],
        ["--hyperliquid-submit-sessions-status", "outputs/session"],
        ["--hyperliquid-submit-sessions-reconcile", "outputs/session"],
        ["--hyperliquid-submit-sessions-fills", "outputs/session"],
        ["--hyperliquid-submit-sessions-health", "outputs/hyperliquid_submits"],
    ],
)
def test_non_mutating_paper_and_broker_routes_remain_available(argv):
    args = build_argument_parser().parse_args(argv)

    assert requested_live_mutations(args) == ()
    enforce_live_execution_freeze(args)


def test_multiple_live_mutations_are_reported_together():
    args = build_argument_parser().parse_args(
        [
            "--hyperliquid-submit-session",
            "outputs/action.json",
            "--broker-order-validations-submit-real",
            "outputs/session",
        ]
    )

    with pytest.raises(ConfigError) as exc_info:
        enforce_live_execution_freeze(args)

    message = str(exc_info.value)
    assert "--hyperliquid-submit-session" in message
    assert "--broker-order-validations-submit-real" in message


def test_cli_live_freeze_returns_nonzero_exit(monkeypatch, capsys):
    monkeypatch.setattr(app, "_load_runtime_dependencies", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["quantlab", "--hyperliquid-submit-session", "outputs/action.json"],
    )

    with pytest.raises(SystemExit) as exc_info:
        app.main()

    assert exc_info.value.code == 2
    assert LIVE_EXECUTION_DISABLED in capsys.readouterr().err
