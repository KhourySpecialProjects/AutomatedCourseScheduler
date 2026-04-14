"""Course Pydantic schemas."""

from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    course_id: int
    subject: str
    code: int
    name: str
    description: str | None = None
    credits: int
    priority: bool = False
    section_count: int | None = None
    qualified_faculty: int = 0

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=10)
    code: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    credits: int = Field(..., ge=0)
    priority: bool = Field(False)


class CourseUpdate(BaseModel):
    subject: str | None = None
    code: int | None = None
    name: str | None = None
    description: str | None = None
    credits: int | None = None
    priority: bool | None = None
