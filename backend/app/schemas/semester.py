"""Schedule Pydantic schemas."""

from pydantic import BaseModel


class SemesterResponse(BaseModel):
    semester_id: int
    season: str
    year: int
    active: bool

    model_config = {"from_attributes": True}


class SemesterCreate(BaseModel):
    season: str
    year: int
    active: bool = True


class SemesterUpdate(BaseModel):
    season: str | None = None
    year: int | None = None
    active: bool | None = None
