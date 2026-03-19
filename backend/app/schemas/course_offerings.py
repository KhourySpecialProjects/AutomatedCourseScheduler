"""Upload Pydantic schemas."""

from pydantic import BaseModel


class OfferingsSchema(BaseModel):
    courseId: int
    courseNo: int
    courseSubject: str
    courseName: str
    sectionCount: str
