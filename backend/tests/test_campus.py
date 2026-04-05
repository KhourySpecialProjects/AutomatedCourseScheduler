"""Tests for campus endpoints and service layer."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.campus import Campus

MOCK_CAMPUSES = [
    {"campus_id": 1, "name": "Boston", "active": True},
    {"campus_id": 2, "name": "Oakland", "active": False},
    {"campus_id": 3, "name": "London", "active": True},
]

PATCH_GET_ALL = "app.routers.campus.campus_service.get_all"
PATCH_GET_BY_ID = "app.routers.campus.campus_service.get_by_id"


# ---------------------------------------------------------------------------
# GET /campuses
# ---------------------------------------------------------------------------


def test_get_campuses_returns_200(client):
    with patch(PATCH_GET_ALL, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    assert response.status_code == 200


def test_get_campuses_returns_list(client):
    with patch(PATCH_GET_ALL, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    assert isinstance(response.json(), list)


def test_get_campuses_returns_all_records(client):
    with patch(PATCH_GET_ALL, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    assert len(response.json()) == 3


def test_get_campuses_response_shape(client):
    """Each campus object has campus_id and name fields."""
    with patch(PATCH_GET_ALL, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    for campus in response.json():
        assert "campus_id" in campus
        assert "name" in campus


def test_get_campuses_correct_values(client):
    with patch(PATCH_GET_ALL, return_value=MOCK_CAMPUSES):
        response = client.get("/campuses")
    data = response.json()
    assert data[0]["campus_id"] == 1
    assert data[0]["name"] == "Boston"
    assert data[1]["campus_id"] == 2
    assert data[1]["name"] == "Oakland"
    assert data[2]["campus_id"] == 3
    assert data[2]["name"] == "London"


def test_get_campuses_empty(client):
    with patch(PATCH_GET_ALL, return_value=[]):
        response = client.get("/campuses")
    assert response.status_code == 200
    assert response.json() == []


def test_get_campuses_calls_service_once(client):
    with patch(PATCH_GET_ALL, return_value=MOCK_CAMPUSES) as mock_service:
        client.get("/campuses")
    mock_service.assert_called_once()


def test_get_campuses_passes_no_filter_by_default(client):
    """GET /campuses passes name=None when no query params given."""
    with patch(PATCH_GET_ALL, return_value=[]) as mock_service:
        client.get("/campuses")
    _, kwargs = mock_service.call_args
    assert kwargs.get("name") is None


def test_get_campuses_filter_by_name(client):
    """GET /campuses?name=Boston passes name to service."""
    with patch(PATCH_GET_ALL, return_value=[MOCK_CAMPUSES[0]]) as mock_service:
        response = client.get("/campuses?name=Boston")
    assert response.status_code == 200
    _, kwargs = mock_service.call_args
    assert kwargs.get("name") == "Boston"


def test_get_campuses_single_record(client):
    single = [{"campus_id": 1, "name": "Boston", "active": True}]
    with patch(PATCH_GET_ALL, return_value=single):
        response = client.get("/campuses")
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Boston"


# ---------------------------------------------------------------------------
# GET /campuses/{campus_id}
# ---------------------------------------------------------------------------


def test_get_campus_by_id_returns_200(client):
    with patch(PATCH_GET_BY_ID, return_value=MOCK_CAMPUSES[0]):
        response = client.get("/campuses/1")
    assert response.status_code == 200


def test_get_campus_by_id_correct_values(client):
    with patch(PATCH_GET_BY_ID, return_value=MOCK_CAMPUSES[0]):
        response = client.get("/campuses/1")
    data = response.json()
    assert data["campus_id"] == 1
    assert data["name"] == "Boston"


def test_get_campus_by_id_response_shape(client):
    with patch(PATCH_GET_BY_ID, return_value=MOCK_CAMPUSES[1]):
        response = client.get("/campuses/2")
    data = response.json()
    assert "campus_id" in data
    assert "name" in data


def test_get_campus_by_id_not_found(client):
    from fastapi import HTTPException

    with patch(
        PATCH_GET_BY_ID,
        side_effect=HTTPException(status_code=404, detail="Campus not found"),
    ):
        response = client.get("/campuses/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Campus not found"


def test_get_campus_by_id_calls_service_with_correct_id(client):
    with patch(PATCH_GET_BY_ID, return_value=MOCK_CAMPUSES[2]) as mock_service:
        client.get("/campuses/3")
    mock_service.assert_called_once()


# ---------------------------------------------------------------------------
# Service layer tests
# ---------------------------------------------------------------------------


def test_service_get_all_calls_repo():
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=[]) as mock_repo:
        campus_service.get_all(mock_db)
    mock_repo.assert_called_once_with(mock_db, name=None)


def test_service_get_all_passes_name_filter():
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=[]) as mock_repo:
        campus_service.get_all(mock_db, name="Oakland")
    mock_repo.assert_called_once_with(mock_db, name="Oakland")


def test_service_get_all_returns_repo_result():
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=MOCK_CAMPUSES):
        result = campus_service.get_all(mock_db)
    assert result == MOCK_CAMPUSES


def test_service_get_all_returns_empty_list():
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_all", return_value=[]):
        result = campus_service.get_all(mock_db)
    assert result == []


def test_service_get_by_id_calls_repo():
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch(
        "app.services.campus.campus_repo.get_by_id", return_value=MOCK_CAMPUSES[0]
    ) as mock_repo:
        campus_service.get_by_id(mock_db, 1)
    mock_repo.assert_called_once_with(mock_db, 1)


def test_service_get_by_id_returns_campus():
    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_by_id", return_value=MOCK_CAMPUSES[0]):
        result = campus_service.get_by_id(mock_db, 1)
    assert result == MOCK_CAMPUSES[0]


def test_service_get_by_id_raises_404_when_not_found():
    from fastapi import HTTPException

    from app.services import campus as campus_service

    mock_db = MagicMock()
    with patch("app.services.campus.campus_repo.get_by_id", return_value=None):
        with pytest.raises(HTTPException) as exc:
            campus_service.get_by_id(mock_db, 9999)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Campus not found"


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------


def test_repo_get_all_returns_list(db_session):
    from app.repositories import campus as campus_repo

    result = campus_repo.get_all(db_session)
    assert isinstance(result, list)


def test_repo_get_all_returns_empty_when_no_data(db_session):
    from app.repositories import campus as campus_repo

    result = campus_repo.get_all(db_session)
    assert result == []


def test_repo_get_all_returns_inserted_campus(db_session):
    from app.repositories import campus as campus_repo

    db_session.add(Campus(name="Boston"))
    db_session.commit()
    result = campus_repo.get_all(db_session)
    assert len(result) == 1
    assert result[0].name == "Boston"


def test_repo_get_all_filter_by_name(db_session):
    from app.repositories import campus as campus_repo

    db_session.add_all([Campus(name="Boston"), Campus(name="Oakland")])
    db_session.commit()
    result = campus_repo.get_all(db_session, name="Boston")
    assert len(result) == 1
    assert result[0].name == "Boston"


def test_repo_get_by_id_returns_campus(db_session):
    from app.repositories import campus as campus_repo

    campus = Campus(name="London")
    db_session.add(campus)
    db_session.commit()
    result = campus_repo.get_by_id(db_session, campus.campus_id)
    assert result is not None
    assert result.name == "London"


def test_repo_get_by_id_returns_none_when_not_found(db_session):
    from app.repositories import campus as campus_repo

    result = campus_repo.get_by_id(db_session, 9999)
    assert result is None
