"""Section Pydantic schemas."""

from pydantic import BaseModel


class SectionResponse(BaseModel):
    SectionID: int
    Schedule: int | None
    TimeBlock: int | None
    Course: int | None
    Capacity: int | None
    Instructor: int | None

    model_config = {"from_attributes": True}


class SectionCreate(BaseModel):
    Schedule: int
    TimeBlock: int | None = None
    Course: int
    Capacity: int
    Instructor: int | None = None


class SectionUpdate(BaseModel):
    TimeBlock: int | None = None
    Course: int | None = None
    Capacity: int | None = None
    Instructor: int | None = None
