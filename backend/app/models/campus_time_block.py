"""CampusTimeBlock Database Model."""

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class CampusTimeBlock(Base):
    __tablename__ = "CampusTimeBlock"
    CTBID = Column(Integer, primary_key=True, autoincrement=True)

    sections = relationship("Section", back_populates="time_block")
