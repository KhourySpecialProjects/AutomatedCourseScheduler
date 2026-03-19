"""Upload Pydantic schemas."""

from pydantic import BaseModel, Field


class PreferencesSchema(BaseModel):
    preferenceId: int
    facultyId: int
    courseId: int
    rank: int = Field(ge=1, le=3)
