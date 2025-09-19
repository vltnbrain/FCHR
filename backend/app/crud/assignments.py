from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from ..db import models


def invite(db: Session, *, idea_id: int, developer_id: int | None = None) -> models.Assignment:
    row = models.Assignment(idea_id=idea_id, developer_id=developer_id, status="invited", created_at=datetime.utcnow())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_assignments(db: Session, *, for_user_id: int | None = None, status: str | None = None) -> list[models.Assignment]:
    stmt = select(models.Assignment)
    if for_user_id is not None:
        stmt = stmt.where(models.Assignment.developer_id == for_user_id)
    if status is not None:
        stmt = stmt.where(models.Assignment.status == status)
    return list(db.execute(stmt.order_by(models.Assignment.created_at.asc())).scalars())


def respond(db: Session, *, assignment_id: int, developer_id: int, response: str) -> models.Assignment:
    row = db.get(models.Assignment, assignment_id)
    if not row:
        raise ValueError("Assignment not found")
    if row.developer_id and row.developer_id != developer_id:
        raise PermissionError("Not your assignment")
    if response == "accept":
        row.status = "accepted"
        row.developer_id = developer_id
    elif response == "decline":
        row.status = "declined"
        row.developer_id = developer_id
    else:
        raise ValueError("Invalid response")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def escalate(db: Session, *, assignment_id: int) -> models.Assignment:
    row = db.get(models.Assignment, assignment_id)
    if not row:
        raise ValueError("Assignment not found")
    row.status = "escalated"
    db.add(row)
    # Push to marketplace queue as open
    mq = models.TaskMarketplace(idea_id=row.idea_id, open=True)
    db.add(mq)
    db.commit()
    db.refresh(row)
    return row

