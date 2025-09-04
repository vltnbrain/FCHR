"""
Pydantic schemas for Idea API
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.models import IdeaStatus, IdeaCategory, ReadinessLevel


class IdeaCreate(BaseModel):
    """Schema for creating a new idea"""
    raw_input: str = Field(..., description="Raw text input from user")
    user_name: str = Field(..., description="Full name of the user submitting the idea")
    user_email: Optional[str] = Field(None, description="Email of the user")
    user_role: Optional[str] = Field(None, description="User's role (developer, analyst, etc.)")
    user_department: Optional[str] = Field(None, description="User's department")


class IdeaUpdate(BaseModel):
    """Schema for updating an idea"""
    title: Optional[str] = None
    structured_summary: Optional[str] = None
    category: Optional[IdeaCategory] = None
    required_team: Optional[str] = None
    readiness_level: Optional[ReadinessLevel] = None
    status: Optional[IdeaStatus] = None


class IdeaResponse(BaseModel):
    """Schema for idea response"""
    id: int
    title: str
    raw_input: str
    structured_summary: Optional[str]
    category: Optional[IdeaCategory]
    required_team: Optional[str]
    readiness_level: Optional[ReadinessLevel]
    author_user_id: int
    status: IdeaStatus
    similarity_parent_id: Optional[int]
    similarity_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    # Related data
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    duplicate_count: int = 0
    review_count: int = 0
    assignment_count: int = 0

    class Config:
        from_attributes = True


class IdeaListResponse(BaseModel):
    """Schema for paginated idea list response"""
    items: List[IdeaResponse]
    total: int
    skip: int
    limit: int


class DuplicateCheckResponse(BaseModel):
    """Schema for duplicate check response"""
    idea_id: int
    title: str
    similarity_score: float
    status: str


class IdeaSummary(BaseModel):
    """Schema for idea summary (used in dashboard)"""
    id: int
    title: str
    status: IdeaStatus
    category: Optional[IdeaCategory]
    author_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    similarity_score: Optional[float]
    has_duplicates: bool = False
    review_count: int = 0
    sla_status: Optional[str] = None  # 'on_track', 'warning', 'overdue'
