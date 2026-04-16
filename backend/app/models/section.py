from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.course import Course
    from app.models.faculty_assignment import FacultyAssignment
    from app.models.schedule import Schedule
    from app.models.section_lock import SectionLock
    from app.models.time_block import TimeBlock


class Section(Base):
    """Represents a section offering a course in a schedule
    assigned to a time block."""

    __tablename__ = "section"

    section_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_number: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    room: Mapped[str | None] = mapped_column(String(50))

    # Foreign Keys
    schedule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schedule.schedule_id"))
    time_block_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("time_block.time_block_id"))
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("course.course_id"))
    crosslisted_section_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("section.section_id"), unique=True
    )

    # Relationships
    schedule: Mapped[Schedule] = relationship(
        "Schedule", back_populates="sections")
    time_block: Mapped[TimeBlock] = relationship(
        "TimeBlock", back_populates="sections")
    course: Mapped[Course] = relationship("Course", back_populates="sections")
    crosslisted_section: Mapped[Section | None] = relationship(
        foreign_keys=[crosslisted_section_id],
        remote_side="Section.section_id",
        post_update=True,
    )
    faculty_assignments: Mapped[list[FacultyAssignment]] = relationship(
        "FacultyAssignment", back_populates="section", cascade="all, delete-orphan"
    )
    section_lock: Mapped[SectionLock] = relationship(
        "SectionLock", back_populates="section", uselist=False, cascade="all, delete-orphan"
    )
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="section", cascade="all, delete-orphan"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
