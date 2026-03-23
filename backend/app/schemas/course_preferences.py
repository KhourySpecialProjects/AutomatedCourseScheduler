"""Course Prefences Pydantic schemas."""

from pydantic import BaseModel
from app.core.enums import PreferenceLevel


class CoursePreferencesSchema(BaseModel):
    facultyName: str
    facultyId: int
    course: str
    semester: str
    preference: PreferenceLevel

    def translate(self, courseId):
        json_payload = {
            "faculty_nuid": self.facultyId,
            "course_id": courseId,
            "preference": self.preference
        }

        return json_payload
