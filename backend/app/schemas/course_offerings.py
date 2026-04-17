"""Course Offerings Pydantic schemas."""

from pydantic import BaseModel


class CourseOfferingsSchema(BaseModel):
    subject: str
    code: int
    name: str
    credits: int
    description: str

    def translate(self):
        json_payload = {
            "subject": self.subject,
            "code": self.code,
            "name": self.name,
            "credits": self.credits,
            "description": self.description,
        }

        return json_payload
