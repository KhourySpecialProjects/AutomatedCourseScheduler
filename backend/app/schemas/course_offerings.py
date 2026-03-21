"""Course Offerings Pydantic schemas."""

from pydantic import BaseModel
from app.models.course import Course

class CourseOfferingsSchema(BaseModel):
    courseNo: int
    courseSubject: str
    courseName: str
    semester: str
    
    def model_translation():
        
        
        return

#  CourseID = Column(Integer, primary_key=True, autoincrement=True)
#     CourseNo = Column(Integer, nullable=False)
#     CourseSubject = Column(String, nullable=False)
#     CourseName = Column(String, nullable=True)
#     SemesterSeason = Column(Enum(SemesterSeason, name="semester_season"))
#     SemesterYear = Column(SmallInteger)
#     SectionCount = Column(Integer, nullable=True)