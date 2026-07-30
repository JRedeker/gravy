from pathlib import Path

from gravy.artifacts import ArtifactStore
from gravy.lifecycle import LifecycleAdapter
from gravy.models import DiagnosticCode, ReviewState
from gravy.ports import PortPool
from gravy.registry import ReviewRegistry
from gravy.schemas import validate_request


class FakePage:
    def __init__(self) -> None:
        self.launched_port: int | None = None
        self.closed = False

    def launch(self, port: int) -> None:
        self.launched_port = port

    def close(self) -> None:
        self.closed = True


class FakeTailnet:
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.mappings: dict[str, int] = {}
        self.removed: list[str] = []

    def https_available(self) -> bool:
        return self.available

    def expose(self, review_id: str, port: int) -> str:
        self.mappings[review_id] = port
        return f"https://{review_id}.tailnet.test"

    def remove(self, review_id: str, port: int) -> None:
        assert self.mappings.get(review_id) == port
        self.mappings.pop(review_id)
        self.removed.append(review_id)


def request():
    return validate_request({"surface": "gallery", "items": ["first.png"]})


def adapter(tmp_path: Path, tailnet: FakeTailnet):
    registry = ReviewRegistry(tmp_path / "registry.json")
    ports = PortPool(41000, 41001)
    pages: list[FakePage] = []

    def build_page(_review_id: str, _request):
        page = FakePage()
        pages.append(page)
        return page

    return LifecycleAdapter(registry, ports, ArtifactStore(tmp_path / "artifacts"), tailnet, build_page), pages


def test_create_launches_a_page_exposes_it_and_close_cleans_owned_resources(tmp_path: Path):
    tailnet = FakeTailnet()
    lifecycle, pages = adapter(tmp_path, tailnet)

    created = lifecycle.create(request())

    assert created.record is not None
    record = created.record
    assert pages[0].launched_port == record.port
    assert tailnet.mappings == {record.review_id: record.port}

    closed = lifecycle.close(record.review_id)

    assert closed.record is not None
    assert closed.record.state is ReviewState.TERMINAL
    assert pages[0].closed
    assert tailnet.mappings == {}
    assert lifecycle.ports.reserved == frozenset()


def test_unavailable_tailnet_does_not_allocate_a_port_or_active_record(tmp_path: Path):
    lifecycle, pages = adapter(tmp_path, FakeTailnet(available=False))

    result = lifecycle.create(request())

    assert result.diagnostic is DiagnosticCode.TAILNET_HTTPS_UNAVAILABLE
    assert pages == []
    assert lifecycle.registry.active_records() == ()
    assert lifecycle.ports.reserved == frozenset()


def test_exposure_failure_closes_the_started_page_and_releases_its_port(tmp_path: Path):
    class FailingTailnet(FakeTailnet):
        def expose(self, review_id: str, port: int) -> str:
            raise OSError("serve failed")

    lifecycle, pages = adapter(tmp_path, FailingTailnet())

    result = lifecycle.create(request())

    assert result.diagnostic is DiagnosticCode.EXPOSURE_FAILURE
    assert pages[0].closed
    assert lifecycle.registry.active_records() == ()
    assert lifecycle.ports.reserved == frozenset()


def test_recycle_marks_only_active_gravy_records_terminal_and_removes_their_mappings(tmp_path: Path):
    tailnet = FakeTailnet()
    lifecycle, _pages = adapter(tmp_path, tailnet)
    first = lifecycle.create(request()).record
    second = lifecycle.create(request()).record
    assert first and second
    tailnet.mappings["foreign-review"] = 49999

    recovered = lifecycle.recover_after_recycle()

    assert {result.record.review_id for result in recovered if result.record} == {first.review_id, second.review_id}
    assert lifecycle.registry.get(first.review_id).state is ReviewState.TERMINAL
    assert lifecycle.registry.get(second.review_id).state is ReviewState.TERMINAL
    assert tailnet.mappings == {"foreign-review": 49999}
