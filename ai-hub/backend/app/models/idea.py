"""
Idea model and related models for AI Hub
"""
from sqlalchemy import Column, String, Text, Float, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class IdeaStatus(str, enum.Enum):
    """Idea status enumeration"""
    NEW = "new"
    ANALYST_REVIEW = "analyst_review"
    FINANCE_REVIEW = "finance_review"
    DEVELOPER_ASSIGNMENT = "developer_assignment"
    IMPLEMENTATION = "implementation"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    IMPROVEMENT = "improvement"


class IdeaCategory(str, enum.Enum):
    """Idea category enumeration"""
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    IMPROVEMENT = "improvement"
    INTEGRATION = "integration"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    PERFORMANCE = "performance"
    UI_UX = "ui_ux"


class ReadinessLevel(str, enum.Enum):
    """Implementation readiness level"""
    CONCEPT = "concept"
    WIREFRAMES = "wireframes"
    PROTOTYPE = "prototype"
    MVP_READY = "mvp_ready"
    PRODUCTION_READY = "production_ready"


class Idea(BaseModel):
    """
    Main idea model representing user-submitted ideas
    """
    __tablename__ = "ideas"

    title = Column(String(200), nullable=False)
    raw_input = Column(Text, nullable=False)
    structured_summary = Column(Text, nullable=True)
    category = Column(Enum(IdeaCategory), nullable=True)
    required_team = Column(String(100), nullable=True)
    readiness_level = Column(Enum(ReadinessLevel), nullable=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(IdeaStatus), default=IdeaStatus.NEW, nullable=False, index=True)
    similarity_parent_id = Column(Integer, ForeignKey("ideas.id"), nullable=True)
    similarity_score = Column(Float, nullable=True)

    # Relationships
    author = relationship("User", back_populates="ideas")
    reviews = relationship("Review", back_populates="idea", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="idea", cascade="all, delete-orphan")
    marketplace_entries = relationship("MarketplaceEntry", back_populates="idea", cascade="all, delete-orphan")
    # Note: AuditEvent is a generic log table; omit ORM relationship here to avoid
    # cross-entity FKs and dialect-specific primaryjoin issues in tests.
    # Omit ORM relationship to Embedding to keep models DB-agnostic in tests

    def __repr__(self):
        return f"<Idea(id={self.id}, title='{self.title}', status={self.status})>"


class Review(BaseModel):
    """
    Review model for analyst and finance reviews
    """
    __tablename__ = "reviews"

    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False, index=True)
    reviewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stage = Column(Enum("analyst", "finance", name="review_stage"), nullable=False)
    decision = Column(Enum("accepted", "rejected", "needs_info", name="review_decision"), nullable=False)
    notes = Column(Text, nullable=True)
    recommended_department = Column(String(100), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    idea = relationship("Idea", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, idea_id={self.idea_id}, stage={self.stage}, decision={self.decision})>"


class Assignment(BaseModel):
    """
    Assignment model for developer assignments
    """
    __tablename__ = "assignments"

    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False, index=True)
    developer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum("invited", "accepted", "declined", "no_response", name="assignment_status"),
                   default="invited", nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    idea = relationship("Idea", back_populates="assignments")
    developer = relationship("User", back_populates="assignments")

    def __repr__(self):
        return f"<Assignment(id={self.id}, idea_id={self.idea_id}, developer_id={self.developer_user_id}, status={self.status})>"


class MarketplaceEntry(BaseModel):
    """
    Marketplace entry for ideas that couldn't find developers
    """
    __tablename__ = "tasks_marketplace"

    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False, index=True, unique=True)
    listed_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    idea = relationship("Idea", back_populates="marketplace_entries")

    def __repr__(self):
        return f"<MarketplaceEntry(id={self.id}, idea_id={self.idea_id})>"
