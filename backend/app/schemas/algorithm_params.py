"""Define Pydantic schemas for algorithm parameters"""

from pydantic import BaseModel, Field


class AlgorithmParameters(BaseModel):
    MaxTimeBlockCapacity: float = Field(
        default=0.15,
        gt=0.0,
        le=1.0,
        description="Max department percentage per time block",
    )
