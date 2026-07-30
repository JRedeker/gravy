"""In-process Gradio and Tailnet lifecycle coordination.

Concrete Gradio and Tailnet integrations stay behind small protocols so the
state machine is deterministic and testable without starting listeners.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .artifacts import ArtifactStore
from .models import DiagnosticCode, LifecycleResult
from .ports import PortPool
from .registry import ReviewRegistry
from .schemas import ReviewRequest


class GradioPage(Protocol):
    """A single in-process Blocks listener."""

    def launch(self, port: int) -> None: ...

    def close(self) -> None: ...


class TailnetServe(Protocol):
    """Gravy-owned persistent Tailnet Serve mappings only."""

    def https_available(self) -> bool: ...

    def expose(self, review_id: str, port: int) -> str: ...

    def remove(self, review_id: str, port: int) -> None: ...

    def reconcile_owned(self, owned_ports: set[int]) -> set[int]: ...


class LifecycleAdapter:
    """Atomically coordinate page, Serve mapping, registry, and port ownership."""

    def __init__(
        self,
        registry: ReviewRegistry,
        ports: PortPool,
        artifacts: ArtifactStore,
        tailnet: TailnetServe,
        build_page: Callable[[str, ReviewRequest], GradioPage],
    ) -> None:
        self.registry = registry
        self.ports = ports
        self._artifacts = artifacts
        self._tailnet = tailnet
        self._build_page = build_page
        self._pages: dict[str, GradioPage] = {}

    def create(self, request: ReviewRequest) -> LifecycleResult:
        if not self._tailnet.https_available():
            return LifecycleResult(diagnostic=DiagnosticCode.TAILNET_HTTPS_UNAVAILABLE)

        page: GradioPage | None = None
        mapped: tuple[str, int] | None = None

        def expose(review_id: str, port: int) -> str:
            nonlocal page, mapped
            page = self._build_page(review_id, request)
            page.launch(port)
            url = self._tailnet.expose(review_id, port)
            mapped = (review_id, port)
            return url

        result = self.registry.create(request, self.ports, self._artifacts, expose)
        if not result.ok:
            if mapped is not None:
                self._remove_mapping(*mapped)
            if page is not None:
                self._close_page(page)
            return result

        assert result.record is not None and page is not None
        self._pages[result.record.review_id] = page
        return result

    def close(self, review_id: str, reason: str = "closed") -> LifecycleResult:
        record = self.registry.get(review_id)
        if record is None or record.state.value == "terminal":
            return self.registry.close(review_id, reason)

        try:
            self._tailnet.remove(record.review_id, record.port)
            page = self._pages.pop(record.review_id, None)
            if page is not None:
                page.close()
        except Exception:
            return LifecycleResult(diagnostic=DiagnosticCode.EXPOSURE_FAILURE)
        return self.registry.close(review_id, reason)

    def recover_after_recycle(self) -> tuple[LifecycleResult, ...]:
        """Terminalize persisted active pages and remove only their owned mappings."""
        results: list[LifecycleResult] = []
        for record in self.registry.active_records():
            try:
                self._tailnet.remove(record.review_id, record.port)
            except Exception:
                results.append(LifecycleResult(diagnostic=DiagnosticCode.EXPOSURE_FAILURE))
                continue
            self._pages.pop(record.review_id, None)
            results.append(self.registry.close(record.review_id, "service_recycled"))
        # Reconcile stale mappings for every port recorded as Gravy-owned.  This
        # intentionally never calls a global tailscale serve reset.
        owned_ports = {record.port for record in self.registry.all_records()}
        try:
            self._tailnet.reconcile_owned(owned_ports)
        except Exception:
            results.append(LifecycleResult(diagnostic=DiagnosticCode.EXPOSURE_FAILURE))
        return tuple(results)

    def _remove_mapping(self, review_id: str, port: int) -> None:
        try:
            self._tailnet.remove(review_id, port)
        except Exception:
            pass

    @staticmethod
    def _close_page(page: GradioPage) -> None:
        try:
            page.close()
        except Exception:
            pass
