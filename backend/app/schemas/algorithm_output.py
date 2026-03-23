"""Algorithm output Pydantic schemas"""

from pydantic import BaseModel, Field

from app.schemas.run_metadata import RunMetadata
from app.schemas.warning import Warning


class DraftScheduleResult(BaseModel):
    SectionAssignments: list[int] = Field(
        ..., description="Section IDs produced by the algorithm"
    )
    StabilityScore: float = Field(..., description="Overall schedule quality score")
    Warnings: list[Warning] = Field(..., description="Schedule warnings and issues")
    Metadata: RunMetadata = Field(..., description="Algorithm run metadata")
