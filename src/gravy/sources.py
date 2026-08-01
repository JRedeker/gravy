"""File-source resolution for batch review loading."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .schemas import RequestValidationError

_SOURCE_FIELD = {
    "gallery": "items",
    "pairwise": "items",
    "queue": "items",
    "checklist": "criteria",
    "form": "fields",
}
_REMOTE_PREFIXES = ("http://", "https://", "ftp://")


def resolve_source(request: Mapping[str, Any]) -> dict[str, Any]:
    """If request contains 'source', load items from the file and return a
    resolved request dict with the surface-appropriate field populated.
    Otherwise return the request as a dict copy (unchanged)."""
    result = dict(request)
    source = result.pop("source", None)
    if source is None:
        return result

    if not isinstance(source, str) or not source.strip():
        raise RequestValidationError("source must be a non-empty file path")

    surface = result.get("surface", "")
    target_field = _SOURCE_FIELD.get(surface)
    if target_field is None:
        raise RequestValidationError(f"source is not supported for surface '{surface}'")

    if target_field in result:
        raise RequestValidationError(f"provide either 'source' or '{target_field}', not both")

    result[target_field] = _load_items(source)
    return result


def _load_items(source: str) -> list[str]:
    if source.startswith(_REMOTE_PREFIXES):
        raise RequestValidationError("source must be a local file path, not a URL")
    path = Path(source)
    if not path.is_file():
        raise RequestValidationError(f"source file not found: {source}")
    ext = path.suffix.lower()
    if ext == ".csv":
        return _load_csv(path)
    if ext == ".json":
        return _load_json(path)
    if ext == ".jsonl":
        return _load_jsonl(path)
    raise RequestValidationError(f"source format must be .csv, .json, or .jsonl (got {ext})")


def _load_csv(path: Path) -> list[str]:
    try:
        with open(path, newline="") as f:
            items = [row[0] for row in csv.reader(f) if row and row[0].strip()]
    except OSError as e:
        raise RequestValidationError(f"source file not readable: {e}") from e
    if not items:
        raise RequestValidationError("source CSV contains no items")
    return items


def _load_json(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise RequestValidationError(f"source JSON is malformed: {e}") from e
    except OSError as e:
        raise RequestValidationError(f"source file not readable: {e}") from e
    if not isinstance(data, list) or not all(isinstance(x, str) and x for x in data):
        raise RequestValidationError("source JSON must be an array of non-empty strings")
    return data


def _load_jsonl(path: Path) -> list[str]:
    try:
        text = path.read_text()
    except OSError as e:
        raise RequestValidationError(f"source file not readable: {e}") from e
    items: list[str] = []
    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as e:
            raise RequestValidationError(f"source JSONL line {line_num} is malformed: {e}") from e
        if not isinstance(item, str) or not item:
            raise RequestValidationError(f"source JSONL line {line_num} must be a non-empty string")
        items.append(item)
    if not items:
        raise RequestValidationError("source JSONL contains no items")
    return items
