import json
import socket
import time
from pathlib import Path

import pytest

from gravy.artifacts import ArtifactStore
from gravy.gradio_runtime import (
    GRADIO_MAX_THREADS,
    GRADIO_QUEUE_MAX_SIZE,
    GradioBlocksPage,
    ReviewPageController,
)
from gravy.schemas import validate_request


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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


def decisions(tmp_path: Path) -> list[dict[str, object]]:
    path = tmp_path / "artifacts" / "review-one" / "decisions.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_gallery_controller_persists_selection_rank_and_notes(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request({"surface": "gallery", "items": ["a.png", "b.png"]})
    controller = ReviewPageController("review-one", request, artifacts)

    result = controller.gallery_submit("b.png", ["b.png", "a.png"], "Prefer contrast")

    assert result == {"complete": True, "remaining": 0}
    assert decisions(tmp_path) == [
        {"notes": "Prefer contrast", "ranking": ["b.png", "a.png"], "selection": "b.png", "surface": "gallery"}
    ]


def test_pairwise_controller_resumes_without_duplicates(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request({"surface": "pairwise", "items": ["a", "b", "c"]})
    controller = ReviewPageController("review-one", request, artifacts)

    assert controller._surface.current_pair == ("a", "b")
    assert controller.pairwise_choose("left") == {"complete": False, "remaining": 2, "pair": ("a", "c")}

    resumed = ReviewPageController("review-one", request, artifacts)
    assert resumed.pairwise_choose("tie") == {"complete": False, "remaining": 1, "pair": ("b", "c")}
    assert resumed.pairwise_choose("skip") == {"complete": True, "remaining": 0, "pair": None}

    assert decisions(tmp_path) == [
        {"choice": "left", "left": "a", "right": "b", "surface": "pairwise"},
        {"choice": "tie", "left": "a", "right": "c", "surface": "pairwise"},
        {"choice": "skip", "left": "b", "right": "c", "surface": "pairwise"},
    ]


def test_pairwise_choose_pair_controller_route(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request({"surface": "pairwise", "items": ["a", "b", "c"]})
    controller = ReviewPageController("review-one", request, artifacts)

    assert controller.pairwise_choose_pair("a", "b", "left") == {
        "complete": False,
        "remaining": 2,
        "pair": ("a", "c"),
    }
    assert controller.pairwise_choose_pair("a", "b", "right") == {
        "complete": False,
        "remaining": 2,
        "pair": ("a", "c"),
    }

    assert decisions(tmp_path) == [
        {"choice": "left", "left": "a", "right": "b", "surface": "pairwise"},
        {"choice": "right", "left": "a", "right": "b", "surface": "pairwise"},
    ]



def test_form_controller_persists_typed_field_values(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request(
        {
            "surface": "form",
            "fields": [
                {"name": "summary", "type": "text"},
                {"name": "approved", "type": "toggle"},
                {"name": "priority", "type": "option", "options": ["low", "high"]},
                {"name": "notes", "type": "free_text"},
            ],
        }
    )
    controller = ReviewPageController("review-one", request, artifacts)

    result = controller.form_submit(
        {"summary": "Ready", "approved": True, "priority": "high", "notes": "Looks good"}
    )

    assert result == {"complete": True, "remaining": 0}
    assert decisions(tmp_path) == [
        {
            "surface": "form",
            "values": {
                "approved": True,
                "notes": "Looks good",
                "priority": "high",
                "summary": "Ready",
            },
        }
    ]


def test_checklist_controller_persists_pass_fail_and_comment(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request(
        {"surface": "checklist", "criteria": ["Has title", "Has image"]}
    )
    controller = ReviewPageController("review-one", request, artifacts)

    assert controller.checklist_submit("Has title", True, "Visible") == {"complete": False, "remaining": 1}
    assert controller.checklist_submit("Has image", False, "Missing alt") == {"complete": True, "remaining": 0}

    assert decisions(tmp_path) == [
        {"comment": "Visible", "criterion": "Has title", "passed": True, "surface": "checklist"},
        {"comment": "Missing alt", "criterion": "Has image", "passed": False, "surface": "checklist"},
    ]


def test_gradio_blocks_page_launches_and_closes(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request({"surface": "gallery", "items": ["a.png", "b.png"]})
    page = GradioBlocksPage("review-one", request, artifacts)
    port = _free_port()

    page.launch(port)
    try:
        _wait_for_server("127.0.0.1", port)
        assert page._blocks is not None
        assert page._blocks.is_running
    finally:
        page.close()

    assert page._blocks is None
    assert not _port_in_use("127.0.0.1", port)


def test_gradio_blocks_page_uses_bounded_queue_and_thread_settings(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request({"surface": "form", "fields": ["summary"]})
    page = GradioBlocksPage("review-one", request, artifacts)
    port = _free_port()

    page.launch(port)
    try:
        assert page._blocks is not None
        assert page._blocks._queue.max_size == GRADIO_QUEUE_MAX_SIZE
        assert page._blocks.max_threads == GRADIO_MAX_THREADS
    finally:
        page.close()


def test_close_terminates_launch_thread_and_allows_port_reuse(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    request = validate_request({"surface": "gallery", "items": ["a.png", "b.png"]})
    port = _free_port()

    first = GradioBlocksPage("review-one", request, artifacts)
    first.launch(port)
    first.close()
    assert first._blocks is None

    second = GradioBlocksPage("review-one", request, artifacts)
    second.launch(port)
    try:
        _wait_for_server("127.0.0.1", port)
        assert second._blocks is not None
        assert second._blocks.is_running
    finally:
        second.close()
    assert not _port_in_use("127.0.0.1", port)
