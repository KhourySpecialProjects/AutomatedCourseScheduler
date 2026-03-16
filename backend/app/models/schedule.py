"""Schedule Database Model."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Schedule(Base):
    __tablename__ = "Schedule"
    ScheduleID = Column(Integer, primary_key=True, autoincrement=True)
    ScheduleName = Column(String(50))
    SemesterSeason = Column(String)  # 'Fall' or 'Spring' (enum in DB)
    SemesterYear = Column(SmallInteger)
    Campus = Column(Integer, ForeignKey("Campus.CampusID"))
    Complete = Column(Boolean, default=False)

    sections = relationship("Section", back_populates="schedule")
