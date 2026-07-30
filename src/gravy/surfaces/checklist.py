"""Criterion-by-criterion pass/fail checklist surface."""

from __future__ import annotations

from .common import DecisionSurface, SurfaceProgress, SurfaceValidationError
from gravy.artifacts import ArtifactStore


class ChecklistSurface(DecisionSurface):
    surface = "checklist"

    def __init__(self, review_id: str, criteria: tuple[str, ...], artifacts: ArtifactStore) -> None:
        super().__init__(review_id, artifacts)
        self._criteria = criteria

    def submit(self, criterion: str, *, passed: bool, comment: str) -> SurfaceProgress:
        decided = {row.get("criterion") for row in self._surface_decisions()}
        if criterion not in self._criteria:
            raise SurfaceValidationError("criterion must be declared by the checklist")
        if criterion in decided:
            raise SurfaceValidationError("criterion already has a decision")
        if not isinstance(passed, bool) or not isinstance(comment, str):
            raise SurfaceValidationError("checklist decisions require a boolean status and text comment")
        self._append({"surface": self.surface, "criterion": criterion, "passed": passed, "comment": comment})
        remaining = len(set(self._criteria) - (decided | {criterion}))
        return SurfaceProgress(complete=remaining == 0, remaining=remaining)
