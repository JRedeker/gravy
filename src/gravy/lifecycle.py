"""In-process Gradio and Tailnet lifecycle coordination.

Concrete Gradio and Tailnet integrations stay behind small protocols so the
state machine is deterministic and testable without starting listeners.
"""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
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
        # Registry and Tailnet Serve transitions form one lifecycle critical
        # section; page interaction remains outside this lock.
        self._lifecycle_lock = RLock()

    def create(self, request: ReviewRequest) -> LifecycleResult:
        with self._lifecycle_lock:
            return self._create(request)

    def _create(self, request: ReviewRequest) -> LifecycleResult:
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
        with self._lifecycle_lock:
            return self._close(review_id, reason)

    def _close(self, review_id: str, reason: str = "closed") -> LifecycleResult:
        # Terminalize the durable record first.  Irreversible resource cleanup runs
        # only after persistence succeeds, so a persistence failure never leaves a
        # record active while its external resources are already gone.
        result = self.registry.close(review_id, reason, release_port=False)
        if not result.ok:
            return result

        record = result.record
        assert record is not None
        cleanup_error: str | None = None

        try:
            self._tailnet.remove(record.review_id, record.port)
        except Exception as exc:
            cleanup_error = f"tailnet.remove failed: {exc}"

        page = self._pages.pop(record.review_id, None)
        if page is not None:
            try:
                page.close()
            except Exception as exc:
                cleanup_error = f"{cleanup_error or ''}; page.close failed: {exc}".lstrip("; ")

        self.ports.release(record.port)

        if cleanup_error:
            return LifecycleResult(record=record, diagnostic=DiagnosticCode.EXPOSURE_FAILURE)
        return result

    def recover_after_recycle(self) -> tuple[LifecycleResult, ...]:
        with self._lifecycle_lock:
            return self._recover_after_recycle()

    def _recover_after_recycle(self) -> tuple[LifecycleResult, ...]:
        """Terminalize persisted active pages and remove only their owned mappings.

        Terminal persistence happens before any irreversible cleanup, matching the
        ordering enforced by ``close``.  Tailnet cleanup is best-effort: if
        ``remove`` or ``reconcile_owned`` throws, the review record is still
        terminalized and a readable recovery artifact is written to its artifact
        namespace so submitted decisions remain recoverable.  This intentionally
        never calls a global ``tailscale serve reset``.
        """
        results: list[LifecycleResult] = []
        for record in self.registry.active_records():
            # Persist the terminal state first; do not release the port until cleanup
            # has run so a concurrent create cannot reuse it while a stale mapping
            # may still exist.
            terminal = self.registry.close(
                record.review_id, "service_recycled", release_port=False
            )
            if not terminal.ok:
                results.append(terminal)
                continue
            assert terminal.record is not None

            cleanup_error: str | None = None
            try:
                self._tailnet.remove(terminal.record.review_id, terminal.record.port)
            except Exception as exc:
                cleanup_error = f"{exc}"
            finally:
                self._pages.pop(terminal.record.review_id, None)
                self.ports.release(terminal.record.port)

            # Preserve a readable recovery artifact even if Tailnet cleanup failed.
            self._artifacts.write_recovery(
                terminal.record.review_id,
                {
                    "review_id": terminal.record.review_id,
                    "artifact_path": terminal.record.artifact_path,
                    "terminal_reason": "service_recycled",
                    **({"cleanup_error": cleanup_error} if cleanup_error else {}),
                },
            )

            if cleanup_error:
                results.append(
                    LifecycleResult(
                        record=terminal.record, diagnostic=DiagnosticCode.EXPOSURE_FAILURE
                    )
                )
            else:
                results.append(terminal)

        # Reconcile stale mappings for every port still recorded as Gravy-owned.
        # Ownership-only: never a global reset.
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
