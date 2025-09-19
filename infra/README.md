Infra

- docker-compose.yml spins up Postgres (pgvector), backend (FastAPI), and frontend (Vite dev server).
- `db/init.sql` enables the `vector` extension on first run.

Usage
- From repo root: `docker compose -f infra/docker-compose.yml up --build`

