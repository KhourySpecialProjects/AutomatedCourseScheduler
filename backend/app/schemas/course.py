"""Course Pydantic schemas."""

from pydantic import BaseModel


class CourseResponse(BaseModel):
    CourseID: int
    CourseDescription: str | None = None
    CourseNo: int | None = None
    CourseSubject: str | None = None
    CourseName: str | None = None
    SectionCount: int | None = None

    model_config = {"from_attributes": True}
