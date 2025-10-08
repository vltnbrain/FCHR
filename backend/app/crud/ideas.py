from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import models


def create_idea(
    db: Session,
    *,
    title: str,
    description: str,
    author_email: str | None = None,
    created_by_id: int | None = None,
) -> models.Idea:
    idea = models.Idea(
        title=title,
        description=description,
        author_email=author_email,
        created_by_id=created_by_id,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def list_ideas(db: Session) -> list[models.Idea]:
    return list(db.execute(select(models.Idea)).scalars().all())


def set_idea_status(db: Session, *, idea_id: int, status: str) -> models.Idea:
    row = db.get(models.Idea, idea_id)
    if not row:
        raise ValueError("Idea not found")
    row.status = status
    db.add(row)
    db.commit()
    db.refresh(row)
    return row



def list_ideas_for_user(db: Session, *, user_id: int) -> list[models.Idea]:
    stmt = select(models.Idea).where(models.Idea.created_by_id == user_id).order_by(models.Idea.created_at.desc())
    return list(db.execute(stmt).scalars().all())
