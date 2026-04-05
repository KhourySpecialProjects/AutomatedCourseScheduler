"""Time Prefences Pydantic schemas."""

import re
from datetime import time

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

    @staticmethod
    def parse_time(t: str, period: str) -> time:
        hour, minute = map(int, t.split(":"))
        if period == "p" and hour != 12:
            hour += 12
        elif period == "a" and hour == 12:
            hour = 0
        return time(hour, minute)

    """Parse a meeting time string into (meetingDays, start_time, end_time) tuples.

    Handles single patterns like 'MWR 8:00a-9:05a' and compound patterns
    like 'T 11:45a-1:25p, R 2:50p-4:30p'."""

    def normalize_meeting_time(self) -> list[tuple[str, time, time]]:
        segment_pattern = re.compile(r"([A-Z]+)\s+(\d{1,2}:\d{2})([ap])-(\d{1,2}:\d{2})([ap])")
        segments = segment_pattern.findall(self.meetingTime)
        if not segments:
            raise ValueError(f"Unrecognized meeting time format: '{self.meetingTime}'")

        return [
            (
                days,
                self.parse_time(start_str, start_period),
                self.parse_time(end_str, end_period),
            )
            for days, start_str, start_period, end_str, end_period in segments
        ]
