"""Faculty Database Model."""

from sqlalchemy import Column, Integer, String, Boolean, CheckConstraint, ForeignKey
import sqlalchemy
from sqlalchemy.orm import relationship

from app.core.database import Base


class Faculty(Base):
    __tablename__ = "Faculty"
    NUID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("User.UserID"), nullable=True)
    FirstName = Column(String(50))
    LastName = Column(String(50))
    Email = Column(String(255))
    Title = Column(String(50))
    Campus = Column(Integer, ForeignKey("Campus.CampusID"), nullable=True)
    Active = Column(Boolean)
    MaxLoad = Column(Integer)

    sections = relationship("Section", back_populates="instructor")

    __table_args__ = (
        CheckConstraint(
            r"Email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'",
            name="valid_email_format"
        ),
    )
