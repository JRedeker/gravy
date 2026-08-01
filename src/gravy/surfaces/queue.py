"""Bulk triage queue surface — assign each item to an outcome bucket."""

from __future__ import annotations

from typing import Mapping

from .common import DecisionSurface, SurfaceProgress, SurfaceValidationError
from gravy.artifacts import ArtifactStore


class QueueSurface(DecisionSurface):
    surface = "queue"

    def __init__(self, review_id: str, items: tuple[str, ...], options: tuple[str, ...], artifacts: ArtifactStore) -> None:
        super().__init__(review_id, artifacts)
        self._items = frozenset(items)
        self._options = frozenset(options)

    def submit(self, assignments: Mapping[str, str]) -> SurfaceProgress:
        if set(assignments) != self._items:
            raise SurfaceValidationError("assignments must cover every item exactly once")
        if any(bucket not in self._options for bucket in assignments.values()):
            raise SurfaceValidationError("bucket must be one of the declared options")
        self._append({"surface": self.surface, "assignments": dict(assignments)})
        return SurfaceProgress(complete=True, remaining=0)
