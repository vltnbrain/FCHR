#!/usr/bin/env python
from app.db.session import engine
from app.db.base import Base


def main():
    # Create all tables based on SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    print("Database initialized (tables created if not present)")


if __name__ == "__main__":
    main()

