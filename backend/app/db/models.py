from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy import types
import os

Base = declarative_base()


# Optional pgvector type (fallback to generic JSON when disabled or unavailable)
USE_PGVECTOR = os.getenv("USE_PGVECTOR", "1").lower() in ("1", "true", "yes")

if USE_PGVECTOR:
    try:
        from pgvector.sqlalchemy import Vector  # type: ignore
    except Exception:  # pragma: no cover
        USE_PGVECTOR = False

if not USE_PGVECTOR:
    class Vector(types.TypeDecorator):  # type: ignore
        impl = types.JSON
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return value

        def process_result_value(self, value, dialect):
            return value


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False, default="user")
    department = Column(String(100))
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class Idea(Base):
    __tablename__ = "ideas"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    author_email = Column(String(255))
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default="submitted")  # submitted | analyst_pending | finance_pending | approved | rejected


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    stage = Column(String(50), nullable=False)  # analyst | finance
    decision = Column(String(50), nullable=True)  # approved | rejected | needs_more_info
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="pending")  # invited | accepted | declined | escalated
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskMarketplace(Base):
    __tablename__ = "tasks_marketplace"
    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EventAudit(Base):
    __tablename__ = "events_audit"
    id = Column(Integer, primary_key=True)
    entity = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    event = Column(String(100), nullable=False)
    payload = Column(types.JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailQueue(Base):
    __tablename__ = "email_queue"
    id = Column(Integer, primary_key=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    try:
        vector = Column(Vector(1536))  # type: ignore[arg-type]
    except Exception:  # pragma: no cover
        vector = Column(types.JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
