"""Campus Database Model."""

from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Campus(Base):
    __tablename__ = "Campus"
    CampusID = Column(Integer, primary_key=True, autoincrement=True)
    CampusName = Column(String, nullable=False)
    