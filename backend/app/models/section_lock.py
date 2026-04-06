from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.section import Section
    from app.models.user import User


class SectionLock(Base):
    """Represents a pessimistic lock on a section to prevent concurrent edits
    by multiple users.

    NOTE: Locking endpoints are not yet implemented — scheduled for a future sprint.
    """

    __tablename__ = "section_lock"

    section_lock_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("section.section_id"), unique=True)
    locked_by: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))

    # Relationships
    section: Mapped[Section] = relationship("Section", back_populates="section_lock")
    user: Mapped[User] = relationship("User", back_populates="section_locks")

    # Timestamps
    locked_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[DateTime] = mapped_column(DateTime)
