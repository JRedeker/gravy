"""Atomic review registry with failure compensation and ID-only lifecycle calls."""

from __future__ import annotations

import json
import logging
import os
import secrets
import tempfile
from dataclasses import replace
from pathlib import Path
from threading import RLock
from typing import Callable, Mapping

from .artifacts import ArtifactStore
from .models import DiagnosticCode, LifecycleResult, ReviewRecord, ReviewState
from .ports import PortPool
from .schemas import ReviewRequest


_LOGGER = logging.getLogger("gravy.registry")


def _log_exposure_failure(stage: str, exc: BaseException) -> tuple[str, str]:
    """Secret-safe observability: record only stable stage and exception class."""
    exc_class = exc.__class__.__name__
    _LOGGER.warning(
        "lifecycle exposure failure at stage=%s exc_class=%s",
        stage,
        exc_class,
        extra={"stage": stage, "exc_class": exc_class},
    )
    return stage, exc_class


class AtomicJsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, object]:
        if not self.path.exists():
            return {"reviews": {}}
        with self.path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, payload: Mapping[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{self.path.stem}-", suffix=".tmp", dir=self.path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


class ReviewRegistry:
    def __init__(self, path: Path, *, capacity: int = 12) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._store = AtomicJsonStore(path)
        loaded = self._store.load().get("reviews", {})
        self._records = {
            review_id: ReviewRecord.from_dict(record)
            for review_id, record in loaded.items()
        }
        self.capacity = capacity
        self._ports: PortPool | None = None
        self._lock = RLock()

    def _persist(self) -> None:
        self._store.save({"reviews": {review_id: record.to_dict() for review_id, record in self._records.items()}})

    def active_records(self) -> tuple[ReviewRecord, ...]:
        with self._lock:
            return tuple(record for record in self._records.values() if record.state is ReviewState.ACTIVE)

    def all_records(self) -> tuple[ReviewRecord, ...]:
        with self._lock:
            return tuple(self._records.values())

    def get(self, review_id: str) -> ReviewRecord | None:
        with self._lock:
            return self._records.get(review_id)

    def create(
        self,
        request: ReviewRequest,
        ports: PortPool,
        artifacts: ArtifactStore,
        expose: Callable[[str, int], str],
    ) -> LifecycleResult:
        with self._lock:
            if self._ports is not None and self._ports is not ports:
                raise ValueError("a registry uses one bounded port pool")
            self._ports = ports
            if len(self.active_records()) >= self.capacity:
                return LifecycleResult(diagnostic=DiagnosticCode.CAPACITY_EXHAUSTED)
            port = ports.reserve()
            if port is None:
                return LifecycleResult(diagnostic=DiagnosticCode.PORT_UNAVAILABLE)
            review_id = secrets.token_urlsafe(18)
            namespace_created = False
            try:
                tailnet_url = expose(review_id, port)
                namespace = artifacts.create_namespace(review_id)
                namespace_created = True
                record = ReviewRecord(
                    review_id=review_id,
                    surface=request.surface,
                    state=ReviewState.ACTIVE,
                    port=port,
                    tailnet_url=tailnet_url,
                    artifact_path=str(namespace),
                )
                self._records[review_id] = record
                try:
                    self._persist()
                except OSError:
                    self._records.pop(review_id, None)
                    ports.release(port)
                    if namespace_created:
                        artifacts.discard_namespace(review_id)
                    return LifecycleResult(diagnostic=DiagnosticCode.PERSISTENCE_FAILURE)
                return LifecycleResult(record=record)
            except Exception as exc:
                stage, exc_class = _log_exposure_failure("create.expose", exc)
                self._records.pop(review_id, None)
                ports.release(port)
                if namespace_created:
                    artifacts.discard_namespace(review_id)
                return LifecycleResult(
                    diagnostic=DiagnosticCode.EXPOSURE_FAILURE,
                    failure_stage=stage,
                    exception_class=exc_class,
                )

    def update(self, review_id: str, patch: Mapping[str, object]) -> LifecycleResult:
        with self._lock:
            record = self._records.get(review_id)
            if record is None:
                return LifecycleResult(diagnostic=DiagnosticCode.UNKNOWN_REVIEW)
            if record.state is ReviewState.TERMINAL:
                return LifecycleResult(diagnostic=DiagnosticCode.TERMINAL_REVIEW)
            updated = replace(record, metadata={**record.metadata, **patch})
            self._records[review_id] = updated
            try:
                self._persist()
            except OSError:
                self._records[review_id] = record
                return LifecycleResult(diagnostic=DiagnosticCode.PERSISTENCE_FAILURE)
            return LifecycleResult(record=updated)

    def close(
        self,
        review_id: str,
        reason: str = "closed",
        *,
        release_port: bool = True,
    ) -> LifecycleResult:
        with self._lock:
            record = self._records.get(review_id)
            if record is None:
                return LifecycleResult(diagnostic=DiagnosticCode.UNKNOWN_REVIEW)
            if record.state is ReviewState.TERMINAL:
                return LifecycleResult(diagnostic=DiagnosticCode.TERMINAL_REVIEW)
            terminal = replace(record, state=ReviewState.TERMINAL, terminal_reason=reason)
            self._records[review_id] = terminal
            try:
                self._persist()
            except OSError:
                self._records[review_id] = record
                return LifecycleResult(diagnostic=DiagnosticCode.PERSISTENCE_FAILURE)
            if self._ports is not None and release_port:
                self._ports.release(record.port)
            return LifecycleResult(record=terminal)
