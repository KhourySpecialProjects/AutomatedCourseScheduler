"""Define Pydantic schemas for conflict groups (classes that are preferred to not overlap in the schedule)"""

from pydantic import BaseModel, Field

class ConflictGroup(BaseModel):
    CourseIDs: list[int] = Field(..., description="Course IDs that should not overlap")
    Label: str = Field(..., description="Label for this conflict group")