from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.schedule import Schedule
    from app.models.time_block import TimeBlock
    from app.models.course import Course
    from app.models.faculty_assignment import FacultyAssignment
    from app.models.section_lock import SectionLock

if TYPE_CHECKING:
    from app.models.section_lock import SectionLock

class Section(Base):
    """Represents a section offering a course in a schedule
    assigned to a time block."""

    __tablename__ = "section"

    section_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    section_number: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    enrollment: Mapped[int] = mapped_column(Integer)

    # Foreign Keys
    schedule_id: Mapped[str] = mapped_column(String(50), ForeignKey("schedule.schedule_id"))
    time_block_id: Mapped[str] = mapped_column(String(50), ForeignKey("time_block.time_block_id"))
    course_id: Mapped[str] = mapped_column(String(50), ForeignKey("course.course_id"))

    # Relationships
    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="sections")
    time_block: Mapped["TimeBlock"] = relationship("TimeBlock", back_populates="sections")
    course: Mapped["Course"] = relationship("Course", back_populates="sections")
    faculty_assignments: Mapped[list["FacultyAssignment"]] = relationship("FacultyAssignment", back_populates="section")
    section_lock: Mapped["SectionLock"] = relationship("SectionLock", back_populates="section", uselist=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

