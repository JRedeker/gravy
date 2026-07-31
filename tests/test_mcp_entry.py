"""MCP runtime entry point tests."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import runpy
import socket
import subprocess
import sys
import threading
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

import gravy.mcp_entry
from gravy.artifacts import ArtifactStore
from gravy.config import ConfigurationError, GravyRuntimeConfig
from gravy.control_plane import GravyControlPlane
from gravy.lifecycle import LifecycleAdapter
from gravy.mcp_entry import GravyMcpServer, main
from gravy.ports import PortPool
from gravy.registry import ReviewRegistry


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
        self.mappings.pop(review_id, None)

    def reconcile_owned(self, owned_ports: set[int]) -> set[int]:
        return set()


class EventLoopThreadFakePage:
    """Fake page that asserts it runs on the async event-loop (main) thread."""

    def __init__(self, loop_thread_id: int) -> None:
        self.loop_thread_id = loop_thread_id
        self.launched_port: int | None = None
        self.closed = False

    def launch(self, port: int) -> None:
        assert threading.current_thread().ident == self.loop_thread_id, (
            "launch must run on the event-loop thread"
        )
        self.launched_port = port

    def close(self) -> None:
        assert threading.current_thread().ident == self.loop_thread_id, (
            "close must run on the event-loop thread"
        )
        self.closed = True


class EventLoopThreadFakeTailnet:
    """Fake tailnet that asserts Serve mutations run on the event-loop (main) thread."""

    def __init__(self, loop_thread_id: int) -> None:
        self.loop_thread_id = loop_thread_id
        self.mappings: dict[str, int] = {}

    def https_available(self) -> bool:
        return True

    def expose(self, review_id: str, port: int) -> str:
        assert threading.current_thread().ident == self.loop_thread_id, (
            "expose must run on the event-loop thread"
        )
        self.mappings[review_id] = port
        return f"https://{review_id}.tailnet.test"

    def remove(self, review_id: str, port: int) -> None:
        assert threading.current_thread().ident == self.loop_thread_id, (
            "remove must run on the event-loop thread"
        )
        self.mappings.pop(review_id, None)

    def reconcile_owned(self, owned_ports: set[int]) -> set[int]:
        return set()


def _make_plane(tmp_path: Path) -> GravyControlPlane:
    lifecycle = LifecycleAdapter(
        ReviewRegistry(tmp_path / "registry.json"),
        PortPool(41000, 41010),
        ArtifactStore(tmp_path / "artifacts"),
        FakeTailnet(),
        lambda _review_id, _request: FakePage(),
    )
    return GravyControlPlane(lifecycle)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.asynccontextmanager
async def _running_server(server: GravyMcpServer, *, timeout: float = 5.0) -> AsyncIterator[GravyMcpServer]:
    task = asyncio.create_task(server.serve())
    base = f"http://{server.config.internal_host}:{server.config.internal_port}"
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            deadline = asyncio.get_event_loop().time() + timeout
            while True:
                try:
                    resp = await client.get(f"{base}/ready")
                    if resp.status_code == 200:
                        break
                except Exception:
                    pass
                if asyncio.get_event_loop().time() >= deadline:
                    raise TimeoutError("server did not become ready")
                await asyncio.sleep(0.05)
        yield server
    finally:
        server.shutdown()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


@contextlib.asynccontextmanager
async def _mcp_session(server: GravyMcpServer) -> AsyncIterator[ClientSession]:
    url = f"http://{server.config.internal_host}:{server.config.internal_port}{server.config.path}"
    async with streamable_http_client(url) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


def _tool_text(result: Any) -> dict[str, Any]:
    assert len(result.content) == 1
    return json.loads(result.content[0].text)


def test_server_rejects_invalid_config_before_binding(tmp_path: Path) -> None:
    bad_config = GravyRuntimeConfig(internal_port=6277, external_port=6277)
    with pytest.raises(ConfigurationError):
        GravyMcpServer(bad_config, _make_plane(tmp_path))


async def test_server_ready_endpoint_reports_ready(tmp_path: Path) -> None:
    config = GravyRuntimeConfig(internal_port=_free_port(), external_port=6277)
    server = GravyMcpServer(config, _make_plane(tmp_path))
    async with _running_server(server):
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(
                f"http://{config.internal_host}:{config.internal_port}/ready"
            )
            assert resp.status_code == 200
            assert resp.json() == {"status": "ready"}


async def test_server_exposes_only_catalog_create_update_close_tools(tmp_path: Path) -> None:
    config = GravyRuntimeConfig(internal_port=_free_port(), external_port=6277)
    server = GravyMcpServer(config, _make_plane(tmp_path))
    async with _running_server(server):
        async with _mcp_session(server) as session:
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {"catalog", "create", "update", "close"}


async def test_server_round_trips_catalog_create_close(tmp_path: Path) -> None:
    config = GravyRuntimeConfig(internal_port=_free_port(), external_port=6277)
    server = GravyMcpServer(config, _make_plane(tmp_path))
    async with _running_server(server):
        async with _mcp_session(server) as session:
            catalog = _tool_text(await session.call_tool("catalog", {}))
            assert catalog["ok"] is True
            surfaces = {item["surface"] for item in catalog["result"]["surfaces"]}
            assert surfaces == {"gallery", "pairwise", "form", "checklist"}

            created = _tool_text(
                await session.call_tool(
                    "create",
                    {"surface": "gallery", "request": {"surface": "gallery", "items": ["a.png"]}},
                )
            )
            assert created["ok"] is True
            review_id = created["record"]["review_id"]
            assert created["record"]["state"] == "active"

            closed = _tool_text(await session.call_tool("close", {"review_id": review_id}))
            assert closed["ok"] is True
            assert closed["record"]["state"] == "terminal"


async def test_server_is_foreground_and_does_not_fork(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fork_calls: list[Any] = []
    popen_calls: list[Any] = []

    def fake_fork() -> int:
        fork_calls.append(True)
        raise OSError("fork is not allowed")

    def fake_popen(*args: Any, **kwargs: Any) -> Any:
        popen_calls.append((args, kwargs))
        raise OSError("subprocess is not allowed")

    monkeypatch.setattr(os, "fork", fake_fork)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    config = GravyRuntimeConfig(internal_port=_free_port(), external_port=6277)
    server = GravyMcpServer(config, _make_plane(tmp_path))
    async with _running_server(server):
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(
                f"http://{config.internal_host}:{config.internal_port}/ready"
            )
            assert resp.status_code == 200

    assert not fork_calls
    assert not popen_calls


def test_main_default_external_port_is_6281(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_config: GravyRuntimeConfig | None = None

    class FakeControlPlane:
        pass

    def fake_create_control_plane(config: GravyRuntimeConfig, state_dir: Path) -> Any:
        return FakeControlPlane()

    class FakeServer:
        def __init__(self, config: GravyRuntimeConfig, control_plane: Any) -> None:
            nonlocal captured_config
            captured_config = config

        async def serve(self) -> None:
            return None

    def fake_asyncio_run(coro: Any) -> Any:
        if hasattr(coro, "close"):
            coro.close()
        return None

    monkeypatch.setattr(
        gravy.mcp_entry, "create_control_plane", fake_create_control_plane
    )
    monkeypatch.setattr(gravy.mcp_entry, "GravyMcpServer", FakeServer)
    monkeypatch.setattr(asyncio, "run", fake_asyncio_run)

    for key in (
        "GRAVY_INTERNAL_HOST",
        "GRAVY_INTERNAL_PORT",
        "GRAVY_EXTERNAL_PORT",
        "GRAVY_PATH",
        "GRAVY_STATE_DIR",
    ):
        monkeypatch.delenv(key, raising=False)

    main()

    assert captured_config is not None
    assert captured_config.external_port == 6281


async def test_create_and_close_run_on_event_loop_thread(
    tmp_path: Path,
) -> None:
    """Create/close handlers run on the async event-loop (main) thread and preserve results.

    Gradio ``Blocks.launch()`` must execute on the main thread, so the lifecycle
    is no longer offloaded to a worker thread.  The fakes here raise if they are
    invoked from any other thread, proving the tool handlers keep the work on the
    event-loop thread.
    """
    loop_thread_id = threading.current_thread().ident

    lifecycle = LifecycleAdapter(
        ReviewRegistry(tmp_path / "registry.json"),
        PortPool(41000, 41010),
        ArtifactStore(tmp_path / "artifacts"),
        EventLoopThreadFakeTailnet(loop_thread_id),
        lambda _review_id, _request: EventLoopThreadFakePage(loop_thread_id),
    )
    plane = GravyControlPlane(lifecycle)
    config = GravyRuntimeConfig(internal_port=_free_port(), external_port=6277)
    server = GravyMcpServer(config, plane)

    async with _running_server(server):
        async with _mcp_session(server) as session:
            created = _tool_text(
                await session.call_tool(
                    "create",
                    {"surface": "gallery", "request": {"surface": "gallery", "items": ["a.png"]}},
                )
            )
            assert created["ok"] is True
            record = created["record"]
            assert record["state"] == "active"
            assert record["tailnet_url"].startswith("https://")

            catalog = _tool_text(await session.call_tool("catalog", {}))
            assert catalog["ok"] is True

            updated = _tool_text(
                await session.call_tool(
                    "update",
                    {"review_id": record["review_id"], "patch": {"phase": "reviewed"}},
                )
            )
            assert updated["ok"] is True
            assert updated["record"]["metadata"] == {"phase": "reviewed"}

            closed = _tool_text(
                await session.call_tool("close", {"review_id": record["review_id"]})
            )
            assert closed["ok"] is True
            assert closed["record"]["state"] == "terminal"


def test_main_guard_invokes_main_when_run_as_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Executing the module as __main__ calls main() without starting a real server."""
    recorded: list[str] = []

    def fake_asyncio_run(coro: Any) -> None:
        recorded.append(coro.__qualname__)
        coro.close()

    monkeypatch.setattr(asyncio, "run", fake_asyncio_run)
    monkeypatch.delitem(sys.modules, "gravy.mcp_entry")

    runpy.run_module("gravy.mcp_entry", run_name="__main__")

    assert recorded == ["GravyMcpServer.serve"]
