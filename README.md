# Workflow Notifications

Production-structured internal workflow reminder system using FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, APScheduler, Jinja2, and Microsoft Graph.

## Features
- Workflow Definitions + concrete Workflow Occurrences (90-day generation horizon).
- Recurrence engine (daily/weekly/monthly/quarterly/yearly/custom with rule fields).
- Reminder rules with before/on/after offsets.
- Email reminders via Microsoft Graph.
- Email reply polling + keyword parsing (`done`, `completed`, `complete`, `finished`, `skip`, `defer`).
- Idempotent inbound processing using unique `graph_message_id`.
- Dashboard + report pages + CSV export.
- Audit log and send/reply logs.

## Quick start
```bash
docker compose up --build
```
App: http://localhost:8000

## Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## Azure App Registration (Microsoft Graph)
1. Register app in Azure AD.
2. Add application permissions: `Mail.Send`, `Mail.Read`, `MailboxSettings.Read`.
3. Grant admin consent.
4. Create client secret.
5. Set `.env` values:
   - `GRAPH_TENANT_ID`
   - `GRAPH_CLIENT_ID`
   - `GRAPH_CLIENT_SECRET`
   - `GRAPH_MAILBOX_USER`

## Deployment (Ubuntu Server LTS, Docker)
1. Install Docker Engine + Docker Compose plugin.
2. Clone repo and create `.env` from `.env.example`.
3. Run `docker compose up -d --build`.
4. Configure reverse proxy (Nginx/Caddy) + TLS.
5. Back up Postgres volume (`pgdata`) regularly.

## Tests
```bash
pytest
```

## Maintenance
```bash
python scripts/clear_cache.py
```
Use this to remove Python/test/lint cache directories.
