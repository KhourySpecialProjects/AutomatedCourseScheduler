"""Course Preference Database Model."""

from sqlalchemy import Column, Integer, String, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class CoursePreference(Base):
    __tablename__ = "CoursePreference"
    PreferenceId = Column(Integer, primary_key=True, autoincrement=True)
    FacultyId = Column(String, ForeignKey("Faculty.FacultyId"), nullable=False)
    CourseId = Column(Integer, ForeignKey("Course.CourseId"), nullable=False)
    Rank = Column(Integer)

    __table_args__ = (
        CheckConstraint('Rank >= 1 AND Rank <= 3', name='validate_rank')
    )
