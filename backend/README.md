Backend - FastAPI

Quickstart
- Create venv and install requirements: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
- Run dev server: `uvicorn app.main:app --reload`

Env
- Load from `.env` (root or backend) via `python-dotenv` if present.

Endpoints (initial)
- GET /healthz - health check
- GET /ideas - list ideas
- POST /ideas - create idea (auth required; supports raw auto-structuring; returns possible_duplicates with scores)
- GET /auth/me - current user
- POST /auth/register - register user (first user becomes admin)
- POST /auth/login - login

RBAC
- Roles: developer, analyst, finance, manager, admin (plus default user)
- Usage in routes: `Depends(RoleChecker(["admin"]))`
- Users API: `POST /users/assign-role` (admin only)

Emails & SLA (MVP skeleton)
- POST /emails/queue (admin) — добавить письмо в очередь
- GET /emails/pending (admin) — посмотреть очередь
- Фоновый воркер отправляет письма через SMTP или mock, обновляя статус
- Провайдер: `EMAIL_PROVIDER=smtp|mock`; шаблоны в `services/email.py`
- SLA дни настраиваются через `SLA_REVIEW_DAYS` и `SLA_ASSIGNMENT_DAYS`

Reviews
- POST /reviews/request (manager/admin) — создать запрос на ревью (analyst | finance)
- GET /reviews/pending?stage=analyst|finance — список ожиданий
- POST /reviews/analyst/decision (analyst) — принять решение
- POST /reviews/finance/decision (finance) — принять решение
- SLA-воркер эскалирует ревью старше 5 дней письмом админу
- Прогрессия статусов идеи: submitted → analyst_pending → finance_pending → approved|rejected

Assignments
- POST /assignments/invite (manager/admin) — пригласить разработчика (по email, если найден — привяжется user)
- GET /assignments/pending — для manager/admin или текущего разработчика
- POST /assignments/respond (developer) — принять/отклонить
- SLA-эскалация: после N дней (SLA_ASSIGNMENT_DAYS) приглашение эскалируется админу и публикуется в marketplace


Security & Audit
- Rate limiting per IP+path (env: RATE_LIMIT_PER_MINUTE, default 120)
- Audit events записываются для ключевых операций (ideas, reviews, assignments) в events_audit

Voice Assistant (FCHR)
- Auth: pass X-VOICE-API-KEY header (configure VOICE_API_KEY in .env)
- POST /voice/identify — входная идентификация пользователя (email/phone/external_id)
- POST /voice/create-idea — создание идеи (поддерживает aw автосборку)
- POST /voice/get-status — статус идеи (по idea_id или последняя для пользователя)
