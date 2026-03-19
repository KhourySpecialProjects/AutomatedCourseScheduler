"""Course Offerings Pydantic schemas."""

from pydantic import BaseModel


class CourseOfferingsSchema(BaseModel):
    courseNo: int
    courseSubject: str
    courseName: str
