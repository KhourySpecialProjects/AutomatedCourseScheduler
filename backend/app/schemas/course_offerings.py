"""Course Offerings Pydantic schemas."""

from pydantic import BaseModel


class CourseOfferingsSchema(BaseModel):
    courseName: str
    credits: int
    description: str

    def translate(self):
        json_payload = {
            "name": self.courseName,
            "credits": self.credits,
            "description": self.description,
        }

        return json_payload
