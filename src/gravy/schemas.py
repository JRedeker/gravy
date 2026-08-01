"""Closed request schemas for Gravy's initial review surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, TypeAlias


FIELD_TYPES = ("text", "image", "option", "toggle", "free_text")


class RequestValidationError(ValueError):
    """Raised when an untrusted create request is outside the closed union."""


@dataclass(frozen=True, slots=True)
class FormField:
    """Typed descriptor for a single form field."""

    name: str
    type: Literal["text", "image", "option", "toggle", "free_text"] = "text"
    label: str | None = None
    options: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"name": self.name, "type": self.type}
        if self.label is not None:
            value["label"] = self.label
        if self.options:
            value["options"] = list(self.options)
        return value


def _form_field(value: Any) -> str | FormField:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, Mapping):
        name = value.get("name")
        if not isinstance(name, str) or not name:
            raise RequestValidationError("form field descriptor must have a non-empty name")
        ftype = value.get("type", "text")
        if ftype not in FIELD_TYPES:
            raise RequestValidationError(
                f"form field type must be one of: {', '.join(FIELD_TYPES)}"
            )
        label = value.get("label")
        if label is not None and not isinstance(label, str):
            raise RequestValidationError("form field label must be a string")
        options = value.get("options", [])
        if not isinstance(options, list) or any(
            not isinstance(option, str) or not option for option in options
        ):
            raise RequestValidationError(
                "form field options must be a list of non-empty strings"
            )
        if ftype == "option" and len(options) < 2:
            raise RequestValidationError(
                "option field requires at least two options"
            )
        return FormField(
            name=name,
            type=ftype,
            label=label,
            options=tuple(options),
        )
    raise RequestValidationError(
        "form field must be a non-empty string or descriptor"
    )


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
    fields: tuple[str | FormField, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "fields": [
                field if isinstance(field, str) else field.to_dict()
                for field in self.fields
            ],
        }


@dataclass(frozen=True, slots=True)
class ChecklistRequest:
    surface: Literal["checklist"]
    criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"surface": self.surface, "criteria": list(self.criteria)}


@dataclass(frozen=True, slots=True)
class QueueRequest:
    surface: Literal["queue"]
    items: tuple[str, ...]
    options: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"surface": self.surface, "items": list(self.items), "options": list(self.options)}


ReviewRequest: TypeAlias = GalleryRequest | PairwiseRequest | FormRequest | ChecklistRequest | QueueRequest


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
        fields_raw = request.get("fields")
        if not isinstance(fields_raw, list) or not fields_raw:
            raise RequestValidationError("fields must be a non-empty list")
        return FormRequest("form", tuple(_form_field(item) for item in fields_raw))
    if surface == "checklist":
        _require_exact_keys(request, "criteria")
        return ChecklistRequest("checklist", _string_list(request, "criteria"))
    if surface == "queue":
        _require_exact_keys(request, "items", "options")
        items = _string_list(request, "items")
        options = _string_list(request, "options")
        if len(options) < 2:
            raise RequestValidationError("queue options must have at least two entries")
        return QueueRequest("queue", items, options)
    raise RequestValidationError("surface must be gallery, pairwise, form, checklist, or queue")
