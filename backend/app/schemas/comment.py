"""Comment Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class CommentSchema(BaseModel):
    section_id: int
    user_id: int
    content: str

    model_config = {"from_attributes": True}


class CommentUserInfo(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str

    model_config = {"from_attributes": True}


class CommentResponse(BaseModel):
    comment_id: int
    user_id: int
    section_id: int
    parent_id: int | None
    content: str
    resolved: bool
    active: bool
    created_at: datetime
    user: CommentUserInfo

    model_config = {"from_attributes": True}
