"""Schedule Warning Pydantic schemas"""

from pydantic import BaseModel, Field

from app.core.enums import Severity, WarningType


class Warning(BaseModel):
    Type: WarningType | None = Field(default=None, description="Type of warning")
    SeverityRank: Severity = Field(..., description="Severity of this warning")
    Message: str = Field(..., description="Warning detail for the user")
    FacultyID: int | None = Field(default=None, description="Related faculty member")
    CourseID: int | None = Field(default=None, description="Related course")
    BlockID: int | None = Field(default=None, description="Related time block")


class WarningResponse(Warning):
    """Warning with persistence fields — returned by the API."""

    warning_id: int = Field(..., description="Unique warning ID")
    dismissed: bool = Field(default=False, description="Whether this warning was dismissed")
