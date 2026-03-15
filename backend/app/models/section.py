"""Section Database Model."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Section(Base):
    """Section ORM model."""

    __tablename__ = "Section"

    SectionID = Column(Integer, primary_key=True, autoincrement=True)
    Schedule = Column(Integer, ForeignKey("Schedule.ScheduleID"), nullable=True) # this should NOT be Nullable
    TimeBlock = Column(Integer, ForeignKey("CampusTimeBlock.CTBID"), nullable=True)
    Course = Column(Integer, ForeignKey("Course.CourseID"), nullable=True)
    Capacity = Column(Integer)
    Instructor = Column(Integer, ForeignKey("Faculty.NUID"), nullable=True)

    schedule = relationship("Schedule", back_populates="sections")
    time_block = relationship("CampusTimeBlock", back_populates="sections")
    course = relationship("Course", back_populates="sections")
    instructor = relationship("Faculty", back_populates="sections")
