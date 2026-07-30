from pathlib import Path

from gravy.control_plane import GravyControlPlane
from gravy.lifecycle import LifecycleAdapter
from gravy.models import DiagnosticCode, ReviewState
from gravy.ports import PortPool
from gravy.registry import ReviewRegistry
from gravy.artifacts import ArtifactStore


class FakePage:
    def launch(self, port: int) -> None:
        self.port = port

    def close(self) -> None:
        pass


class FakeTailnet:
    def __init__(self) -> None:
        self.mappings: dict[str, int] = {}

    def https_available(self) -> bool:
        return True

    def expose(self, review_id: str, port: int) -> str:
        self.mappings[review_id] = port
        return f"https://{review_id}.tailnet.test"

    def remove(self, review_id: str, port: int) -> None:
        assert self.mappings.pop(review_id) == port


def plane(tmp_path: Path) -> GravyControlPlane:
    lifecycle = LifecycleAdapter(
        ReviewRegistry(tmp_path / "registry.json"),
        PortPool(41000, 41002),
        ArtifactStore(tmp_path / "artifacts"),
        FakeTailnet(),
        lambda _request: FakePage(),
    )
    return GravyControlPlane(lifecycle)


def test_control_plane_exposes_only_catalog_create_update_close(tmp_path: Path):
    service = plane(tmp_path)

    assert service.catalog()["deferred"] == ("annotation", "queue", "document", "preview")
    created = service.create("gallery", {"surface": "gallery", "items": ["first.png"]})

    assert created.record is not None
    assert created.record.tailnet_url.startswith("https://")
    updated = service.update(created.record.review_id, {"phase": "reviewing"})
    assert updated.record is not None
    assert updated.record.metadata == {"phase": "reviewing"}
    closed = service.close(created.record.review_id)
    assert closed.record is not None
    assert closed.record.state is ReviewState.TERMINAL


def test_control_plane_rejects_invalid_or_mismatched_create_without_allocation(tmp_path: Path):
    service = plane(tmp_path)

    invalid = service.create("gallery", {"surface": "gallery", "items": []})
    mismatched = service.create("form", {"surface": "gallery", "items": ["first.png"]})

    assert invalid.diagnostic is DiagnosticCode.INVALID_REQUEST
    assert mismatched.diagnostic is DiagnosticCode.INVALID_REQUEST
    assert service.lifecycle.registry.active_records() == ()
    assert service.lifecycle.ports.reserved == frozenset()


def test_startup_recovery_terminalizes_active_records_with_artifact_pointer(tmp_path: Path):
    service = plane(tmp_path)
    created = service.create("gallery", {"surface": "gallery", "items": ["first.png"]})
    assert created.record is not None

    recovered = service.startup_recovery()
    record = service.lifecycle.registry.get(created.record.review_id)

    assert len(recovered) == 1
    assert recovered[0].record is not None
    assert record is not None
    assert record.state is ReviewState.TERMINAL
    assert record.terminal_reason == "service_recycled"
    assert record.artifact_path.endswith(created.record.review_id)
