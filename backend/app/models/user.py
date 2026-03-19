"""User ORM model."""

from sqlalchemy import Column, Integer, String, Enum

from app.core.database import Base


class UserRole(Enum.enum):
    Admin = "Admin"
    Basic = "Basic"


class User(Base):
    __tablename__ = "User"
    UserId = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String)
    UserRole = Column(Enum(UserRole, name="role"))
