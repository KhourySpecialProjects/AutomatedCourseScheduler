from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import comment as comment_repo
from app.repositories import section as section_repo
from app.repositories import user as user_repo
from app.schemas.comment import CommentResponse, CommentSchema

# def _comment_to_response(comment: Comment, section_count: int) -> CommentResponse:
#     return CourseResponse(
#         CourseID=course.course_id,
#         CourseName=course.name,
#         CourseDescription=course.description,
#         CourseNo=None,
#         CourseSubject=None,
#         SectionCount=section_count,
#     )


def get_by_id(db: Session, comment_id: int) -> CommentResponse | None:
    """Return a single comment by ID, or None if not found."""
    return comment_repo.get_by_id(db, comment_id)


def get_comments(db: Session, section_id: int) -> list[CommentResponse]:
    if not section_repo.get_by_id(db, section_id):
        raise HTTPException(status_code=404, detail=f"Section with id {section_id} not found")

    comments = comment_repo.get_by_section(db, section_id)
    return comments


def post_comment(db: Session, commentIn: CommentSchema) -> CommentResponse:
    errors = []
    section = section_repo.get_by_id(db, commentIn.section_id)
    user = user_repo.get_by_id(db, commentIn.user_id)

    if not user:
        errors.append(f"User with id '{commentIn.user_id}' not found")
    if not section:
        errors.append(f"Section with id '{commentIn.section_id}' not found")

    if errors:
        raise ValueError(errors)

    comment = comment_repo.post_comment(db, commentIn)

    return comment


def post_reply(db: Session, replyIn: CommentSchema, parent_id: int) -> CommentResponse:
    errors = []
    section = section_repo.get_by_id(db, replyIn.section_id)
    user = user_repo.get_by_id(db, replyIn.user_id)
    parent_comment = comment_repo.get_by_id(db, parent_id)

    if not user:
        errors.append(f"User with id '{replyIn.user_id}' not found")
    if not section:
        errors.append(f"Section with id '{replyIn.section_id}' not found")
    if not parent_comment:
        errors.append(f"Parent comment with id '{parent_id}' not found")

    if errors:
        raise ValueError(errors)

    # If you "reply to a reply", re-parent to the top-level comment.
    root_parent_id = (
        parent_comment.parent_id
        if parent_comment.parent_id is not None
        else parent_comment.comment_id
    )

    reply = comment_repo.post_reply(db, replyIn, root_parent_id)

    return reply


def delete_comment(db: Session, comment_id: int) -> CommentResponse:
    comment = comment_repo.get_by_id(db, comment_id)
    if not comment:
        raise ValueError(f"Comment with id '{comment_id}' not found")

    deleted = comment_repo.delete_comment(db, comment)

    return deleted


def resolve_comment(db: Session, comment_id: int) -> CommentResponse:
    comment = comment_repo.get_by_id(db, comment_id)
    if not comment:
        raise ValueError(f"Comment with id '{comment_id}' not found")

    resolved = comment_repo.resolve_comment(db, comment)

    return resolved
