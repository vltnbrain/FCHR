"""
User model for AI Hub
"""
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class UserRole(str, enum.Enum):
    """User role enumeration"""
    DEVELOPER = "developer"
    ANALYST = "analyst"
    FINANCE = "finance"
    MANAGER = "manager"
    ADMIN = "admin"


class Department(str, enum.Enum):
    """Department enumeration"""
    ENGINEERING = "engineering"
    PRODUCT = "product"
    DESIGN = "design"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"


class User(BaseModel):
    """
    User model representing employees in the organization
    """
    __tablename__ = "users"

    full_name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, index=True)
    department = Column(Enum(Department), nullable=False, index=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    ideas = relationship("Idea", back_populates="author", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="reviewer", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="developer", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="actor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.full_name}', role={self.role})>"
