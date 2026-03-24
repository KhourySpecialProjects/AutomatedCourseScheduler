"""Algorithm Input Pydantic schemas for the scheduling algorithm"""

from pydantic import BaseModel, Field

from app.schemas.algorithm_params import AlgorithmParameters
from app.schemas.conflict_group import ConflictGroup
from app.schemas.course import CourseResponse
from app.schemas.faculty import FacultyResponse


# ---------------------
# Algorithm Input
# ---------------------
class AlgorithmInput(BaseModel):
    OfferedCourses: list[CourseResponse] = Field(
        ..., description="Courses to schedule this semester"
    )
    CoursePreferences: list[int] = Field(
        ..., description="Faculty course preference IDs"
    )
    TimePreferences: list[int] = Field(
        ..., description="Faculty time block preference IDs"
    )
    TimeBlocks: list[int] = Field(..., description="Available time block IDs")
    ConflictGroups: list[ConflictGroup] = Field(
        default=[], description="Course groups that should not overlap"
    )
    AllFaculty: list[FacultyResponse] = Field(
        ..., description="Available faculty this semester"
    )
    Parameters: AlgorithmParameters = Field(
        default_factory=AlgorithmParameters,
        description="Tunable algorithm parameters",
    )
