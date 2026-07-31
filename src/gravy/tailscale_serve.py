"""Injectable Tailscale Serve adapter for Gravy review lifecycles.

This module deliberately never runs a global `tailscale serve reset`.  It only
adds or removes mappings for review ports explicitly recorded as Gravy-owned, and
uses `tailscale serve status --json` to reconcile stale state.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable, Protocol


class TailnetCommandError(RuntimeError):
    """Typed outcome for a failed Tailscale CLI invocation."""

    def __init__(
        self,
        *,
        command: list[str],
        returncode: int,
        stdout: str,
        stderr: str,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message or f"tailscale command failed ({returncode}): {' '.join(command)}"
        )
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class CommandRunner(Protocol):
    """Injectable subprocess boundary for deterministic testing."""

    def __call__(
        self,
        args: Sequence[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float | None,
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True, slots=True)
class _Status:
    """Subset of `tailscale status --json` needed for HTTPS exposure."""

    dns_name: str
    magic_dns_enabled: bool


class TailscaleServe:
    """Gravy-owned Tailscale Serve mappings with typed outcomes and no global reset."""

    def __init__(
        self,
        executable: str = "tailscale",
        *,
        timeout: float = 10.0,
        runner: CommandRunner | None = None,
    ) -> None:
        self._executable = executable
        self._timeout = timeout
        self._runner: CommandRunner = runner or subprocess.run

    def https_available(self) -> bool:
        """Preflight check: is the tailnet reachable and HTTPS-capable?"""
        try:
            status = self._load_status()
        except TailnetCommandError:
            return False
        return status.magic_dns_enabled and bool(status.dns_name)

    def expose(self, review_id: str, port: int) -> str:
        """Expose a local Gradio listener on a persistent Tailnet HTTPS origin.

        Raises `TailnetCommandError` if the tailnet is not ready or the Serve
        mutation fails.  No registry entry or port is allocated by this method.
        """
        if not self.https_available():
            raise TailnetCommandError(
                command=[self._executable, "status", "--json"],
                returncode=1,
                stdout="",
                stderr="Tailnet HTTPS is not available",
                message="Tailnet HTTPS is not available",
            )
        public_port = self._public_port(port)
        self._run(
            [
                "serve",
                "--bg",
                "--yes",
                f"--https={public_port}",
                f"localhost:{port}",
            ],
            check=True,
        )
        return f"https://{self._load_status().dns_name}:{public_port}"

    def remove(self, review_id: str, port: int) -> None:
        """Remove a Gravy-owned Serve mapping if it still exists.

        The method is idempotent: if `serve status --json` shows no matching
        mapping, the `off` command is not run.
        """
        public_port = self._public_port(port)
        if not self._mapping_exists(public_port):
            return
        self._run(
            [
                "serve",
                "--bg",
                "--yes",
                f"--https={public_port}",
                "off",
            ],
            check=True,
        )

    def reconcile_owned(self, owned_ports: set[int]) -> set[int]:
        """Remove stale Serve mappings for ports explicitly owned by Gravy.

        Reads `tailscale serve status --json` and removes only Web handlers
        whose public port is in `owned_ports`.  Foreign mappings are never
        touched and `tailscale serve reset` is never used.
        """
        status = self._load_serve_status()
        removed: set[int] = set()
        for hostport in status.get("Web", {}):
            public_port = _public_port_from_hostport(hostport)
            if public_port in owned_ports:
                self._run(
                    [
                        "serve",
                        "--bg",
                        "--yes",
                        f"--https={public_port}",
                        "off",
                    ],
                    check=True,
                )
                removed.add(public_port)
        return removed

    def _load_status(self) -> _Status:
        result = self._run(["status", "--json"], check=True)
        data = json.loads(result.stdout)
        current = data.get("CurrentTailnet", {})
        self_node = data.get("Self", {})
        dns_name = self_node.get("DNSName") or ""
        if not dns_name and self_node.get("HostName") and current.get("MagicDNSSuffix"):
            dns_name = f"{self_node['HostName']}.{current['MagicDNSSuffix']}"
        return _Status(
            dns_name=dns_name.rstrip("."),
            magic_dns_enabled=bool(current.get("MagicDNSEnabled")),
        )

    def _load_serve_status(self) -> dict[str, Any]:
        result = self._run(["serve", "status", "--json"], check=True)
        return json.loads(result.stdout)

    def _mapping_exists(self, public_port: int) -> bool:
        try:
            status = self._load_serve_status()
        except TailnetCommandError:
            return False
        for hostport in status.get("Web", {}):
            if _public_port_from_hostport(hostport) == public_port:
                return True
        return False

    def _public_port(self, local_port: int) -> int:
        return local_port

    def _run(
        self,
        args: list[str],
        *,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self._runner(
                [self._executable, *args],
                capture_output=True,
                text=True,
                check=False,
                timeout=self._timeout,
            )
        except FileNotFoundError as exc:
            raise TailnetCommandError(
                command=[self._executable, *args],
                returncode=127,
                stdout="",
                stderr=str(exc),
            ) from exc
        if check and result.returncode != 0:
            raise TailnetCommandError(
                command=[self._executable, *args],
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        return result


def _public_port_from_hostport(hostport: str) -> int:
    """Parse the public port from a "host.example.ts.net:443" host:port string."""
    if ":" not in hostport:
        return 0
    try:
        return int(hostport.rsplit(":", 1)[-1])
    except ValueError:
        return 0
