"""Faculty Pydantic schemas."""

from pydantic import BaseModel


class FacultyResponse(BaseModel):
    NUID: int
    FirstName: str | None = None
    LastName: str | None = None
    Email: str | None = None
    Title: str | None = None
    Campus: int | None = None
    Active: bool | None = None
    MaxLoad: int | None = None

    model_config = {"from_attributes": True}
