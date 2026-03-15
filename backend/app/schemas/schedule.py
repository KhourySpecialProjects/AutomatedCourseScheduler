"""Schedule Pydantic schemas."""

from pydantic import BaseModel


class ScheduleResponse(BaseModel):
    ScheduleID: int
    ScheduleName: str | None = None
    SemesterSeason: str | None = None  # "Fall" or "Spring"
    SemesterYear: int | None = None
    Campus: int | None = None
    Complete: bool | None = None

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    ScheduleName: str
    SemesterSeason: str  
    SemesterYear: int
    Campus: int


class ScheduleUpdate(BaseModel):
    ScheduleName: str | None = None
    Complete: bool | None = None
