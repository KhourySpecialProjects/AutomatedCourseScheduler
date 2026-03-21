"""User ORM model."""
import enum
from sqlalchemy import Column, Integer, String, Enum

from app.core.database import Base


class UserRole(enum.Enum):
    Admin = "Admin"
    Basic = "Basic"


class User(Base):
    __tablename__ = "User"
    UserID = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String)
    UserRole = Column(Enum(UserRole, name="role"))
