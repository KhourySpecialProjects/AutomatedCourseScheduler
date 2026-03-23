"""Algorithm output Pydantic schemas"""

from datetime import datetime
from pydantic import BaseModel, Field

class RunMetadata(BaseModel):
    StartTime: datetime = Field(..., description="Algorithm run start time")
    EndTime: datetime = Field(..., description="Algorithm run end time")
    TotalRunTime: int = Field(..., description="Total run time in milliseconds")
    Version: int = Field(..., description="Algorithm version")
