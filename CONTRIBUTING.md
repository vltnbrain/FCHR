Contributing Guide

Development
- Frontend lives in the repo root (Vite + React), backend in `ai-hub/backend`.
- Prefer small, focused PRs with clear descriptions.
- Keep changes consistent with existing code style; avoid unrelated refactors.

Backend
- Python 3.11+, FastAPI + SQLAlchemy 2.x.
- Run locally with SQLite: `uvicorn app:app --reload` from `ai-hub/backend`.
- Tests: `pytest -q` (installs: `pytest`, `aiosqlite`, `email-validator`).

RBAC/Auth
- During MVP, simulate roles via `x-user-role` header.
- JWT/OIDC-based auth planned; keep role checks via dependency injection.

Database
- Dev uses SQLite for tests; Postgres+pgvector via `ai-hub/infra/docker-compose.yml`.
- Avoid dialect-coupled relationships without foreign keys.

Commit Messages
- Use concise, imperative mood: "Add users API", "Fix idea routing".

Code of Conduct
- Be respectful and constructive in issues and PRs.

