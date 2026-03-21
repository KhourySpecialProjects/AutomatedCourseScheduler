"""CampusTimeBlock Database Model."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class CampusTimeBlock(Base):
    __tablename__ = "CampusTimeBlock"
    CTBID = Column(Integer, primary_key=True, autoincrement=True)
    BlockId = Column(Integer, ForeignKey(
        "TimeBlock.TimeBlockID"), nullable=False)
    CampusID = Column(Integer, ForeignKey("Campus.CampusID"), nullable=True)

    sections = relationship("Section", back_populates="time_block")
