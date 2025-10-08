from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from ..db import models


def create_review(db: Session, *, idea_id: int, stage: str, reviewer_id: int | None = None) -> models.Review:
    # If pending review for stage exists, reuse it
    existing = db.execute(
        select(models.Review).where(and_(models.Review.idea_id == idea_id, models.Review.stage == stage, models.Review.decision.is_(None)))
    ).scalars().first()
    if existing:
        return existing
    row = models.Review(idea_id=idea_id, stage=stage, reviewer_id=reviewer_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_pending(db: Session, *, stage: str) -> list[models.Review]:
    return list(
        db.execute(
            select(models.Review).where(and_(models.Review.stage == stage, models.Review.decision.is_(None))).order_by(models.Review.created_at.asc())
        ).scalars()
    )


def set_decision(db: Session, *, idea_id: int, stage: str, decision: str, notes: str | None = None, reviewer_id: int | None = None) -> models.Review:
    row = db.execute(
        select(models.Review).where(and_(models.Review.idea_id == idea_id, models.Review.stage == stage)).order_by(models.Review.id.desc()).limit(1)
    ).scalars().first()
    if not row:
        row = create_review(db, idea_id=idea_id, stage=stage)
    row.decision = decision
    row.notes = notes
    if reviewer_id:
        row.reviewer_id = reviewer_id
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def overdue_reviews(db: Session, *, older_than_days: int = 5) -> list[models.Review]:
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    return list(
        db.execute(
            select(models.Review).where(and_(models.Review.decision.is_(None), models.Review.created_at < cutoff)).order_by(models.Review.created_at.asc())
        ).scalars()
    )



def list_pending_for_stage(db: Session, *, stage: str, reviewer_id: int | None = None) -> list[models.Review]:
    stmt = select(models.Review).where(models.Review.stage == stage, models.Review.decision.is_(None))
    if reviewer_id is not None:
        stmt = stmt.where(models.Review.reviewer_id == reviewer_id)
    stmt = stmt.order_by(models.Review.created_at.asc())
    return list(db.execute(stmt).scalars())


def list_recent_reviews_for_user(db: Session, *, reviewer_id: int, limit: int = 10) -> list[models.Review]:
    stmt = (
        select(models.Review)
        .where(models.Review.reviewer_id == reviewer_id)
        .order_by(models.Review.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())
