"""Algorithm Input/Output Pydantic schemas for the scheduling algorithm."""

from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, Field

# ---------------------
# Algorithm Enums
# ---------------------


class Preference(int, Enum):
    FIRST_CHOICE = 1
    SECOND_CHOICE = 2
    THIRD_CHOICE = 3


class Severity(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class WarningType(StrEnum):
    TIME_BLOCK_OVERLOAD = "Time block surpasses threshold"
    UNPREFERENCED_COURSE = "Faculty assigned unpreferenced course"
    UNPREFERENCED_TIME = "Faculty assigned unpreferenced time"
    CONFLICT_GROUP_VIOLATION = "Conflict group courses overlap"
    FACULTY_OVERLOAD = "Faculty overloaded with assignments"


# ---------------------
# Algorithm Input
# ---------------------


class Course(BaseModel):
    CourseID: int = Field(..., description="Unique course identifier")
    SectionCount: int = Field(..., description="Sections to generate for this course")
    ImportanceWeight: float = Field(
        default=0.5,
        description="Scheduling priority (0.0-1.0, higher = more important)",
    )


class ConflictGroup(BaseModel):
    CourseIDs: list[int] = Field(..., description="Course IDs that should not overlap")
    Label: str = Field(..., description="Label for this conflict group")


class Faculty(BaseModel):
    NUID: int = Field(..., description="Unique faculty identifier")
    MaxLoad: int = Field(
        default=4,
        description="Max courses per semester",
    )


class FacultyCoursePreference(BaseModel):
    FacultyID: int = Field(..., description="NUID of the faculty member")
    CourseID: int = Field(..., description="ID of the preferred course")
    PreferenceBucket: Preference = Field(..., description="Preference bucket (1-3)")


class TimeBlock(BaseModel):
    BlockID: int = Field(..., description="Unique time block identifier")
    StartTime: datetime = Field(..., description="Start time of the time block")
    EndTime: datetime = Field(..., description="End time of the time block")
    CampusID: int = Field(..., description="Campus this time block belongs to")


class FacultyTimePreference(BaseModel):
    FacultyID: int = Field(..., description="NUID of the faculty member")
    BlockID: int = Field(..., description="ID of the preferred time block")
    PreferenceBucket: Preference = Field(..., description="Preference bucket (1-3)")


class AlgorithmParameters(BaseModel):
    MaxTimeBlockCapacity: float = Field(
        default=0.15,
        description="Max section percentage per time block",
    )
    FacultyVsScheduleBalance: float = Field(
        default=0.5,
        description="Faculty preference vs. balance weight (0.0-1.0)",
    )


class AlgorithmInput(BaseModel):
    OfferedCourses: list[Course] = Field(
        ..., description="Courses to schedule this semester"
    )
    CoursePreferences: list[FacultyCoursePreference] = Field(
        ..., description="Faculty course preferences"
    )
    TimePreferences: list[FacultyTimePreference] = Field(
        ..., description="Faculty time block preferences"
    )
    TimeBlocks: list[TimeBlock] = Field(..., description="Available time blocks")
    ConflictGroups: list[ConflictGroup] = Field(
        default=[], description="Course groups that should not overlap"
    )
    AllFaculty: list[Faculty] = Field(
        ..., description="Available faculty this semester"
    )
    Parameters: AlgorithmParameters = Field(
        default_factory=AlgorithmParameters,
        description="Tunable algorithm parameters",
    )


# ---------------------------
# Algorithm Output
# ---------------------------


class Section(BaseModel):
    CourseID: int = Field(..., description="Assigned course identifier")
    FacultyID: int = Field(..., description="Assigned faculty identifier")
    BlockID: int = Field(..., description="Assigned time block identifier")
    CoursePreference: Preference | None = Field(
        default=None, description="Faculty course preference bucket"
    )
    TimePreference: Preference | None = Field(
        default=None, description="Faculty time preference bucket"
    )
    AssignmentScore: float = Field(..., description="Quality score for this assignment")


class Warning(BaseModel):
    Type: WarningType | None = Field(default=None, description="Type of warning")
    SeverityRank: Severity = Field(..., description="Severity of this warning")
    Message: str = Field(..., description="Warning detail for the user")
    FacultyID: int | None = Field(default=None, description="Related faculty member")
    CourseID: int | None = Field(default=None, description="Related course")
    BlockID: int | None = Field(default=None, description="Related time block")


class RunMetadata(BaseModel):
    StartTime: datetime = Field(..., description="Algorithm run start time")
    EndTime: datetime = Field(..., description="Algorithm run end time")
    TotalRunTime: int = Field(..., description="Total run time in milliseconds")
    Version: int = Field(..., description="Algorithm version")


class DraftScheduleResult(BaseModel):
    SectionAssignments: list[Section] = Field(
        ..., description="All section assignments"
    )
    StabilityScore: float = Field(..., description="Overall schedule quality score")
    Warnings: list[Warning] = Field(..., description="Schedule warnings and issues")
    RunMetadata: RunMetadata = Field(..., description="Algorithm run metadata")
