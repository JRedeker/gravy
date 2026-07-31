"""Typed runtime configuration for the Gravy MCP entry point."""

from __future__ import annotations

from dataclasses import dataclass

VISION_EXTERNAL_PORT_RANGE = range(6276, 6326)


class ConfigurationError(ValueError):
    """Raised when the Gravy runtime configuration is invalid."""


@dataclass(frozen=True, slots=True)
class GravyRuntimeConfig:
    """Validated loopback MCP runtime configuration.

    The internal endpoint is what Gravy binds in the foreground.  Vision owns
    the external endpoint and forwards it to the internal ``/mcp`` URL.  Gravy
    validates the contract because Vision only checks that its own external port
    is within ``6276-6325``.
    """

    internal_port: int
    external_port: int
    internal_host: str = "127.0.0.1"
    path: str = "/mcp"

    @property
    def internal_url(self) -> str:
        return f"http://{self.internal_host}:{self.internal_port}{self.path}"

    @property
    def vision_url(self) -> str:
        return f"http://{self.internal_host}:{self.external_port}{self.path}"

    def validate(self) -> None:
        """Reject dangerous or invalid runtime configurations.

        Enforcement:
        - ``internal_host`` must be the IPv4 loopback address.
        - ``path`` must be exactly ``/mcp``.
        - ``internal_port`` and ``external_port`` must be valid TCP ports.
        - ``internal_port`` must not be in Vision's external range ``6276-6325``.
        - ``external_port`` must be inside Vision's external range ``6276-6325``.
        - The two ports must be distinct.
        """
        if not isinstance(self.internal_port, int) or not isinstance(
            self.external_port, int
        ):
            raise ConfigurationError("internal_port and external_port must be integers")
        if not (1 <= self.internal_port <= 65535):
            raise ConfigurationError("internal_port must be a valid TCP port (1-65535)")
        if not (1 <= self.external_port <= 65535):
            raise ConfigurationError("external_port must be a valid TCP port (1-65535)")
        if self.internal_host != "127.0.0.1":
            raise ConfigurationError("internal_host must be loopback (127.0.0.1)")
        if self.path != "/mcp":
            raise ConfigurationError("path must be exactly '/mcp'")
        if self.internal_port == self.external_port:
            raise ConfigurationError(
                "internal_port and external_port must not be equal"
            )
        if self.internal_port in VISION_EXTERNAL_PORT_RANGE:
            raise ConfigurationError(
                f"internal_port {self.internal_port} must not fall within "
                f"Vision's external port range 6276-6325"
            )
        if self.external_port not in VISION_EXTERNAL_PORT_RANGE:
            raise ConfigurationError(
                f"external_port {self.external_port} must be within "
                f"Vision's external port range 6276-6325"
            )
