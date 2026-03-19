"""Course Prefences Pydantic schemas."""

from pydantic import BaseModel, enum


class PreferenceEnum(str, enum.Enum):
    THIRD = "Not my cup of tea"
    SECOND = "Ready to teach"
    FIRST = "Eager to teach"


class CoursePreferencesSchema(BaseModel):
    faculty: str
    course: str
    preference: str
