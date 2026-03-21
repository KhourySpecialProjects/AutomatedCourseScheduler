from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.section import Section


class TimeBlock(Base):
    """Represents a schedulable time block slot that can be assigned to a
    section, including the days, time, and location where the section will
    meet."""

    __tablename__ = "time_block"

    time_block_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    timezone: Mapped[str] = mapped_column(String(4))
    campus: Mapped[str] = mapped_column(String(100))

    # Relationships
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="time_block"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
