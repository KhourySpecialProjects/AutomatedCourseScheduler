"""Schedule Pydantic schemas."""

from pydantic import BaseModel


class ScheduleResponse(BaseModel):
    schedule_id: int
    name: str
    semester_id: int
    draft: bool
    campus: int
    complete: bool
    active: bool

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    name: str
    semester_id: int
    campus: int


class ScheduleUpdate(BaseModel):
    name: str | None = None
    complete: bool | None = None
    active: bool | None = None
