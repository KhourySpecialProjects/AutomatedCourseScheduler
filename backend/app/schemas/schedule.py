"""Schedule Pydantic schemas."""

from pydantic import BaseModel

from app.core.enums import Campus, Semester


class ScheduleResponse(BaseModel):
    schedule_id: int
    name: str
    semester: Semester
    year: int
    draft: bool
    campus: Campus
    complete: bool

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    name: str
    semester: Semester
    year: int
    campus: Campus


class ScheduleUpdate(BaseModel):
    name: str | None = None
    complete: bool | None = None
