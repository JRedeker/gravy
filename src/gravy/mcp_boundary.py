"""MCP-facing control-plane boundary.

This module exposes exactly the four Gravy operations an external MCP server is
allowed to invoke: catalog, create, update, and close.  `create` also serves the
review page, so there is no separate serve operation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .control_plane import GravyControlPlane
from .models import LifecycleResult


class GravyMcpBoundary:
    """Dispatch MCP tool calls to the closed Gravy control plane."""

    _TOOL_NAMES = ("catalog", "create", "update", "close")

    def __init__(self, control_plane: GravyControlPlane) -> None:
        self._plane = control_plane

    @property
    def tools(self) -> tuple[str, ...]:
        """The closed set of MCP tool names supported by Gravy."""
        return self._TOOL_NAMES

    def handle(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Route one MCP tool call to the corresponding control-plane operation."""
        if name == "catalog":
            return {"ok": True, "result": self._plane.catalog()}
        if name == "create":
            result = self._plane.create(
                arguments.get("surface", ""), arguments.get("request", {})
            )
        elif name == "update":
            result = self._plane.update(
                arguments.get("review_id", ""), arguments.get("patch", {})
            )
        elif name == "close":
            result = self._plane.close(arguments.get("review_id", ""))
        else:
            return {
                "ok": False,
                "error": "unknown_tool",
                "available_tools": list(self._TOOL_NAMES),
            }
        return _serialize(result)


def _serialize(result: LifecycleResult) -> dict[str, Any]:
    if result.record is not None:
        return {"ok": True, "record": result.record.to_dict()}
    return {"ok": False, "diagnostic": str(result.diagnostic)}
