import os
os.environ.setdefault('PYTHONPATH', 'backend')
os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://postgres:postgres@localhost:5432/aihub')

from app.db.session import SessionLocal
from app.core.passwords import hash_password
from app.db import models

def main():
    db = SessionLocal()
    try:
        # Create sample users if not exist
        def ensure_user(email, role):
            u = db.query(models.User).filter(models.User.email==email).first()
            if not u:
                u = models.User(email=email, role=role, password_hash=hash_password('secret'))
                db.add(u)
                db.commit()
                db.refresh(u)
            return u

        admin = ensure_user('admin@example.com','admin')
        analyst = ensure_user('analyst@example.com','analyst')
        finance = ensure_user('finance@example.com','finance')
        dev = ensure_user('dev@example.com','developer')

        # Sample ideas
        if not db.query(models.Idea).count():
            idea = models.Idea(title='Sample Idea', description='Demo idea for MVP', created_by_id=admin.id)
            db.add(idea)
            db.commit()
        print('Seed completed')
    finally:
        db.close()

if __name__ == '__main__':
    main()

