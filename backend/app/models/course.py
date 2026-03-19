"""Course Database Model."""

from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "Course"
    CourseID = Column(Integer, primary_key=True, autoincrement=True)
    CourseNo = Column(Integer, nullable=False)
    CourseSubject = Column(String, nullable=False)
    CourseName = Column(String, nullable=False)
    SectionCount = Column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint('CourseNo >= 1000', name='validate_course_number')
    )
