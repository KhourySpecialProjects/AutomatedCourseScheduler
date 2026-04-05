from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.section_lock import SectionLock


class User(Base):
    """Represents a user of the application who can log in and
    perform tasks like running the scheduler and editing schedule
    drafts."""

    __tablename__ = "user"

    nuid: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    phone_number: Mapped[str] = mapped_column(String(15))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    section_locks: Mapped[list["SectionLock"]] = relationship("SectionLock", back_populates="user")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
