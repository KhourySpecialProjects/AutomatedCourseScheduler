"""TimeBlock Database Model."""
import enum
from sqlalchemy import Column, Integer, ForeignKey, Time, ARRAY, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class Weekday(enum.Enum):
    M = "M"
    T = "T"
    W = "W"
    R = "R"
    F = "F"


class TimeBlock(Base):
    __tablename__ = "TimeBlock"
    TimeBlockID = Column(Integer, primary_key=True, autoincrement=True)
    StartTime = Column(Time, nullable=False)
    EndTime = Column(Time, nullable=False)
    MeetingDays = Column(ARRAY(Enum(Weekday, name="weekday")))
    # CampusId = Column(Integer, ForeignKey("Campus.CampusId"), nullable=True)

    # sections = relationship("Section", back_populates="time_block") // i dont think we need this
