"""Faculty Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator

from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo


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


class FacultyCreate(BaseModel):
    nuid: int = Field(..., gt=0)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    campus: str = Field(..., min_length=1)
    phone_number: str | None = None
    title: str | None = None
    active: bool = True

    @field_validator("first_name", "last_name", "email", "campus")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v


class FacultyUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    campus: str | None = None
    phone_number: str | None = None
    title: str | None = None
    active: bool | None = None

    @field_validator("first_name", "last_name", "email", "campus")
    @classmethod
    def not_empty_optional(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty")
        return v


class FacultyProfileResponse(BaseModel):
    nuid: int
    first_name: str
    last_name: str
    email: str
    title: str | None = None
    campus: str
    active: bool
    course_preferences: list[CoursePreferenceInfo]
    meeting_preferences: list[MeetingPreferenceInfo]
