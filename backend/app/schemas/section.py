"""Section Pydantic schemas."""

from pydantic import BaseModel


class SectionResponse(BaseModel):
    section_id: int
    schedule_id: int
    time_block_id: int
    course_id: int
    capacity: int
    section_number: int

    model_config = {"from_attributes": True}


class SectionCreate(BaseModel):
    schedule_id: int
    time_block_id: int
    course_id: int
    capacity: int
    section_number: int


class SectionUpdate(BaseModel):
    time_block_id: int | None = None
    course_id: int | None = None
    capacity: int | None = None
