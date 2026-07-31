import json
from pathlib import Path

from gravy.artifacts import ArtifactStore
from gravy.surfaces.checklist import ChecklistSurface
from gravy.surfaces.form import FormSurface
from gravy.surfaces.gallery import GallerySurface
from gravy.surfaces.pairwise import PairwiseSurface


def store(tmp_path: Path) -> ArtifactStore:
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.create_namespace("review-one")
    return artifacts


def decisions(tmp_path: Path) -> list[dict[str, object]]:
    path = tmp_path / "artifacts" / "review-one" / "decisions.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_gallery_persists_selection_rank_and_notes_before_advancing(tmp_path: Path):
    surface = GallerySurface("review-one", ("a.png", "b.png"), store(tmp_path))

    result = surface.submit(selection="b.png", ranking=("b.png", "a.png"), notes="Prefer contrast")

    assert decisions(tmp_path) == [
        {"notes": "Prefer contrast", "ranking": ["b.png", "a.png"], "selection": "b.png", "surface": "gallery"}
    ]
    assert result.complete


def test_pairwise_resumes_at_first_undecided_comparison_without_duplicates(tmp_path: Path):
    artifacts = store(tmp_path)
    first = PairwiseSurface("review-one", ("a", "b", "c"), artifacts)

    assert first.current_pair == ("a", "b")
    assert not first.choose("left").complete
    resumed = PairwiseSurface("review-one", ("a", "b", "c"), artifacts)

    assert resumed.current_pair == ("a", "c")
    resumed.choose("tie")
    resumed.choose("skip")

    assert decisions(tmp_path) == [
        {"choice": "left", "left": "a", "right": "b", "surface": "pairwise"},
        {"choice": "tie", "left": "a", "right": "c", "surface": "pairwise"},
        {"choice": "skip", "left": "b", "right": "c", "surface": "pairwise"},
    ]
    assert resumed.complete


def test_form_persists_closed_field_values(tmp_path: Path):
    surface = FormSurface("review-one", ("summary", "approved"), store(tmp_path))

    result = surface.submit({"summary": "Ready", "approved": True})

    assert result.complete
    assert decisions(tmp_path) == [
        {"surface": "form", "values": {"approved": True, "summary": "Ready"}}
    ]


def test_checklist_persists_explicit_status_and_comment_per_criterion(tmp_path: Path):
    surface = ChecklistSurface("review-one", ("Has title", "Has image"), store(tmp_path))

    assert not surface.submit("Has title", passed=True, comment="Visible").complete
    result = surface.submit("Has image", passed=False, comment="Missing alt")

    assert result.complete
    assert decisions(tmp_path) == [
        {"comment": "Visible", "criterion": "Has title", "passed": True, "surface": "checklist"},
        {"comment": "Missing alt", "criterion": "Has image", "passed": False, "surface": "checklist"},
    ]
