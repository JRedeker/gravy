"""Resumable pairwise comparison surface.

Scope note (allowSurfaceDecisionRevision): pairwise is intentionally NOT revised
to allow re-deciding past pairs. Unlike gallery/form/checklist, pairwise does not
block resubmission with an immutability error — it advances through combinations
via ``current_pair`` and only raises when all pairs are decided. Revisiting a past
pair would require a new UI navigation feature (previous-pair control or pair
selector), which is out of scope per the change's "no new product features"
boundary. See design.md §D4 for rationale.
"""

from __future__ import annotations

from itertools import combinations
from typing import Literal

from .common import DecisionSurface, SurfaceProgress, SurfaceValidationError
from gravy.artifacts import ArtifactStore

PairwiseChoice = Literal["left", "right", "tie", "skip"]


class PairwiseSurface(DecisionSurface):
    surface = "pairwise"
    _choices = frozenset(("left", "right", "tie", "skip"))

    def __init__(self, review_id: str, items: tuple[str, ...], artifacts: ArtifactStore) -> None:
        super().__init__(review_id, artifacts)
        self._pairs = tuple(combinations(items, 2))

    @property
    def current_pair(self) -> tuple[str, str] | None:
        decided = {(row.get("left"), row.get("right")) for row in self._surface_decisions()}
        return next((pair for pair in self._pairs if pair not in decided), None)

    @property
    def complete(self) -> bool:
        return self.current_pair is None

    def choose(self, choice: PairwiseChoice) -> SurfaceProgress:
        if choice not in self._choices:
            raise SurfaceValidationError("choice must be left, right, tie, or skip")
        pair = self.current_pair
        if pair is None:
            raise SurfaceValidationError("pairwise review is complete")
        self._append({"surface": self.surface, "left": pair[0], "right": pair[1], "choice": choice})
        remaining = sum(1 for candidate in self._pairs if candidate not in {(row.get("left"), row.get("right")) for row in self._surface_decisions()})
        return SurfaceProgress(complete=remaining == 0, remaining=remaining)
