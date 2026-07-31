from pathlib import Path

import pytest

from gravy.artifacts import ArtifactStore
from gravy.models import DiagnosticCode, ReviewRecord, ReviewState
from gravy.ports import PortPool
from gravy.registry import AtomicJsonStore, ReviewRegistry
from gravy.schemas import validate_request


def gallery_request():
    return validate_request({"surface": "gallery", "items": ["first.png"]})


def test_atomic_file_failure_preserves_existing_metadata(tmp_path: Path, monkeypatch):
    path = tmp_path / "registry.json"
    store = AtomicJsonStore(path)
    original = {"reviews": {"existing": {"state": "active"}}}
    store.save(original)

    def fail_replace(source, destination):
        raise OSError("disk failure")

    monkeypatch.setattr("gravy.registry.os.replace", fail_replace)

    with pytest.raises(OSError, match="disk failure"):
        store.save({"reviews": {}})

    assert store.load() == original
    assert not list(tmp_path.glob(".registry-*.tmp"))


def test_create_rolls_back_port_and_active_state_when_atomic_commit_fails(tmp_path: Path, monkeypatch):
    registry = ReviewRegistry(tmp_path / "registry.json", capacity=12)
    ports = PortPool(41000, 41001)
    artifacts = ArtifactStore(tmp_path / "artifacts")

    def fail_save(self, payload):
        raise OSError("registry unavailable")

    monkeypatch.setattr(AtomicJsonStore, "save", fail_save)
    result = registry.create(gallery_request(), ports, artifacts, lambda review_id, port: f"https://{port}.ts.net")

    assert result.diagnostic is DiagnosticCode.PERSISTENCE_FAILURE
    assert registry.active_records() == ()
    assert ports.reserved == frozenset()
    assert not (tmp_path / "artifacts").exists()


def test_review_identity_prevents_terminal_or_unknown_updates_touching_another_review(tmp_path: Path):
    registry = ReviewRegistry(tmp_path / "registry.json", capacity=12)
    ports = PortPool(41000, 41002)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    url = lambda review_id, port: f"https://{review_id}.example.test:{port}"
    first = registry.create(gallery_request(), ports, artifacts, url)
    second = registry.create(gallery_request(), ports, artifacts, url)

    assert first.record and second.record and first.record.review_id != second.record.review_id
    assert registry.close(first.record.review_id).record.state is ReviewState.TERMINAL
    assert first.record.port not in ports.reserved
    assert registry.update(first.record.review_id, {"note": "ignored"}).diagnostic is DiagnosticCode.TERMINAL_REVIEW
    assert registry.update("unknown", {"note": "ignored"}).diagnostic is DiagnosticCode.UNKNOWN_REVIEW
    assert registry.get(second.record.review_id).state is ReviewState.ACTIVE


def test_capacity_exhaustion_is_a_typed_result(tmp_path: Path):
    registry = ReviewRegistry(tmp_path / "registry.json", capacity=1)
    ports = PortPool(41000, 41001)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    url = lambda review_id, port: f"https://{review_id}.example.test:{port}"

    assert registry.create(gallery_request(), ports, artifacts, url).record is not None
    result = registry.create(gallery_request(), ports, artifacts, url)

    assert result.diagnostic is DiagnosticCode.CAPACITY_EXHAUSTED


def test_decision_append_flushes_and_syncs_before_return(tmp_path: Path, monkeypatch):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    synced = []

    monkeypatch.setattr("gravy.artifacts.os.fsync", lambda descriptor: synced.append(descriptor))

    path = artifacts.append_decision("review-one", {"choice": "left"})

    assert path.read_text(encoding="utf-8") == '{"choice": "left"}\n'
    assert len(synced) == 1
