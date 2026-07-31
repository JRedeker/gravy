"""Gallery selection and ranking surface."""

from __future__ import annotations

from .common import DecisionSurface, SurfaceProgress, SurfaceValidationError
from gravy.artifacts import ArtifactStore


class GallerySurface(DecisionSurface):
    surface = "gallery"

    def __init__(self, review_id: str, items: tuple[str, ...], artifacts: ArtifactStore) -> None:
        super().__init__(review_id, artifacts)
        self.items = items

    def submit(self, *, selection: str, ranking: tuple[str, ...], notes: str) -> SurfaceProgress:
        if self._surface_decisions():
            raise SurfaceValidationError("gallery already has a decision")
        if selection not in self.items:
            raise SurfaceValidationError("selection must be a gallery item")
        if len(ranking) != len(self.items) or set(ranking) != set(self.items):
            raise SurfaceValidationError("ranking must contain every gallery item exactly once")
        if not isinstance(notes, str):
            raise SurfaceValidationError("notes must be text")
        self._append({"surface": self.surface, "selection": selection, "ranking": list(ranking), "notes": notes})
        return SurfaceProgress(complete=True, remaining=0)
