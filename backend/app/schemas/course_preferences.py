"""Course Prefences Pydantic schemas."""

from pydantic import BaseModel
import enum


class PreferenceEnum(str, enum.Enum):
    FIRST = "Eager to teach"
    SECOND = "Ready to teach"
    THIRD = "Willing to teach"
    NO = "Not my cup of tea"
    

    def to_int(self) -> int:
        mapping = {
            PreferenceEnum.THIRD: 1,
            PreferenceEnum.SECOND: 2,
            PreferenceEnum.FIRST: 3,
            PreferenceEnum.NO: 4,
        }

        return mapping[self]


class CoursePreferencesSchema(BaseModel):
    facultyName: str
    facultyId: int
    course: str
    semester: str
    preference: PreferenceEnum

    def translate(self, courseId):
        json_payload = {
            "FacultyID": self.facultyId,
            "CourseID": courseId,
            "Rank": self.preference.to_int()
        }
        
        return json_payload
