from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import models


def queue_email(db: Session, *, to_email: str, subject: str, body: str) -> models.EmailQueue:
    row = models.EmailQueue(to_email=to_email, subject=subject, body=body, status="pending")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_pending_emails(db: Session, limit: int = 50) -> list[models.EmailQueue]:
    return list(
        db.execute(
            select(models.EmailQueue).where(models.EmailQueue.status == "pending").order_by(models.EmailQueue.id.asc()).limit(limit)
        ).scalars()
    )


def mark_email_status(db: Session, row: models.EmailQueue, status: str):
    row.status = status
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_email_by_id(db: Session, *, email_id: int) -> models.EmailQueue | None:
    return db.get(models.EmailQueue, email_id)


def retry_email(db: Session, *, email_id: int) -> models.EmailQueue:
    row = db.get(models.EmailQueue, email_id)
    if not row:
        raise ValueError("Email not found")
    row.status = "pending"
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
