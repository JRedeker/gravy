"""Shared persistence and progress primitives for closed review surfaces."""

from __future__ import annotations

import json
from collections.abc import Callable
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

    def latest_decision(self) -> dict[str, Any] | None:
        """Effective decision for a whole-surface surface: the last appended row.

        Revision appends; the latest row wins. Returns ``None`` when no decision
        has been recorded yet, so reconstruction after recycle can distinguish
        "not yet decided" from "decided".
        """
        rows = self._surface_decisions()
        return rows[-1] if rows else None

    def latest_per_key(self, key_fn: Callable[[dict[str, Any]], Any]) -> dict[Any, dict[str, Any]]:
        """Effective decisions for a keyed surface (e.g. checklist by criterion).

        Returns a mapping of key -> latest row. Earlier rows for a revised key are
        preserved in the durable log (append-only) but only the latest per key is
        effective. Returns an empty mapping when no decisions exist.
        """
        latest: dict[Any, dict[str, Any]] = {}
        for row in self._surface_decisions():
            latest[key_fn(row)] = row
        return latest

    def _append(self, decision: dict[str, Any]) -> None:
        self._artifacts.append_decision(self.review_id, decision)
