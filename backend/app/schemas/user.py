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


class InviteLinkResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    invite_link: str
