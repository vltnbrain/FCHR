<div align="center">
  <img width="1200" alt="FCHR / AI Hub" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# FCHR • AI Hub of Ideas & Tasks

Monorepo with a React (Vite) frontend and a FastAPI backend that collects user ideas, performs deduplication via embeddings, and routes them through analyst/finance/developer workflows with SLA-based notifications.

• Frontend: Vite + React + TypeScript (in repo root)
• Backend: FastAPI + SQLAlchemy + Pydantic (in `ai-hub/backend`)
• Infra: Postgres+pgvector, Redis, MailHog via Docker Compose (in `ai-hub/infra`)

This README summarizes local development, tests, and the MVP endpoints shipped.

## Quick Start

Prerequisites
- Node.js 18+
- Python 3.11+
- (Optional) Docker & Docker Compose for full stack (Postgres/Redis/MailHog)

### Frontend (Vite)
```bash
npm install
npm run dev
# Open http://localhost:5173
```

### Backend (FastAPI)
Local quick run (SQLite, no external services):
```bash
cd ai-hub/backend
python -m pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
# Open http://localhost:8000/docs
```

Full stack with Postgres, Redis, MailHog:
```bash
cd ai-hub/infra
docker-compose up -d
# Backend will be available at http://localhost:8000
# MailHog UI at http://localhost:8025
```

Environment variables (examples)
- Copy `.env.example` to `.env` (root) as needed
- Backend supports `OPENAI_API_KEY` for embeddings; without it, duplicate check returns empty and system still works
- Database URL can be set via `DATABASE_URI`. Default dev Postgres is `postgresql://aihub:aihub123@localhost:5432/aihub`

## MVP Features (Implemented)
- Idea Ingestion API: create/list/get; auto-structuring of title; optional duplicate detection via embeddings
- Minimal RBAC: header `x-user-role` gate for sensitive routes (analyst/finance/manager/admin). JWT planned next.
- Users API: create (RBAC), list with filters, get by id
- Email queue stubs: queue entries + MailHog integration in docker compose
- SQLite-friendly dev/test: embeddings column falls back to `Text` when pgvector isn’t present

## API (MVP)
Base URL: `http://localhost:8000/api/v1`

Ideas
- POST `/ideas/` – submit new idea
- GET `/ideas/` – list with filters, pagination
- GET `/ideas/{id}` – idea details
- GET `/ideas/{id}/duplicates` – potential duplicates (requires `OPENAI_API_KEY`)
- POST `/ideas/{id}/route/analyst` – requires role: analyst|manager|admin
- POST `/ideas/{id}/route/finance` – requires role: finance|manager|admin
- POST `/ideas/{id}/route/developers` – requires role: manager|admin

Users
- POST `/users/` – create (requires role: admin|manager)
- GET `/users/` – list, filter by `role`, `department`, `q`
- GET `/users/{id}` – get by id

RBAC (temporary)
- Send header `x-user-role: analyst|finance|manager|admin|developer` to simulate roles during development.
- JWT/OIDC auth is planned to replace the header in the next iteration.

## Tests
Run backend tests (uses SQLite):
```bash
python -m pip install -r ai-hub/backend/requirements.txt
python -m pip install pytest aiosqlite email-validator
pytest -q
```

## Project Structure
```
ai-hub/
  backend/               # FastAPI app (app.py entry)
  infra/                 # docker-compose + init.sql (pgvector)
  integrations/          # voice adapter and helpers
  docs/                  # project docs

components/, hooks/, lib/, index.tsx  # Frontend (Vite)
```

## Contributing
1. Create a branch: `git checkout -b feature/your-change`
2. Run tests locally: `pytest -q`
3. Submit a PR with a clear description

## License
MIT (see `LICENSE`)
