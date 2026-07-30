"""Closed, review-ID-addressed local control plane.

This module deliberately exposes only the four Gravy lifecycle operations.  It
does not identify callers or carry MCP-session state: lifecycle ownership is
always resolved by the supplied review ID.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .catalog import catalog
from .lifecycle import LifecycleAdapter
from .models import DiagnosticCode, LifecycleResult
from .schemas import RequestValidationError, validate_request


class GravyControlPlane:
    """Adapt untrusted control-plane inputs to the deterministic lifecycle."""

    def __init__(self, lifecycle: LifecycleAdapter) -> None:
        self.lifecycle = lifecycle

    def catalog(self) -> dict[str, Any]:
        return catalog()

    def create(self, surface: str, request: Mapping[str, Any]) -> LifecycleResult:
        """Validate the closed discriminator before lifecycle allocation starts."""
        try:
            parsed = validate_request(request)
        except RequestValidationError:
            return LifecycleResult(diagnostic=DiagnosticCode.INVALID_REQUEST)
        if surface != parsed.surface:
            return LifecycleResult(diagnostic=DiagnosticCode.INVALID_REQUEST)
        return self.lifecycle.create(parsed)

    def update(self, review_id: str, patch: Mapping[str, object]) -> LifecycleResult:
        return self.lifecycle.registry.update(review_id, patch)

    def close(self, review_id: str) -> LifecycleResult:
        return self.lifecycle.close(review_id)

    def startup_recovery(self) -> tuple[LifecycleResult, ...]:
        """Terminalize in-process pages lost to a backend recycle."""
        return self.lifecycle.recover_after_recycle()
