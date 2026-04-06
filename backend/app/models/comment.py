from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.section import Section
    from app.models.user import User


class Comment(Base):
    """Represents a comment"""

    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    content: Mapped[str] = mapped_column(String(200))
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("section.section_id"))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("comment.comment_id")
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="comments")
    section: Mapped["Section"] = relationship("Section", back_populates="comments")
    replies: Mapped[list["Comment"]] = relationship(
        foreign_keys=[parent_id],
        primaryjoin="Comment.comment_id == foreign(Comment.parent_id)",
        post_update=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
