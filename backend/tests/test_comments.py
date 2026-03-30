"""Tests for comment routes.

These tests describe CORRECT expected behavior. Several will currently fail
due to known bugs in the router (documented per test).
"""

from datetime import datetime

from app.models import Comment, Schedule, Section, User
from app.models.campus import Campus
from app.models.semester import Semester as SemesterModel

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_campus(db, name="Boston"):
    campus = Campus(name=name)
    db.add(campus)
    db.flush()
    return campus


def _make_user(db, nuid=1):
    user = User(
        nuid=nuid,
        first_name="Test",
        last_name="User",
        email=f"user{nuid}@test.com",
        phone_number="1234567890",
    )
    db.add(user)
    db.commit()
    return user


def _make_schedule(db):
    campus = _make_campus(db)
    semester = SemesterModel(
        name="Fall 2024",
        start_date=datetime(2024, 9, 1),
        end_date=datetime(2024, 12, 31),
    )
    db.add(semester)
    db.flush()
    schedule = Schedule(
        name="Test Schedule",
        semester_id=semester.semester_id,
        year=2024,
        campus=campus.campus_id,
    )
    db.add(schedule)
    db.commit()
    return schedule


def _make_section(db, schedule_id):
    section = Section(
        schedule_id=schedule_id,
        time_block_id=1,
        course_id=1,
        section_number=1,
        capacity=30,
    )
    db.add(section)
    db.commit()
    return section


def _make_comment(db, user_id, section_id, content="A comment", parent_id=None):
    comment = Comment(
        user_id=user_id,
        section_id=section_id,
        content=content,
        parent_id=parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# ---------------------------------------------------------------------------
# POST /comments  — top-level comments
# ---------------------------------------------------------------------------


def test_post_comment_success(client, db_session):
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)

    response = client.post(
        "/comments",
        json={
            "user_id": user.nuid,
            "section_id": section.section_id,
            "parent_id": None,
            "content": "Looks good to me",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user.nuid
    assert data["section_id"] == section.section_id
    assert data["content"] == "Looks good to me"
    assert data["resolved"] is False
    assert "comment_id" in data
    assert "created_at" in data


def test_post_comment_persisted_to_db(client, db_session):
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)

    client.post(
        "/comments",
        json={
            "user_id": user.nuid,
            "section_id": section.section_id,
            "parent_id": None,
            "content": "Persisted comment",
        },
    )

    db_session.expire_all()
    comment = db_session.query(Comment).first()
    assert comment is not None
    assert comment.content == "Persisted comment"
    assert comment.user_id == user.nuid
    assert comment.section_id == section.section_id


def test_post_comment_user_not_found(client, db_session):
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)

    response = client.post(
        "/comments",
        json={
            "user_id": 9999,
            "section_id": section.section_id,
            "parent_id": None,
            "content": "Ghost comment",
        },
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("9999" in e for e in errors)


def test_post_comment_section_not_found(client, db_session):
    """
    BUG: the error string is missing a closing quote around section_id
    (f"Section with id '{commentIn.section_id} not found" — no closing ').
    The test asserts the correct error message format.
    """
    user = _make_user(db_session)

    response = client.post(
        "/comments",
        json={
            "user_id": user.nuid,
            "section_id": 9999,
            "parent_id": None,
            "content": "Section-less comment",
        },
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("9999" in e for e in errors)
    assert any(e == "Section with id '9999' not found" for e in errors)


def test_post_comment_user_and_section_not_found(client, db_session):
    response = client.post(
        "/comments",
        json={
            "user_id": 9999,
            "section_id": 8888,
            "parent_id": None,
            "content": "Nothing exists",
        },
    )

    assert response.status_code == 422
    assert len(response.json()["detail"]) == 2


# ---------------------------------------------------------------------------
# POST /comments  — replies
# ---------------------------------------------------------------------------


def test_post_reply_success(client, db_session):
    """A reply should be created and stored with parent_id set."""
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)
    parent = _make_comment(db_session, user.nuid, section.section_id, "Parent comment")

    response = client.post(
        f"/comments/{parent.comment_id}",
        json={
            "user_id": user.nuid,
            "section_id": section.section_id,
            "content": "This is a reply",
        },
    )

    assert response.status_code == 201

    db_session.expire_all()
    reply = (
        db_session.query(Comment).filter(Comment.content == "This is a reply").first()
    )
    assert reply is not None
    assert reply.parent_id == parent.comment_id


def test_post_reply_invalid_parent_returns_422(client, db_session):
    """Supplying a non-existent parent_id should return 422."""
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)

    response = client.post(
        "/comments/9999",
        json={
            "user_id": user.nuid,
            "section_id": section.section_id,
            "content": "Reply to nowhere",
        },
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("9999" in e for e in errors)


# ---------------------------------------------------------------------------
# GET /comments/{section_id}
# ---------------------------------------------------------------------------


def test_get_comments_section_not_found(client, db_session):
    response = client.get("/comments/9999")
    assert response.status_code == 404
    assert "9999" in response.json()["detail"]


def test_get_comments_section_with_no_comments_returns_empty_list(client, db_session):
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)

    response = client.get(f"/comments/{section.section_id}")

    assert response.status_code == 200
    assert response.json() == []


def test_get_comments_returns_comments_for_section(client, db_session):
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)
    _make_comment(db_session, user.nuid, section.section_id, "First comment")
    _make_comment(db_session, user.nuid, section.section_id, "Second comment")

    response = client.get(f"/comments/{section.section_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    contents = {c["content"] for c in data}
    assert contents == {"First comment", "Second comment"}
    for item in data:
        assert "comment_id" in item
        assert "user_id" in item
        assert "section_id" in item
        assert "resolved" in item
        assert "created_at" in item


def test_get_comments_only_returns_comments_for_requested_section(client, db_session):
    """Comments from other sections must not appear in the response."""
    user = _make_user(db_session)
    schedule_id = _make_schedule(db_session).schedule_id
    section_a = _make_section(db_session, schedule_id)
    section_b = _make_section(db_session, schedule_id)
    _make_comment(db_session, user.nuid, section_a.section_id, "Comment on A")
    _make_comment(db_session, user.nuid, section_b.section_id, "Comment on B")

    response = client.get(f"/comments/{section_a.section_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Comment on A"


# ---------------------------------------------------------------------------
# DELETE /comments/{comment_id}
# ---------------------------------------------------------------------------


def test_delete_comment_success(client, db_session):
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)
    comment = _make_comment(db_session, user.nuid, section.section_id)

    response = client.delete(f"/comments/{comment.comment_id}")

    assert response.status_code == 200

    db_session.expire_all()
    updated = db_session.get(Comment, comment.comment_id)
    assert updated.active is False


def test_delete_comment_not_found_returns_404(client, db_session):
    response = client.delete("/comments/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /comments/{comment_id}  — resolve
# ---------------------------------------------------------------------------


def test_resolve_comment_success(client, db_session):
    user = _make_user(db_session)
    section = _make_section(db_session, _make_schedule(db_session).schedule_id)
    comment = _make_comment(db_session, user.nuid, section.section_id)
    assert comment.resolved is False

    response = client.put(f"/comments/{comment.comment_id}")

    assert response.status_code == 204

    db_session.expire_all()
    updated = db_session.get(Comment, comment.comment_id)
    assert updated.resolved is True


def test_resolve_comment_not_found_returns_404(client, db_session):
    response = client.put("/comments/9999")
    assert response.status_code == 404
