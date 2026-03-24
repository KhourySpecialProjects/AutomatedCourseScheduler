"""Section Pydantic schemas."""

from pydantic import BaseModel


class SectionResponse(BaseModel):
    section_id: int
    schedule_id: int
    time_block_id: int
    course_id: int
    capacity: int
    section_number: int
    assignment_score: float | None = None

    model_config = {"from_attributes": True}


class SectionCreate(BaseModel):
    schedule_id: int
    time_block_id: int
    course_id: int
    capacity: int
    section_number: int


class SectionUpdate(BaseModel):
    time_block_id: int | None = None
    course_id: int | None = None
    capacity: int | None = None


# --- Rich / denormalized response for the section row view ---


class CourseInfo(BaseModel):
    course_id: int
    name: str
    description: str
    credits: int


class TimeBlockInfo(BaseModel):
    time_block_id: int
    days: str
    start_time: str
    end_time: str
    timezone: str


class CoursePreferenceInfo(BaseModel):
    course_id: int
    course_name: str
    preference: str


class MeetingPreferenceInfo(BaseModel):
    meeting_time: str
    preference: str


class InstructorInfo(BaseModel):
    nuid: int
    first_name: str
    last_name: str
    title: str
    email: str
    course_preferences: list[CoursePreferenceInfo]
    meeting_preferences: list[MeetingPreferenceInfo]


class SectionRichResponse(BaseModel):
    section_id: int
    section_number: int
    capacity: int
    schedule_id: int
    course: CourseInfo
    time_block: TimeBlockInfo
    instructors: list[InstructorInfo]
