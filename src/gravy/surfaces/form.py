"""Closed-field form surface."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .common import DecisionSurface, SurfaceProgress, SurfaceValidationError
from gravy.artifacts import ArtifactStore


class FormSurface(DecisionSurface):
    surface = "form"

    def __init__(self, review_id: str, fields: tuple[str, ...], artifacts: ArtifactStore) -> None:
        super().__init__(review_id, artifacts)
        self._fields = frozenset(fields)

    def submit(self, values: Mapping[str, Any]) -> SurfaceProgress:
        if self._surface_decisions():
            raise SurfaceValidationError("form already has a submission")
        if set(values) != self._fields:
            raise SurfaceValidationError("form values must contain exactly the declared fields")
        copied_values = dict(values)
        try:
            json.dumps(copied_values)
        except (TypeError, ValueError) as exc:
            raise SurfaceValidationError("form values must be JSON data") from exc
        self._append({"surface": self.surface, "values": copied_values})
        return SurfaceProgress(complete=True, remaining=0)
