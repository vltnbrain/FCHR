import os
import importlib.util
from pathlib import Path

if __spec__ is None:
    __spec__ = importlib.util.spec_from_file_location('app.main', Path(__file__).resolve())
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .core.rate_limit import RateLimitMiddleware
from .core.security_headers import SecurityHeadersMiddleware
from .api import ideas, auth, users, emails, reviews, assignments, audit, voice, projects
from .db.base import Base
from .db.session import engine
from .db.session import SessionLocal
from .crud import emails as emails_crud
from .crud import reviews as reviews_crud
from .crud import events as events_crud
from .services.email import send_email_smtp
from .services import sla as sla_services
from sqlalchemy import text
import threading
import time
from prometheus_fastapi_instrumentator import Instrumentator


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Hub of Ideas & Tasks", version="0.1.0")

    # CORS
    origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()] if settings.CORS_ALLOWED_ORIGINS else [
        "http://localhost:5173", "http://localhost:3000"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    # Simple rate limiting per IP+path
    try:
        import os as _os
        limit = int(_os.getenv("RATE_LIMIT_PER_MINUTE", "120") or 120)
        app.add_middleware(RateLimitMiddleware, limit_per_minute=limit)
    except Exception:
        pass

    # Prometheus metrics exposure
    try:
        Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")
    except Exception:
        pass

    @app.on_event("startup")
    def on_startup():
        # Create tables in dev; in prod prefer migrations
        try:
            Base.metadata.create_all(bind=engine)
            # Ensure pgvector extension and index exist for similarity search
            with engine.begin() as conn:
                try:
                    conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
                except Exception:
                    pass
                try:
                    conn.exec_driver_sql(
                        "CREATE INDEX IF NOT EXISTS embeddings_vector_idx ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);"
                    )
                except Exception:
                    pass
                # Ensure 'status' column exists on ideas
                try:
                    conn.exec_driver_sql("ALTER TABLE ideas ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'submitted';")
                except Exception:
                    pass
        except Exception:
            pass

        # Start background email worker (simple polling)
        def email_worker():
            while True:
                try:
                    db = SessionLocal()
                    pending = emails_crud.get_pending_emails(db, limit=20)
                    for row in pending:
                        # Provider-agnostic send
                        from .services.email import send_email
                        status = send_email(row.to_email, row.subject, row.body)
                        emails_crud.mark_email_status(db, row, status)
                except Exception:
                    pass
                finally:
                    try:
                        db.close()
                    except Exception:
                        pass
                time.sleep(10)

        t = threading.Thread(target=email_worker, daemon=True)
        t.start()

        # SLA worker: escalate reviews older than 5 days (email admin once)
        def sla_worker():
            while True:
                try:
                    db = SessionLocal()
                    import os as _os
                    review_days = int(_os.getenv("SLA_REVIEW_DAYS", "5") or 5)
                    assign_days = int(_os.getenv("SLA_ASSIGNMENT_DAYS", "5") or 5)
                    sla_services.review_sla_pass(db, days=review_days)
                    sla_services.assignment_sla_pass(db, days=assign_days)
                except Exception:
                    pass
                finally:
                    try:
                        db.close()
                    except Exception:
                        pass
                time.sleep(60)

        s = threading.Thread(target=sla_worker, daemon=True)
        s.start()

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(ideas.router, prefix="/ideas", tags=["ideas"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(emails.router, prefix="/emails", tags=["emails"])
    app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
    app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
    app.include_router(audit.router, prefix="/events", tags=["audit"]) 
    app.include_router(voice.router, prefix="/voice", tags=["voice"]) 
    app.include_router(projects.router, prefix="/projects", tags=["projects"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
    )

