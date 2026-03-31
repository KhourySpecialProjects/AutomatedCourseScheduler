"""Course Pydantic schemas."""

from pydantic import BaseModel


class CourseResponse(BaseModel):
    CourseID: int
    CourseDescription: str | None = None
    CourseNo: int | None = None
    CourseSubject: str | None = None
    CourseName: str | None = None
    SectionCount: int | None = None
    Priority: bool = False
    QualifiedFaculty: int = 0

    model_config = {"from_attributes": True}
