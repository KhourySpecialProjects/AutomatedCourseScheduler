from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.section_lock import SectionLock


class User(Base):
    """Represents a user of the application.

    Created at invite time (auth0_sub is null until first login).
    nuid is the Northeastern University ID — a shared external identifier
    that can be used to correlate a User with a Faculty record, but is not
    a relational FK.
    """

    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auth0_sub: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    nuid: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[str] = mapped_column(String(50), default="VIEWER")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships — Comment and SectionLock reference user.user_id
    section_locks: Mapped[list["SectionLock"]] = relationship("SectionLock", back_populates="user")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
