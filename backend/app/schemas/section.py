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
