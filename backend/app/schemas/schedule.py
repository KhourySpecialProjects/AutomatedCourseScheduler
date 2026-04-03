"""Schedule Pydantic schemas."""

from pydantic import BaseModel

from app.schemas.course import CourseResponse


class ScheduleResponse(BaseModel):
    schedule_id: int
    name: str
    semester_id: int
    draft: bool
    campus: int
    complete: bool
    active: bool
    course_list: list[CourseResponse] = []

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    name: str
    semester_id: int
    campus: int
    new_courses: list[int] = []


class ScheduleUpdate(BaseModel):
    name: str | None = None
    active: bool | None = None
