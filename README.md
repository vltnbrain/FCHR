AI Hub of Ideas & Tasks — Monorepo

Overview
- Backend: Python FastAPI (API, auth, ideas)
- Frontend: React + TypeScript (dashboard)
- Infra: Docker Compose + Postgres (pgvector)
- Docs, Scripts, Integrations folders for ops and adapters

CI & Tests
- GitHub Actions workflow in `.github/workflows/ci.yml` runs sqlite and postgres jobs
- Local smoke: set env `PYTHONPATH=backend`, `DATABASE_URL=sqlite+pysqlite:///:memory:` and run `python scripts/smoke_test.py`

Prod Compose
- See `infra/prod/docker-compose.yml` and `infra/prod/nginx.conf`
- Bring up stack: `docker compose -f infra/prod/docker-compose.yml up --build`
- For TLS, use `infra/prod/nginx-ssl.conf` (replace example.com and mount certs from Let's Encrypt)
 - Certbot automation:
   - HTTP-01 challenge path is served from `/var/www/certbot` in Nginx
   - First issue (example):
     `docker compose -f infra/prod/docker-compose.yml run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com --email you@example.com --agree-tos --noninteractive`
   - After issuing, switch Nginx to `nginx-ssl.conf` and reload. Renewal runs inside `certbot` service.

Email Queue (Admin)
- View pending emails via `GET /emails/pending`; retry with `POST /emails/retry/:id`

Security
- Security headers middleware is enabled; set `RATE_LIMIT_PER_MINUTE` for rate limit
- Password policy: min length 8; use `/auth/refresh` to renew access token

Monitoring
- Uptime Kuma: `http://<host>:3001` (configure monitors for backend and nginx)
- Node Exporter: exposes metrics on host for Prometheus
- Logs: Loki on `:3100`, Promtail ships container logs; connect Grafana or external Loki UI
 - Prometheus: `http://<host>:9090` (scrapes node-exporter)
 - Grafana: `http://<host>:3000` (admin/admin). Provisioned datasources for Prometheus+Loki and basic Node dashboard. Prefer SSH port-forwarding.

Manual Deploy Helpers
- Linux: `scripts/deploy.sh` (set REPO_DIR if needed)
- Windows: `scripts/deploy.ps1 -RepoDir <path>`

Getting Started
- Copy `.env.example` to `.env` and adjust values
- Backend dev: `cd backend && uvicorn app.main:app --reload`
- Frontend dev: `cd frontend && npm install && npm run dev`
- Docker (optional): see `infra/docker-compose.yml`

Structure
- backend/ — FastAPI app and services
- frontend/ — React + Vite + TS dashboard
- infra/ — docker-compose, DB init
- docs/ — documentation
- scripts/ — dev helpers
- integrations/ — external adapters
