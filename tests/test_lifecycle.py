import concurrent.futures
import json
import multiprocessing
import socket
import time
from pathlib import Path

from gravy.artifacts import ArtifactStore
from gravy.gradio_runtime import GradioBlocksPage
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
        self.reconciled: set[int] = set()

    def https_available(self) -> bool:
        return self.available

    def expose(self, review_id: str, port: int) -> str:
        self.mappings[review_id] = port
        return f"https://{review_id}.tailnet.test"

    def remove(self, review_id: str, port: int) -> None:
        assert self.mappings.get(review_id) == port
        self.mappings.pop(review_id)
        self.removed.append(review_id)

    def reconcile_owned(self, owned_ports: set[int]) -> set[int]:
        removed: set[int] = set()
        for review_id, port in list(self.mappings.items()):
            if port in owned_ports:
                self.mappings.pop(review_id)
                self.removed.append(review_id)
                self.reconciled.add(port)
                removed.add(port)
        return removed


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

    # Close the first review normally, then simulate a stale Serve mapping that
    # was not removed (e.g. after an unclean shutdown).
    lifecycle.close(first.review_id)
    tailnet.mappings["stale-owned"] = first.port
    tailnet.mappings["foreign-review"] = 49999

    recovered = lifecycle.recover_after_recycle()

    assert {result.record.review_id for result in recovered if result.record} == {second.review_id}
    assert lifecycle.registry.get(first.review_id).state is ReviewState.TERMINAL
    assert lifecycle.registry.get(second.review_id).state is ReviewState.TERMINAL
    # Only Gravy-owned stale mappings are removed; foreign mappings are preserved.
    assert tailnet.mappings == {"foreign-review": 49999}
    assert first.port in tailnet.reconciled
    assert 49999 not in tailnet.reconciled


def _wait_for_server(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.05)
    raise TimeoutError(f"server on {host}:{port} did not start") from last_error


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def test_ten_concurrent_creates_use_distinct_ports_and_namespaces(tmp_path: Path):
    """Ten simultaneous creates yield distinct IDs, ports, URLs, and namespaces."""
    registry = ReviewRegistry(tmp_path / "registry.json")
    ports = PortPool(41000, 41011)  # 12 ports, satisfies the >=10-port pool requirement
    artifacts = ArtifactStore(tmp_path / "artifacts")
    pages: list[FakePage] = []
    tailnet = FakeTailnet()

    def build_page(_review_id: str, _request):
        page = FakePage()
        pages.append(page)
        return page

    lifecycle = LifecycleAdapter(registry, ports, artifacts, tailnet, build_page)

    def create_one(_):
        return lifecycle.create(request())

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(create_one, range(10)))

    records = [r.record for r in results if r.record]
    assert len(records) == 10
    assert len({r.review_id for r in records}) == 10
    assert len({r.port for r in records}) == 10
    assert len({r.tailnet_url for r in records}) == 10
    assert len({r.artifact_path for r in records}) == 10
    assert all(r.state is ReviewState.ACTIVE for r in records)
    assert len(lifecycle.registry.active_records()) == 10
    assert len(lifecycle.ports.reserved) == 10
    assert len(tailnet.mappings) == 10

    launched_ports = {p.launched_port for p in pages}
    assert len(launched_ports) == 10
    assert launched_ports == {r.port for r in records}


def gallery_request():
    return validate_request(
        {"surface": "gallery", "items": ["a.png", "b.png", "c.png"]}
    )


def test_ten_concurrent_active_reviews_record_durable_decisions_via_controller(
    tmp_path: Path,
):
    """AC3: ten simultaneous creates each progress via the page controller.

    Every active review records a durable decision through its real
    GradioBlocksPage controller without queue starvation.
    """
    registry = ReviewRegistry(tmp_path / "registry.json")
    ports = PortPool(41000, 41011)  # 12 ports, satisfies >=10 concurrent reviews
    artifacts = ArtifactStore(tmp_path / "artifacts")
    tailnet = FakeTailnet()

    def build_page(review_id: str, request):
        return GradioBlocksPage(review_id, request, artifacts)

    lifecycle = LifecycleAdapter(registry, ports, artifacts, tailnet, build_page)

    def create_one(_):
        return lifecycle.create(gallery_request())

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(create_one, range(10)))

    records = [r.record for r in results if r.record]
    assert len(records) == 10
    assert len({r.review_id for r in records}) == 10
    assert len({r.port for r in records}) == 10

    for record in records:
        _wait_for_server("127.0.0.1", record.port)

    def submit_for(record):
        page = lifecycle._pages[record.review_id]
        assert isinstance(page, GradioBlocksPage)
        # Real page/controller pathway: call the controller bound to the Blocks.
        progress = page._controller.gallery_submit(
            selection="b.png",
            ranking=["b.png", "a.png", "c.png"],
            notes="selected via controller",
        )
        return record.review_id, progress

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        progress_results = list(executor.map(submit_for, records))

    assert len(progress_results) == 10
    for review_id, progress in progress_results:
        assert progress == {"complete": True, "remaining": 0}
        decision_path = Path(artifacts.root) / review_id / "decisions.jsonl"
        assert decision_path.exists()
        decisions = [
            json.loads(line)
            for line in decision_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        assert decisions == [
            {
                "notes": "selected via controller",
                "ranking": ["b.png", "a.png", "c.png"],
                "selection": "b.png",
                "surface": "gallery",
            }
        ]

    for record in records:
        lifecycle.close(record.review_id)
        assert registry.get(record.review_id).state is ReviewState.TERMINAL


def test_close_recycle_with_real_gradio_releases_listener_and_preserves_artifacts(tmp_path: Path):
    """Real Gradio teardown after close/recycle leaves no listener or subprocess."""
    registry = ReviewRegistry(tmp_path / "registry.json")
    ports = PortPool(41000, 41002)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    tailnet = FakeTailnet()

    def build_page(review_id: str, request):
        return GradioBlocksPage(review_id, request, artifacts)

    lifecycle = LifecycleAdapter(registry, ports, artifacts, tailnet, build_page)

    created = lifecycle.create(request())
    assert created.record is not None
    record = created.record
    _wait_for_server("127.0.0.1", record.port)
    assert _port_in_use("127.0.0.1", record.port)
    page = lifecycle._pages[record.review_id]
    assert isinstance(page, GradioBlocksPage)
    assert page._blocks is not None
    assert page._blocks.is_running
    launch_thread = page._blocks.server.thread
    assert launch_thread.is_alive()

    closed = lifecycle.close(record.review_id)
    assert closed.record is not None
    assert closed.record.state is ReviewState.TERMINAL
    assert not _port_in_use("127.0.0.1", record.port)
    assert page._blocks is None
    assert not launch_thread.is_alive()
    assert multiprocessing.active_children() == []

    second = lifecycle.create(request())
    assert second.record is not None
    artifacts.append_decision(second.record.review_id, {"choice": "left"})
    second_page = lifecycle._pages[second.record.review_id]
    assert isinstance(second_page, GradioBlocksPage)

    recovered = lifecycle.recover_after_recycle()
    recovered_ids = {r.record.review_id for r in recovered if r.record}
    assert second.record.review_id in recovered_ids

    second_record = registry.get(second.record.review_id)
    assert second_record is not None
    assert second_record.state is ReviewState.TERMINAL
    assert second_record.terminal_reason == "service_recycled"
    assert (Path(second_record.artifact_path) / "decisions.jsonl").exists()
    assert second.record.review_id not in tailnet.mappings

    # The page is not closed by recycle (Vision recycle kills the process), so
    # close it explicitly here to keep the test process clean and verify the
    # listener is released.
    second_page.close()
    assert second_page._blocks is None
    assert not _port_in_use("127.0.0.1", second.record.port)
    assert multiprocessing.active_children() == []


def test_recycle_terminalizes_active_reviews_and_preserves_recovery_artifact_despite_cleanup_failure(
    tmp_path: Path,
):
    """RED regression: even if Tailnet cleanup/reconciliation throws, every active
    review becomes terminal and a readable recovery artifact is preserved.
    """

    class CleanupFailingTailnet(FakeTailnet):
        def remove(self, review_id: str, port: int) -> None:
            raise OSError(f"cleanup refused for {review_id}")

        def reconcile_owned(self, owned_ports: set[int]) -> set[int]:
            raise RuntimeError("reconcile refused")

    tailnet = CleanupFailingTailnet()
    lifecycle, pages = adapter(tmp_path, tailnet)
    first = lifecycle.create(request()).record
    second = lifecycle.create(request()).record
    assert first and second

    # Seed a pre-existing decision artifact to prove it survives recycle.
    decision_path = lifecycle._artifacts.append_decision(
        first.review_id, {"note": "pre-recycle"}
    )

    recovered = lifecycle.recover_after_recycle()

    # Every active review is terminal, regardless of cleanup failures.
    assert lifecycle.registry.get(first.review_id).state is ReviewState.TERMINAL
    assert lifecycle.registry.get(second.review_id).state is ReviewState.TERMINAL
    assert lifecycle.registry.get(first.review_id).terminal_reason == "service_recycled"
    assert lifecycle.registry.get(second.review_id).terminal_reason == "service_recycled"
    # Ports are released so the pool can be reused.
    assert lifecycle.ports.reserved == frozenset()

    # A readable recovery artifact is preserved for each review.
    for record in (first, second):
        recovery_path = Path(record.artifact_path) / "recovery.json"
        assert recovery_path.exists()
        recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
        assert recovery["review_id"] == record.review_id
        assert recovery["terminal_reason"] == "service_recycled"
        assert Path(recovery["artifact_path"]) == Path(record.artifact_path)
        assert "cleanup_error" in recovery

    # Pre-existing decisions are not deleted.
    assert decision_path.exists()
    decisions = [
        json.loads(line)
        for line in decision_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert decisions == [{"note": "pre-recycle"}]

    # Recovery results include terminal records for both active reviews and a
    # diagnostic for the reconcile failure, but never leave an active record.
    terminal_ids = {
        result.record.review_id
        for result in recovered
        if result.record and result.record.state is ReviewState.TERMINAL
    }
    assert terminal_ids == {first.review_id, second.review_id}
    diagnostics = [result.diagnostic for result in recovered if result.diagnostic]
    assert DiagnosticCode.EXPOSURE_FAILURE in diagnostics
    assert all(
        result.record is None or result.record.state is ReviewState.TERMINAL
        for result in recovered
    )
