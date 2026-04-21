"""Algorithm Input Pydantic schemas for the scheduling algorithm"""

from pydantic import BaseModel, Field

from app.schemas.algorithm_params import AlgorithmParameters
from app.schemas.conflict_group import ConflictGroup
from app.schemas.course import CourseResponse
from app.schemas.faculty import FacultyProfileResponse


# ---------------------
# Algorithm Input
# ---------------------
class AlgorithmInput(BaseModel):
    OfferedCourses: list[CourseResponse] = Field(..., description="Courses to schedule this semester")
    TimeBlocks: list[int] = Field(..., description="Available time block IDs")
    ConflictGroups: list[ConflictGroup] = Field(default=[], description="Course groups that should not overlap")
    AllFaculty: list[FacultyProfileResponse] = Field(..., description="Faculty members and their preferences")
    Parameters: AlgorithmParameters = Field(
        default_factory=AlgorithmParameters,
        description="Tunable algorithm parameters",
    )
