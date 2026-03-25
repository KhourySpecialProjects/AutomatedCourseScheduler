"""Schedule Pydantic schemas."""

from pydantic import BaseModel


class ScheduleResponse(BaseModel):
    schedule_id: int
    name: str | None = None
    semester: str | None = None
    year: int | None = None
    draft: bool | None = True
    campus: int | None = None
    complete: bool | None = False

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    name: str
    semester: str
    year: int
    campus: int

class ScheduleUpdate(BaseModel):
    name: str | None = None
    complete: bool | None = None