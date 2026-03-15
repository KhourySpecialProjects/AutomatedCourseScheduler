"""Faculty Database Model."""

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class Faculty(Base):
    __tablename__ = "Faculty"
    NUID = Column(Integer, primary_key=True, autoincrement=True)

    sections = relationship("Section", back_populates="instructor")
