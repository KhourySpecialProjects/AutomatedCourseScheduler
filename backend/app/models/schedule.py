"""Schedule Database Model."""

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class Schedule(Base):
    __tablename__ = "Schedule"
    ScheduleID = Column(Integer, primary_key=True, autoincrement=True)

    sections = relationship("Section", back_populates="schedule")
