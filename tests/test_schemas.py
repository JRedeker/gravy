import pytest

from gravy.catalog import catalog
from gravy.schemas import RequestValidationError, validate_request


def test_catalog_is_closed_to_the_five_supported_surfaces():
    listing = catalog()

    assert tuple(item["surface"] for item in listing["surfaces"]) == (
        "gallery",
        "pairwise",
        "form",
        "checklist",
        "queue",
    )
    assert listing["deferred"] == ("annotation", "document", "preview")
    assert all("example" in item and "schema" in item for item in listing["surfaces"])


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"surface": "custom", "items": ["a"]},
        {"surface": "gallery", "items": []},
        {"surface": "form", "fields": "not-a-list"},
        {"surface": "checklist", "criteria": ["works", 3]},
    ],
)
def test_invalid_discriminated_requests_are_rejected(payload):
    with pytest.raises(RequestValidationError):
        validate_request(payload)


def test_checklist_remains_its_own_discriminated_schema():
    request = validate_request({"surface": "checklist", "criteria": ["shows a title"]})

    assert request.surface == "checklist"
    assert request.to_dict() == {"surface": "checklist", "criteria": ["shows a title"]}


def test_queue_request_validates_items_and_options():
    request = validate_request({"surface": "queue", "items": ["a", "b"], "options": ["accept", "reject"]})

    assert request.surface == "queue"
    assert request.items == ("a", "b")
    assert request.options == ("accept", "reject")
    assert request.to_dict() == {"surface": "queue", "items": ["a", "b"], "options": ["accept", "reject"]}


def test_queue_request_rejects_missing_options():
    with pytest.raises(RequestValidationError):
        validate_request({"surface": "queue", "items": ["a"]})


def test_queue_request_rejects_fewer_than_two_options():
    with pytest.raises(RequestValidationError):
        validate_request({"surface": "queue", "items": ["a"], "options": ["only"]})
