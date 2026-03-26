"""Course Pydantic schemas."""

from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    CourseID: int
    CourseDescription: str | None = None
    CourseNo: int | None = None
    CourseSubject: str | None = None
    CourseName: str | None = None
    SectionCount: int | None = None
    Priority: bool | None = None

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    credits: int = Field(..., ge=0)
    priority: bool = Field(False)


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    credits: int | None = None
    priority: bool | None = None
