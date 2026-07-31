"""Foreground Streamable HTTP MCP entry point for Gravy.

This module wraps the existing review runtime in a thin MCP control boundary.  It
binds only to the configured loopback address, exposes exactly the four Gravy
operations, and provides a small readiness endpoint for Vision's managed-http
health check.  It never daemonizes or forks.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import uvicorn
from mcp.server import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .artifacts import ArtifactStore
from .config import GravyRuntimeConfig
from .control_plane import GravyControlPlane
from .gradio_runtime import GradioBlocksPage
from .lifecycle import LifecycleAdapter
from .mcp_boundary import GravyMcpBoundary
from .ports import PortPool
from .registry import ReviewRegistry
from .tailscale_serve import TailscaleServe


def create_control_plane(config: GravyRuntimeConfig, state_dir: Path) -> GravyControlPlane:
    """Wire the existing review runtime into a ``GravyControlPlane``.

    Review ports are kept separate from the MCP internal port and from Vision's
    external port range.  The runtime owns review lifecycle state under
    ``state_dir``.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    registry = ReviewRegistry(state_dir / "registry.json", capacity=10)
    ports = PortPool(17000, 17099)
    artifacts = ArtifactStore(state_dir / "artifacts")
    tailnet = TailscaleServe()
    return GravyControlPlane(
        LifecycleAdapter(
            registry=registry,
            ports=ports,
            artifacts=artifacts,
            tailnet=tailnet,
            build_page=GradioBlocksPage.build_for,
        )
    )


class GravyMcpServer:
    """Foreground Streamable HTTP MCP server for the Gravy review kit."""

    def __init__(self, config: GravyRuntimeConfig, control_plane: GravyControlPlane) -> None:
        config.validate()
        self.config = config
        self._control_plane = control_plane
        self._boundary = GravyMcpBoundary(control_plane)
        self._server: uvicorn.Server | None = None

        self._mcp = FastMCP(
            "gravy",
            host=config.internal_host,
            port=config.internal_port,
            streamable_http_path=config.path,
            log_level="WARNING",
        )

        @self._mcp.tool()
        async def catalog() -> dict[str, Any]:
            """List supported review surfaces, schemas, and examples."""
            return self._boundary.handle("catalog", {})

        @self._mcp.tool()
        async def create(surface: str, request: Mapping[str, Any]) -> dict[str, Any]:
            """Create a review page and return its lifecycle record."""
            return self._boundary.handle(
                "create", {"surface": surface, "request": request}
            )

        @self._mcp.tool()
        async def update(review_id: str, patch: Mapping[str, Any]) -> dict[str, Any]:
            """Update metadata for an active review."""
            return self._boundary.handle(
                "update", {"review_id": review_id, "patch": patch}
            )

        @self._mcp.tool()
        async def close(review_id: str) -> dict[str, Any]:
            """Close a review and release its resources."""
            return self._boundary.handle("close", {"review_id": review_id})

        @self._mcp.custom_route("/ready", methods=["GET"])
        async def _ready(_request: Request) -> JSONResponse:
            return JSONResponse({"status": "ready"})

    async def serve(self) -> None:
        """Start the foreground uvicorn server and block until ``shutdown``."""
        app = self._mcp.streamable_http_app()
        uvicorn_config = uvicorn.Config(
            app,
            host=self.config.internal_host,
            port=self.config.internal_port,
            log_level="warning",
        )
        self._server = uvicorn.Server(uvicorn_config)
        await self._server.serve()

    def shutdown(self) -> None:
        """Request a graceful stop of the foreground server."""
        if self._server is not None:
            self._server.should_exit = True


def main() -> None:
    """CLI entry point: read configuration, validate it, and serve."""
    config = GravyRuntimeConfig(
        internal_host=os.environ.get("GRAVY_INTERNAL_HOST", "127.0.0.1"),
        internal_port=int(os.environ.get("GRAVY_INTERNAL_PORT", "7654")),
        external_port=int(os.environ.get("GRAVY_EXTERNAL_PORT", "6277")),
        path=os.environ.get("GRAVY_PATH", "/mcp"),
    )
    state_dir = Path(
        os.environ.get("GRAVY_STATE_DIR", Path.home() / ".local/share/gravy")
    )
    control_plane = create_control_plane(config, state_dir)
    server = GravyMcpServer(config, control_plane)
    asyncio.run(server.serve())
