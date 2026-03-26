"""Comment Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class CommentSchema(BaseModel):
    section_id: int
    parent_id: int | None
    user_id: int
    content: str

    model_config = {"from_attributes": True}


class CommentResponse(BaseModel):
    comment_id: int
    user_id: int
    section_id: int
    content: str
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}