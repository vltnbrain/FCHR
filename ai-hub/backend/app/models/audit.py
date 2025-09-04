"""
Audit and system models for AI Hub
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

# Use PostgreSQL VECTOR when available; fallback to Text for non-Postgres (e.g., SQLite tests)
try:  # pragma: no cover - import-time environment check
    from sqlalchemy.dialects.postgresql import VECTOR as PGVECTOR
    _HAS_PG_VECTOR = True
except Exception:  # pragma: no cover - environments without PG dialect
    PGVECTOR = None
    _HAS_PG_VECTOR = False

from app.db.base import BaseModel


class AuditEvent(BaseModel):
    """
    Audit log for all system events and state changes
    """
    __tablename__ = "events_audit"

    entity_type = Column(String(50), nullable=False, index=True)  # 'idea', 'user', 'review', etc.
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # 'created', 'updated', 'deleted', 'status_changed', etc.
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    payload_json = Column(JSON, nullable=True)  # Additional data about the event

    # Relationships
    actor = relationship("User", back_populates="audit_events")

    def __repr__(self):
        return f"<AuditEvent(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id}, action='{self.action}')>"


class Embedding(BaseModel):
    """
    Vector embeddings for duplicate detection and similarity search
    """
    __tablename__ = "embeddings"

    entity_type = Column(String(50), nullable=False, index=True)  # 'idea', 'user', etc.
    entity_id = Column(Integer, nullable=False, index=True)
    # When running on PostgreSQL, store as pgvector; otherwise store as serialized text.
    vector = Column(PGVECTOR(1536) if _HAS_PG_VECTOR else Text, nullable=False)
    model = Column(String(100), nullable=False)  # Model used to generate embedding
    text_content = Column(Text, nullable=True)  # Original text that was embedded

    # Relationships intentionally omitted here to keep model generic and DB-agnostic

    def __repr__(self):
        return f"<Embedding(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id}, model='{self.model}')>"


class EmailQueue(BaseModel):
    """
    Email queue for notifications and communications
    """
    __tablename__ = "email_queue"

    to_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)  # 'pending', 'sent', 'failed'
    sent_at = Column(String, nullable=True)  # ISO datetime string
    provider_message_id = Column(String(255), nullable=True)  # Provider-specific ID
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<EmailQueue(id={self.id}, to='{self.to_email}', subject='{self.subject}', status='{self.status}')>"
