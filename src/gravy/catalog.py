"""Static, closed catalog exposed by the future control-plane adapter."""

from __future__ import annotations

from typing import Any


DEFERRED_SURFACES = ("annotation", "queue", "document", "preview")

_SURFACES = (
    {
        "surface": "gallery",
        "schema": {"surface": "gallery", "items": "non-empty string[]"},
        "example": {"surface": "gallery", "items": ["variant-a.png", "variant-b.png"]},
    },
    {
        "surface": "pairwise",
        "schema": {"surface": "pairwise", "items": "non-empty string[]"},
        "example": {"surface": "pairwise", "items": ["left", "right"]},
    },
    {
        "surface": "form",
        "schema": {"surface": "form", "fields": "non-empty string[]"},
        "example": {"surface": "form", "fields": ["summary", "approved"]},
    },
    {
        "surface": "checklist",
        "schema": {"surface": "checklist", "criteria": "non-empty string[]"},
        "example": {"surface": "checklist", "criteria": ["title is visible"]},
    },
)


def catalog() -> dict[str, Any]:
    """Return copies so callers cannot mutate the durable closed catalog."""
    return {
        "surfaces": tuple(
            {"surface": item["surface"], "schema": dict(item["schema"]), "example": dict(item["example"])}
            for item in _SURFACES
        ),
        "deferred": DEFERRED_SURFACES,
    }
