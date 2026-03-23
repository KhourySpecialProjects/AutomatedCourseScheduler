"""Faculty Pydantic schemas."""

from pydantic import BaseModel

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
