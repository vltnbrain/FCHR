from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from ..db import models


def record_event(db: Session, *, entity: str, entity_id: int, event: str, payload: dict | None = None) -> models.EventAudit:
    row = models.EventAudit(entity=entity, entity_id=entity_id, event=event, payload=payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def has_event(db: Session, *, entity: str, entity_id: int, event: str) -> bool:
    existing = db.execute(
        select(models.EventAudit.id).where(
            and_(models.EventAudit.entity == entity, models.EventAudit.entity_id == entity_id, models.EventAudit.event == event)
        ).limit(1)
    ).first()
    return existing is not None

