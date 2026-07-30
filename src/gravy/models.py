"""Durable review state and typed lifecycle diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReviewState(StrEnum):
    ACTIVE = "active"
    TERMINAL = "terminal"


class DiagnosticCode(StrEnum):
    CAPACITY_EXHAUSTED = "capacity_exhausted"
    PORT_UNAVAILABLE = "port_unavailable"
    EXPOSURE_FAILURE = "exposure_failure"
    PERSISTENCE_FAILURE = "persistence_failure"
    UNKNOWN_REVIEW = "unknown_review"
    TERMINAL_REVIEW = "terminal_review"


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    review_id: str
    surface: str
    state: ReviewState
    port: int
    tailnet_url: str
    artifact_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    terminal_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "surface": self.surface,
            "state": self.state.value,
            "port": self.port,
            "tailnet_url": self.tailnet_url,
            "artifact_path": self.artifact_path,
            "metadata": self.metadata,
            "terminal_reason": self.terminal_reason,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ReviewRecord":
        return cls(
            review_id=str(value["review_id"]),
            surface=str(value["surface"]),
            state=ReviewState(value["state"]),
            port=int(value["port"]),
            tailnet_url=str(value["tailnet_url"]),
            artifact_path=str(value["artifact_path"]),
            metadata=dict(value.get("metadata", {})),
            terminal_reason=value.get("terminal_reason"),
        )


@dataclass(frozen=True, slots=True)
class LifecycleResult:
    record: ReviewRecord | None = None
    diagnostic: DiagnosticCode | None = None

    @property
    def ok(self) -> bool:
        return self.record is not None and self.diagnostic is None
