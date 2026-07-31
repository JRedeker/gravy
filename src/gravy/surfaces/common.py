"""Shared persistence and progress primitives for closed review surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gravy.artifacts import ArtifactStore


class SurfaceValidationError(ValueError):
    """Raised when a surface receives a decision outside its closed contract."""


@dataclass(frozen=True, slots=True)
class SurfaceProgress:
    """The state to render after a decision has been durably appended."""

    complete: bool
    remaining: int


class DecisionSurface:
    """Base class that makes decision persistence precede UI progress changes."""

    surface: str

    def __init__(self, review_id: str, artifacts: ArtifactStore) -> None:
        self.review_id = review_id
        self._artifacts = artifacts

    @property
    def _decision_path(self) -> Path:
        return self._artifacts.root / self.review_id / "decisions.jsonl"

    def decisions(self) -> tuple[dict[str, Any], ...]:
        """Read durable decisions; corruption blocks reconstruction rather than guessing."""
        path = self._decision_path
        if not path.exists():
            return ()
        try:
            rows = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)
        except json.JSONDecodeError as exc:
            raise SurfaceValidationError("cannot reconstruct corrupt decision history") from exc
        if any(not isinstance(row, dict) for row in rows):
            raise SurfaceValidationError("decision history must contain JSON objects")
        return rows

    def _surface_decisions(self) -> tuple[dict[str, Any], ...]:
        return tuple(row for row in self.decisions() if row.get("surface") == self.surface)

    def _append(self, decision: dict[str, Any]) -> None:
        self._artifacts.append_decision(self.review_id, decision)
