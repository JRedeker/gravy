import pytest

from gravy.catalog import catalog
from gravy.schemas import RequestValidationError, validate_request


def test_catalog_is_closed_to_the_four_supported_surfaces():
    listing = catalog()

    assert tuple(item["surface"] for item in listing["surfaces"]) == (
        "gallery",
        "pairwise",
        "form",
        "checklist",
    )
    assert listing["deferred"] == ("annotation", "queue", "document", "preview")
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
