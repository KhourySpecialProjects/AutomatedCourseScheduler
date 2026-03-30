"""Schedule Pydantic schemas."""

from pydantic import BaseModel


class SemesterResponse(BaseModel):
    semester_id: int
    name: str
    start_date: str  # ISO format date string
    end_date: str  # ISO format date string
    active: bool

    model_config = {"from_attributes": True}


class SemesterCreate(BaseModel):
    name: str
    start_date: str  # ISO format date string
    end_date: str  # ISO format date string
    active: bool = True


class SemesterUpdate(BaseModel):
    name: str | None = None
    start_date: str | None = None  # ISO format date string
    end_date: str | None = None  # ISO format date string
    active: bool | None = None
