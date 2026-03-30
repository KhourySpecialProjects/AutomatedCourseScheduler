"""Schedule Pydantic schemas."""

from pydantic import BaseModel

from app.core.enums import Semester


class ScheduleResponse(BaseModel):
    schedule_id: int
    name: str
    semester: Semester
    year: int
    draft: bool
    campus: int
    complete: bool

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    name: str
    semester: Semester
    year: int
    campus: int


class ScheduleUpdate(BaseModel):
    name: str | None = None
    complete: bool | None = None
