"""Typed tests for the injectable Tailscale Serve adapter.

All subprocess calls are mocked; no live Tailnet commands are run.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any

import pytest

from gravy.tailscale_serve import TailnetCommandError, TailscaleServe


def _completed(
    returncode: int = 0, stdout: str = "", stderr: str = ""
) -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _runner(responses: dict[tuple[str, ...], SimpleNamespace]) -> Any:
    """Return a callable that replays canned subprocess results by command tuple."""
    commands: list[tuple[str, ...]] = []

    def run(
        args: Sequence[str],
        *,
        capture_output: bool = False,
        text: bool = False,
        check: bool = False,
        timeout: float | None = None,
    ) -> SimpleNamespace:
        cmd = tuple(args)
        commands.append(cmd)
        if cmd not in responses:
            raise FileNotFoundError(f"unexpected command: {cmd}")
        result = responses[cmd]
        if check and result.returncode != 0:
            raise TailnetCommandError(
                command=list(cmd),
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        return result

    run.commands = commands  # type: ignore[attr-defined]
    return run


def _status(dns_name: str = "host.example.ts.net.", enabled: bool = True) -> str:
    return json.dumps(
        {
            "CurrentTailnet": {
                "MagicDNSEnabled": enabled,
                "MagicDNSSuffix": "example.ts.net",
            },
            "Self": {"DNSName": dns_name, "HostName": "host"},
        }
    )


SERVE_CMD = (
    "tailscale",
    "serve",
    "--bg",
    "--yes",
    "--https=41000",
    "localhost:41000",
)

OFF_CMD = ("tailscale", "serve", "--bg", "--yes", "--https=41000", "off")

STATUS_CMD = ("tailscale", "status", "--json")

SERVE_STATUS_CMD = ("tailscale", "serve", "status", "--json")


def test_https_available_is_true_when_magicdns_and_dns_name_present():
    runner = _runner({STATUS_CMD: _completed(0, _status())})
    serve = TailscaleServe(runner=runner)

    assert serve.https_available() is True
    assert runner.commands == [STATUS_CMD]


def test_https_available_is_false_when_magicdns_disabled():
    runner = _runner(
        {STATUS_CMD: _completed(0, _status(enabled=False))}
    )
    serve = TailscaleServe(runner=runner)

    assert serve.https_available() is False


def test_https_available_is_false_when_tailscale_status_fails():
    runner = _runner({STATUS_CMD: _completed(1, "", "tailscaled not running")})
    serve = TailscaleServe(runner=runner)

    assert serve.https_available() is False


def test_expose_issues_serve_command_and_returns_url():
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_CMD: _completed(0, ""),
        }
    )
    serve = TailscaleServe(runner=runner)

    url = serve.expose("review-1", 41000)

    assert url == "https://host.example.ts.net:41000"
    assert SERVE_CMD in runner.commands


def test_expose_preflight_raises_before_serve_when_https_unavailable():
    runner = _runner(
        {STATUS_CMD: _completed(0, _status(enabled=False))}
    )
    serve = TailscaleServe(runner=runner)

    with pytest.raises(TailnetCommandError, match="HTTPS"):
        serve.expose("review-1", 41000)

    assert SERVE_CMD not in runner.commands


def test_expose_raises_typed_error_when_serve_command_fails():
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_CMD: _completed(1, "", "serve failed: port in use"),
        }
    )
    serve = TailscaleServe(runner=runner)

    with pytest.raises(TailnetCommandError) as exc_info:
        serve.expose("review-1", 41000)

    error = exc_info.value
    assert error.command == list(SERVE_CMD)
    assert error.returncode == 1
    assert "serve failed" in error.stderr


def test_remove_issues_off_command_when_mapping_exists():
    status_json = json.dumps(
        {
            "Web": {
                "host.example.ts.net:41000": {
                    "Handlers": {"/": {"Proxy": "http://127.0.0.1:41000"}}
                }
            }
        }
    )
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_STATUS_CMD: _completed(0, status_json),
            OFF_CMD: _completed(0, ""),
        }
    )
    serve = TailscaleServe(runner=runner)

    serve.remove("review-1", 41000)

    assert OFF_CMD in runner.commands


def test_remove_is_idempotent_when_mapping_is_already_gone():
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_STATUS_CMD: _completed(0, json.dumps({"Web": {}})),
        }
    )
    serve = TailscaleServe(runner=runner)

    serve.remove("review-1", 41000)

    assert OFF_CMD not in runner.commands


def test_reconcile_owned_removes_only_stale_gravy_ports():
    status_json = json.dumps(
        {
            "Web": {
                "host.example.ts.net:41000": {
                    "Handlers": {"/": {"Proxy": "http://127.0.0.1:41000"}}
                },
                "host.example.ts.net:41001": {
                    "Handlers": {"/": {"Proxy": "http://127.0.0.1:41001"}}
                },
                "host.example.ts.net:50000": {
                    "Handlers": {"/": {"Proxy": "http://127.0.0.1:50000"}}
                },
            }
        }
    )
    off_41001 = (
        "tailscale",
        "serve",
        "--bg",
        "--yes",
        "--https=41001",
        "off",
    )
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_STATUS_CMD: _completed(0, status_json),
            OFF_CMD: _completed(0, ""),
            off_41001: _completed(0, ""),
        }
    )
    serve = TailscaleServe(runner=runner)

    removed = serve.reconcile_owned({41000, 41001})

    assert removed == {41000, 41001}
    assert OFF_CMD in runner.commands
    assert off_41001 in runner.commands
    assert (
        "tailscale",
        "serve",
        "--bg",
        "--yes",
        "--https=50000",
        "off",
    ) not in runner.commands


def test_reconcile_owned_returns_empty_when_status_has_no_web_mappings():
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_STATUS_CMD: _completed(0, json.dumps({"Web": {}})),
        }
    )
    serve = TailscaleServe(runner=runner)

    assert serve.reconcile_owned({41000}) == set()
    assert OFF_CMD not in runner.commands


def test_reconcile_owned_raises_typed_error_when_status_command_fails():
    runner = _runner(
        {
            STATUS_CMD: _completed(0, _status()),
            SERVE_STATUS_CMD: _completed(1, "", "permission denied"),
        }
    )
    serve = TailscaleServe(runner=runner)

    with pytest.raises(TailnetCommandError) as exc_info:
        serve.reconcile_owned({41000})

    assert exc_info.value.command == list(SERVE_STATUS_CMD)
