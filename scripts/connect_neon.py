#!/usr/bin/env python3
"""
Configure the project to use a Neon Postgres database.

Usage:
  - Pass the psql connection URL as an argument:
      python scripts/connect_neon.py "postgresql://user:pass@host/db?sslmode=require"
  - Or via env var PSQL_URL:
      PSQL_URL=postgresql://... python scripts/connect_neon.py

This will:
  1) Connect to Neon and ensure pgvector extension
  2) Write DATABASE_URL (SQLAlchemy form) and USE_PGVECTOR=1 to .env
  3) Create tables (init_db)
"""
from __future__ import annotations
import os
import sys
from pathlib import Path


def to_sqlalchemy_url(psql_url: str) -> str:
    if psql_url.startswith("postgresql+psycopg://"):
        return psql_url
    if psql_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + psql_url[len("postgresql://") :]
    return psql_url


def ensure_pgvector(psql_url: str) -> None:
    import psycopg

    # Use raw psql URL for psycopg
    with psycopg.connect(psql_url) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()


def write_env(sqlalchemy_url: str) -> None:
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.exists():
        example = root / ".env.example"
        if example.exists():
            env_path.write_text(example.read_text(), encoding="utf-8")
        else:
            env_path.touch()

    # Read & update
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    def upsert(key: str, value: str):
        nonlocal lines
        found = False
        for i, ln in enumerate(lines):
            if ln.startswith(key + "="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")

    upsert("DATABASE_URL", sqlalchemy_url)
    upsert("USE_PGVECTOR", "1")
    if not any(ln.startswith("SECRET_KEY=") for ln in lines):
        import secrets
        upsert("SECRET_KEY", secrets.token_hex(32))

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def init_db() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from app.db.session import engine
    from app.db.base import Base

    Base.metadata.create_all(bind=engine)


def main() -> None:
    psql_url = None
    if len(sys.argv) > 1:
        psql_url = sys.argv[1]
    if not psql_url:
        psql_url = os.getenv("PSQL_URL")
    if not psql_url:
        print("Provide Neon psql URL as an argument or set PSQL_URL env var.", file=sys.stderr)
        sys.exit(2)

    print("Connecting to Neon and ensuring pgvector...")
    try:
        ensure_pgvector(psql_url)
        print("pgvector extension ensured.")
    except Exception as e:
        print(f"Warning: could not ensure pgvector ({e}). Continuing...", file=sys.stderr)

    sqlalchemy_url = to_sqlalchemy_url(psql_url)
    write_env(sqlalchemy_url)
    print(".env updated with DATABASE_URL and USE_PGVECTOR=1")

    print("Creating tables (init_db)...")
    init_db()
    print("Done. You can now run backend:")
    print("  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()

