"""User and invite Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator


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
    role: str = Field(default="viewer")

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "viewer"):
            raise ValueError("Role must be 'admin' or 'viewer'")
        return v


class InviteResponse(BaseModel):
    user: UserResponse
    signup_url: str
