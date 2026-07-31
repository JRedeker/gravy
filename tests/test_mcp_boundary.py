from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from gravy.artifacts import ArtifactStore
from gravy.control_plane import GravyControlPlane
from gravy.lifecycle import LifecycleAdapter
from gravy.mcp_boundary import GravyMcpBoundary
from gravy.models import DiagnosticCode, LifecycleResult, ReviewRecord, ReviewState
from gravy.ports import PortPool
from gravy.registry import ReviewRegistry
from gravy.schemas import validate_request


class FakePage:
    def __init__(self) -> None:
        self.launched_port: int | None = None
        self.closed = False

    def launch(self, port: int) -> None:
        self.launched_port = port

    def close(self) -> None:
        self.closed = True


class FakeTailnet:
    def __init__(self) -> None:
        self.mappings: dict[str, int] = {}

    def https_available(self) -> bool:
        return True

    def expose(self, review_id: str, port: int) -> str:
        self.mappings[review_id] = port
        return f"https://{review_id}.tailnet.test"

    def remove(self, review_id: str, port: int) -> None:
        assert self.mappings.pop(review_id) == port


def make_plane(tmp_path: Path) -> GravyControlPlane:
    lifecycle = LifecycleAdapter(
        ReviewRegistry(tmp_path / "registry.json"),
        PortPool(41000, 41010),
        ArtifactStore(tmp_path / "artifacts"),
        FakeTailnet(),
        lambda _review_id, _request: FakePage(),
    )
    return GravyControlPlane(lifecycle)


def test_mcp_boundary_exposes_only_catalog_create_update_close():
    boundary = GravyMcpBoundary(make_plane(Path("/tmp/should-not-be-used")))

    assert boundary.tools == ("catalog", "create", "update", "close")


def test_mcp_boundary_routes_catalog_create_update_close(tmp_path: Path):
    plane = make_plane(tmp_path)
    boundary = GravyMcpBoundary(plane)

    catalog = boundary.handle("catalog", {})
    assert catalog["ok"] is True
    assert set(item["surface"] for item in catalog["result"]["surfaces"]) == {
        "gallery",
        "pairwise",
        "form",
        "checklist",
    }

    created = boundary.handle(
        "create", {"surface": "gallery", "request": {"surface": "gallery", "items": ["a.png"]}}
    )
    assert created["ok"] is True
    record = created["record"]
    assert record["review_id"]
    assert record["tailnet_url"].startswith("https://")

    updated = boundary.handle(
        "update", {"review_id": record["review_id"], "patch": {"phase": "reviewing"}}
    )
    assert updated["ok"] is True
    assert updated["record"]["metadata"] == {"phase": "reviewing"}

    closed = boundary.handle("close", {"review_id": record["review_id"]})
    assert closed["ok"] is True
    assert closed["record"]["state"] == "terminal"


def test_mcp_boundary_unknown_tool_returns_typed_error():
    boundary = GravyMcpBoundary(make_plane(Path("/tmp/should-not-be-used")))

    result = boundary.handle("serve", {})

    assert result["ok"] is False
    assert result["error"] == "unknown_tool"
    assert result["available_tools"] == ["catalog", "create", "update", "close"]


def test_mcp_boundary_rejects_invalid_create_without_allocation(tmp_path: Path):
    plane = make_plane(tmp_path)
    boundary = GravyMcpBoundary(plane)

    result = boundary.handle(
        "create", {"surface": "gallery", "request": {"surface": "form", "fields": ["x"]}}
    )

    assert result["ok"] is False
    assert result["diagnostic"] == str(DiagnosticCode.INVALID_REQUEST)
    assert plane.lifecycle.registry.active_records() == ()
    assert plane.lifecycle.ports.reserved == frozenset()
