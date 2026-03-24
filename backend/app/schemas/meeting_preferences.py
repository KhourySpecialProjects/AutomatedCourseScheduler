"""Time Prefences Pydantic schemas."""

from pydantic import BaseModel

from app.core.enums import PreferenceLevel


class MeetingPreferencesSchema(BaseModel):
    facultyName: str
    facultyId: int
    meetingTime: str
    semester: str
    preference: PreferenceLevel

    def translate(self, timeBlockId):
        json_payload = {
            "faculty_nuid": self.facultyId,
            "meeting_time": timeBlockId,
            "preference": self.preference,
        }

        return json_payload
