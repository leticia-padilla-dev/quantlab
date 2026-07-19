from __future__ import annotations

import argparse

from quantlab.errors import ConfigError

LIVE_EXECUTION_DISABLED = "live_execution_disabled"

# Remote broker mutations exposed by the current CLI. Keep this inventory explicit:
# adding a new mutating command requires updating this policy and its regression tests.
LIVE_MUTATION_ARGUMENTS: tuple[tuple[str, str], ...] = (
    ("hyperliquid_submit_signed_action", "--hyperliquid-submit-signed-action"),
    ("hyperliquid_submit_session", "--hyperliquid-submit-session"),
    ("hyperliquid_submit_sessions_cancel", "--hyperliquid-submit-sessions-cancel"),
    ("broker_order_validations_submit_real", "--broker-order-validations-submit-real"),
)


def requested_live_mutations(args: argparse.Namespace) -> tuple[str, ...]:
    """Return the mutating CLI routes requested by the parsed arguments."""

    return tuple(
        cli_flag
        for attribute, cli_flag in LIVE_MUTATION_ARGUMENTS
        if bool(getattr(args, attribute, None))
    )


def enforce_live_execution_freeze(args: argparse.Namespace) -> None:
    """Fail closed while v0.1-hardening remediation is in progress."""

    requested = requested_live_mutations(args)
    if not requested:
        return

    routes = ", ".join(requested)
    raise ConfigError(
        f"{LIVE_EXECUTION_DISABLED}: remote broker mutation is frozen during "
        f"v0.1-hardening; blocked route(s): {routes}. Paper, dry-run, validation, "
        "status and reconciliation remain available."
    )
