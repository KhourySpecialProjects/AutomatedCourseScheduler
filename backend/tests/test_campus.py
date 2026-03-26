"""Tests for campus endpoints and service layer."""

from unittest.mock import MagicMock, call, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Use real enum values from Campus enum
MOCK_CAMPUSES = [
    {"CampusID": 1, "CampusName": "Boston"},
    {"CampusID": 2, "CampusName": "Oakland"},
    {"CampusID": 3, "CampusName": "London"},
]

PATCH_TARGET = "app.routers.campus.campus_service.get_all"


# ---------------------------------------------------------------------------
# Router tests — GET /campuses
# ---------------------------------------------------------------------------


def test_get_campuses_returns_200():
    """GET /campuses returns HTTP 200."""
    with patch(PATCH_TARGET, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    assert response.status_code == 200


def test_get_campuses_returns_list():
    """GET /campuses returns a list."""
    with patch(PATCH_TARGET, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    assert isinstance(response.json(), list)


def test_get_campuses_returns_all_records():
    """GET /campuses returns all campuses."""
    with patch(PATCH_TARGET, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    assert len(response.json()) == 3


def test_get_campuses_response_shape():
    """Each campus object has CampusID and CampusName fields."""
    with patch(PATCH_TARGET, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    for campus in response.json():
        assert "CampusID" in campus
        assert "CampusName" in campus


def test_get_campuses_correct_values():
    """GET /campuses returns correct campus data."""
    with patch(PATCH_TARGET, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    data = response.json()
    assert data[0]["CampusID"] == 1
    assert data[0]["CampusName"] == "Boston"
    assert data[1]["CampusID"] == 2
    assert data[1]["CampusName"] == "Oakland"
    assert data[2]["CampusID"] == 3
    assert data[2]["CampusName"] == "London"


def test_get_campuses_empty():
    """GET /campuses returns empty list when no campuses exist."""
    with patch(PATCH_TARGET, return_value=[]):
        response = client.get("/campuses")
    assert response.status_code == 200
    assert response.json() == []


def test_get_campuses_calls_service_once():
    """GET /campuses calls the service exactly once."""
    with patch(PATCH_TARGET, return_value=MOCK_CAMPUSES) as mock_service:
        client.get("/campuses")
    mock_service.assert_called_once()


def test_get_campuses_passes_no_filters_by_default():
    """GET /campuses passes None for both filters when no query params given."""
    with patch(PATCH_TARGET, return_value=[]) as mock_service:
        client.get("/campuses")
    _, kwargs = mock_service.call_args
    assert kwargs.get("campus_id") is None
    assert kwargs.get("campus_name") is None


def test_get_campuses_filter_by_campus_id():
    """GET /campuses?campus_id=1 passes campus_id to service."""
    with patch(PATCH_TARGET, return_value=[MOCK_CAMPUSES[0]]) as mock_service:
        response = client.get("/campuses?campus_id=1")
    assert response.status_code == 200
    _, kwargs = mock_service.call_args
    assert kwargs.get("campus_id") == 1


def test_get_campuses_filter_by_campus_name():
    """GET /campuses?campus_name=Boston passes campus_name to service."""
    with patch(PATCH_TARGET, return_value=[MOCK_CAMPUSES[0]]) as mock_service:
        response = client.get("/campuses?campus_name=Boston")
    assert response.status_code == 200
    _, kwargs = mock_service.call_args
    assert kwargs.get("campus_name") == "Boston"


def test_get_campuses_filter_both_params():
    """GET /campuses passes both filter params to service when provided."""
    with patch(PATCH_TARGET, return_value=[MOCK_CAMPUSES[0]]) as mock_service:
        client.get("/campuses?campus_id=1&campus_name=Boston")
    _, kwargs = mock_service.call_args
    assert kwargs.get("campus_id") == 1
    assert kwargs.get("campus_name") == "Boston"


def test_get_campuses_single_record():
    """GET /campuses handles a single result correctly."""
    single = [{"CampusID": 1, "CampusName": "Boston"}]
    with patch(PATCH_TARGET, return_value=single):
        response = client.get("/campuses")
    assert len(response.json()) == 1
    assert response.json()[0]["CampusName"] == "Boston"


# ---------------------------------------------------------------------------
# Service layer tests
# ---------------------------------------------------------------------------


def test_service_calls_repo():
    """campus_service.get_all calls the repository."""
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=[]) as mock_repo:
        campus_service.get_all(mock_db)
    mock_repo.assert_called_once_with(mock_db, campus_id=None, campus_name=None)


def test_service_passes_filters_to_repo():
    """campus_service.get_all forwards filter params to repository."""
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=[]) as mock_repo:
        campus_service.get_all(mock_db, campus_id=2, campus_name="Oakland")
    mock_repo.assert_called_once_with(mock_db, campus_id=2, campus_name="Oakland")


def test_service_returns_repo_result():
    """campus_service.get_all returns whatever the repository returns."""
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch(
        "app.services.campus.campus_repo.get_all", return_value=MOCK_CAMPUSES
    ):
        result = campus_service.get_all(mock_db)
    assert result == MOCK_CAMPUSES


def test_service_returns_empty_list_when_repo_empty():
    """campus_service.get_all returns empty list when repo returns empty."""
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=[]):
        result = campus_service.get_all(mock_db)
    assert result == []


# ---------------------------------------------------------------------------
# Repository tests (stubbed until Campus ORM model exists)
# ---------------------------------------------------------------------------


# def test_repo_get_all_returns_list():
#     """campus_repo.get_all returns a list."""
#     from app.repositories import campus as campus_repo

#     mock_db = MagicMock()
#     result = campus_repo.get_all(mock_db)
#     assert isinstance(result, list)


# def test_repo_get_all_returns_empty_stub():
#     """campus_repo.get_all returns empty list in stub state."""
#     from app.repositories import campus as campus_repo

#     mock_db = MagicMock()
#     result = campus_repo.get_all(mock_db)
#     assert result == []