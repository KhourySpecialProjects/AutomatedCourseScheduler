"""Faculty Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator

from app.schemas.section import CoursePreferenceInfo, MeetingPreferenceInfo


class FacultyResponse(BaseModel):
    nuid: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    campus: int | None = None
    active: bool | None = None
    maxLoad: int | None = None

    model_config = {"from_attributes": True}


class FacultyCreate(BaseModel):
    nuid: int = Field(..., gt=0)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    campus: int = Field(..., gt=0)
    active: bool = True
    max_load: int = Field(default=3, ge=1)

    @field_validator("first_name", "last_name", "email")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v


class FacultyUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    campus: int | None = None
    active: bool | None = None
    max_load: int | None = None

    @field_validator("first_name", "last_name", "email")
    @classmethod
    def not_empty_optional(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("max_load")
    @classmethod
    def not_negative_optional(cls, v: int | None) -> int | None:
        if v < 1:
            raise ValueError("Max_load cannot be less than 1")
        return v


class FacultyProfileResponse(BaseModel):
    nuid: int
    first_name: str
    last_name: str
    email: str
    campus: int
    active: bool
    maxLoad: int | None = None
    needsAdminReview: bool = False
    course_preferences: list[CoursePreferenceInfo]
    meeting_preferences: list[MeetingPreferenceInfo]
