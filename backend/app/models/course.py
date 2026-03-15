"""Course Database Model."""

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "Course"
    CourseID = Column(Integer, primary_key=True, autoincrement=True)

    sections = relationship("Section", back_populates="course")
