"""Comment Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class Comment(BaseModel):
    comment_id: int
    schedule_id: int | None = None
    section_id: int | None = None
    user_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    schedule_id: int | None = None
    section_id: int | None = None
    content: str
