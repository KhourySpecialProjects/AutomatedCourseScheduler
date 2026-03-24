"""Define Pydantic schemas for algorithm parameters"""

from pydantic import BaseModel, Field


class AlgorithmParameters(BaseModel):
    MaxTimeBlockCapacity: float = Field(
        default=0.15,
        description="Max section percentage per time block",
    )
    FacultyVsScheduleBalance: float = Field(
        default=0.5,
        description="Faculty preference vs. balance weight (0.0-1.0)",
    )
