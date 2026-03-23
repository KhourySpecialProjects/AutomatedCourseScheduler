"""Define Pydantic schemas for conflict groups (classes that shouldn't overlap)"""

from pydantic import BaseModel, Field


class ConflictGroup(BaseModel):
    CourseIDs: list[int] = Field(..., description="Course IDs that should not overlap")
    Label: str = Field(..., description="Label for this conflict group")
