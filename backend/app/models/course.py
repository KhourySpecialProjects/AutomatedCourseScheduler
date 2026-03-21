"""Course Database Model."""
import enum
from sqlalchemy import Column, Integer, String, CheckConstraint, Enum, SmallInteger
from sqlalchemy.orm import relationship

from app.core.database import Base


class SemesterSeason(enum.Enum):
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER_1 = "Summer 1"
    SUMMER_2 = "Summer 2"


class Course(Base):
    __tablename__ = "Course"
    CourseID = Column(Integer, primary_key=True, autoincrement=True)
    # CourseNo = Column(Integer, nullable=False)
    # CourseSubject = Column(String, nullable=False)
    CourseName = Column(String, nullable=False)
    SemesterSeason = Column(Enum(SemesterSeason, name="semester_season"))
    SemesterYear = Column(SmallInteger)
    SectionCount = Column(Integer, nullable=True)
