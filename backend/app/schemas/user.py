"""User and invite Pydantic schemas."""

import re

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserResponse(BaseModel):
    user_id: int
    nuid: int
    first_name: str
    last_name: str
    email: str
    role: str
    active: bool

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    nuid: int = Field(..., gt=0)
    role: str = Field(default="VIEWER")

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("ADMIN", "VIEWER"):
            raise ValueError("Role must be 'ADMIN' or 'VIEWER'")
        return v


class InviteResponse(BaseModel):
    user: UserResponse
    signup_url: str


class AdminInviteRequest(BaseModel):
    """Pending admin user + Auth0 signup URL (no faculty row; same linking as bootstrap_admin)."""

    nuid: int = Field(..., gt=0)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=100)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("This field is required")
        return s

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        s = v.strip()
        if len(s) > 100 or not _EMAIL_RE.match(s):
            raise ValueError("Invalid email address")
        return s


class InviteLinkResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    invite_link: str
