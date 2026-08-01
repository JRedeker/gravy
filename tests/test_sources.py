import json

import pytest

from gravy.schemas import RequestValidationError
from gravy.sources import resolve_source


def test_resolve_source_csv(tmp_path):
    f = tmp_path / "batch.csv"
    f.write_text("card-001\ncard-002\ncard-003\n")
    result = resolve_source({"surface": "queue", "source": str(f), "options": ["accept", "reject"]})
    assert result["items"] == ["card-001", "card-002", "card-003"]
    assert "source" not in result
    assert result["options"] == ["accept", "reject"]


def test_resolve_source_json(tmp_path):
    f = tmp_path / "batch.json"
    f.write_text(json.dumps(["a", "b", "c"]))
    result = resolve_source({"surface": "gallery", "source": str(f)})
    assert result["items"] == ["a", "b", "c"]


def test_resolve_source_jsonl(tmp_path):
    f = tmp_path / "batch.jsonl"
    f.write_text('"first"\n"second"\n"third"\n')
    result = resolve_source({"surface": "checklist", "source": str(f)})
    assert result["criteria"] == ["first", "second", "third"]


def test_resolve_source_missing_file():
    with pytest.raises(RequestValidationError, match="not found"):
        resolve_source({"surface": "queue", "source": "/nonexistent/file.csv"})


def test_resolve_source_unknown_format(tmp_path):
    f = tmp_path / "batch.txt"
    f.write_text("hello")
    with pytest.raises(RequestValidationError, match="format must be"):
        resolve_source({"surface": "queue", "source": str(f)})


def test_resolve_source_malformed_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json")
    with pytest.raises(RequestValidationError, match="malformed"):
        resolve_source({"surface": "queue", "source": str(f)})


def test_resolve_source_malformed_jsonl(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('"good"\n{bad line\n')
    with pytest.raises(RequestValidationError, match="line 2.*malformed"):
        resolve_source({"surface": "queue", "source": str(f)})


def test_resolve_source_mutual_exclusion(tmp_path):
    f = tmp_path / "batch.csv"
    f.write_text("card-001\n")
    with pytest.raises(RequestValidationError, match="not both"):
        resolve_source({"surface": "queue", "source": str(f), "items": ["existing"]})


def test_resolve_source_no_source():
    result = resolve_source({"surface": "gallery", "items": ["a.png", "b.png"]})
    assert result == {"surface": "gallery", "items": ["a.png", "b.png"]}


def test_resolve_source_url_rejected():
    with pytest.raises(RequestValidationError, match="local file"):
        resolve_source({"surface": "queue", "source": "https://example.com/batch.csv"})


def test_resolve_source_empty_source():
    with pytest.raises(RequestValidationError, match="non-empty"):
        resolve_source({"surface": "queue", "source": ""})


def test_resolve_source_surface_mapping(tmp_path):
    f = tmp_path / "batch.csv"
    f.write_text("a\nb\n")
    # queue -> items
    r = resolve_source({"surface": "queue", "source": str(f)})
    assert "items" in r and "criteria" not in r
    # checklist -> criteria
    r = resolve_source({"surface": "checklist", "source": str(f)})
    assert "criteria" in r and "items" not in r
    # form -> fields
    r = resolve_source({"surface": "form", "source": str(f)})
    assert "fields" in r and "items" not in r


def test_resolve_source_empty_csv(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("")
    with pytest.raises(RequestValidationError, match="no items"):
        resolve_source({"surface": "queue", "source": str(f)})


def test_resolve_source_csv_skips_blank_rows(tmp_path):
    f = tmp_path / "batch.csv"
    f.write_text("card-001\n\n  \ncard-002\n")
    result = resolve_source({"surface": "queue", "source": str(f)})
    assert result["items"] == ["card-001", "card-002"]
