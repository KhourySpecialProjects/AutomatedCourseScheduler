from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.faculty import Faculty
    from app.models.section import Section


class FacultyAssignment(Base):
    """Represents the assignment of a faculty member to a section."""

    __tablename__ = "faculty_assignment"

    faculty_assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    faculty_nuid: Mapped[int] = mapped_column(Integer, ForeignKey("faculty.nuid"))
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("section.section_id"))

    # Relationships
    faculty: Mapped["Faculty"] = relationship(
        "Faculty", back_populates="faculty_assignments"
    )
    section: Mapped["Section"] = relationship(
        "Section", back_populates="faculty_assignments"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
