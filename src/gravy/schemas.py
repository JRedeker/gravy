"""Closed request schemas for Gravy's initial review surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, TypeAlias


class RequestValidationError(ValueError):
    """Raised when an untrusted create request is outside the closed union."""


def _string_list(request: Mapping[str, Any], name: str) -> tuple[str, ...]:
    value = request.get(name)
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise RequestValidationError(f"{name} must be a non-empty list of non-empty strings")
    return tuple(value)


def _require_exact_keys(request: Mapping[str, Any], *keys: str) -> None:
    if set(request) != {"surface", *keys}:
        raise RequestValidationError(f"request must contain only: surface, {', '.join(keys)}")


@dataclass(frozen=True, slots=True)
class GalleryRequest:
    surface: Literal["gallery"]
    items: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"surface": self.surface, "items": list(self.items)}


@dataclass(frozen=True, slots=True)
class PairwiseRequest:
    surface: Literal["pairwise"]
    items: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"surface": self.surface, "items": list(self.items)}


@dataclass(frozen=True, slots=True)
class FormRequest:
    surface: Literal["form"]
    fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"surface": self.surface, "fields": list(self.fields)}


@dataclass(frozen=True, slots=True)
class ChecklistRequest:
    surface: Literal["checklist"]
    criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"surface": self.surface, "criteria": list(self.criteria)}


ReviewRequest: TypeAlias = GalleryRequest | PairwiseRequest | FormRequest | ChecklistRequest


def validate_request(request: Mapping[str, Any]) -> ReviewRequest:
    """Parse exactly one supported discriminated request, rejecting every other shape."""
    if not isinstance(request, Mapping):
        raise RequestValidationError("request must be a mapping")

    surface = request.get("surface")
    if surface == "gallery":
        _require_exact_keys(request, "items")
        return GalleryRequest("gallery", _string_list(request, "items"))
    if surface == "pairwise":
        _require_exact_keys(request, "items")
        return PairwiseRequest("pairwise", _string_list(request, "items"))
    if surface == "form":
        _require_exact_keys(request, "fields")
        return FormRequest("form", _string_list(request, "fields"))
    if surface == "checklist":
        _require_exact_keys(request, "criteria")
        return ChecklistRequest("checklist", _string_list(request, "criteria"))
    raise RequestValidationError("surface must be gallery, pairwise, form, or checklist")
