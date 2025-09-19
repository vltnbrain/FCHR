from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import models


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.execute(select(models.User).where(models.User.email == email)).scalars().first()


def create_user(db: Session, *, email: str, password_hash: str, full_name: str | None = None, role: str = "user", department: str | None = None) -> models.User:
    user = models.User(email=email, password_hash=password_hash, full_name=full_name, role=role, department=department)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def count_users(db: Session) -> int:
    return db.query(models.User).count()
