# Case Risk Scoring Tool

Analysts group security alerts into cases, pick scoring policies, and see a transparent risk score and severity.

## What it does
- **New case page:** enter a name, pick alerts and policies (with a live score preview), then click *Create case*. Nothing is saved until then, and the case is created in one request.
- **Case page:** edit alerts and policies as a local draft with a live score preview; *Update case* saves them in one request (disabled until something changes). Rename is separate: type the new name and click the tick.
- **All cases page:** lists every case with its alert count, final score and severity; open one to edit it, or delete it.
- Create, rename and delete cases (names are required, trimmed, max 100 chars, not unique; the id is the identifier).
- Add seeded, read-only alerts to cases (the same alert can be in several cases). Adding an alert twice to one case through `POST /cases/{id}/alerts` is a 409; the UI never sends a duplicate, and the create and update calls collapse repeated alert ids.
- Request policies per case: `REPEAT_NOISE_DAMPING` plus at most one escalation (`CRITICAL_ASSET_BOOST` or `APT_CAMPAIGN_LINK`).
- See raw score, each adjustment, final score (capped at 100) and severity (Low 0-29, Medium 30-59, High 60-84, Critical 85-100).

## Tech stack
React + Vite + TypeScript (styled with Pico CSS plus a small `styles.css`), FastAPI + SQLAlchemy + Alembic, PostgreSQL, Docker Compose (nginx serves the build and proxies `/api`).

## Architecture and design decisions
- **Scoring engine** (`backend/app/scoring/engine.py`) is a pure function with no DB or web imports, so it is tested in isolation.
- **Requested vs applied:** a case stores the *requested* policies only. Whether each is *applied* (and the score itself) is recomputed on every read and never stored. A policy that stops qualifying stays requested, shows "not applied" with a reason, and re-applies automatically if the case qualifies again.
- **Order:** damping first, then escalation, then cap at 100. Boost and APT both use the post-damping score. Boost is `floor(20% of s)`, capped at 30.
- **Damping:** among `network_scan` alerts only the highest-scoring one counts (ties: highest alert id); the rest are ignored.
- **`applied`** is true only when the policy's own points are non-zero (before the 100 cap). The backend returns the flag and a human-readable `detail`; the UI shows them as-is.
- The backend rejects two escalations (400) even though the UI's radio group prevents it.
- Deleting a case cascades to its alert links and policies.

Note on the boost cap: the 30-point cap only reduces the boost when the score is at least 155, and by then the score is already above 100, so the final score is 100 regardless. The cap only changes the displayed boost points.

## Run locally
```
cp .env.example .env   # optional; defaults match
docker compose up --build
```
Open http://localhost:8080 (API at http://localhost:8000/api, docs at /docs). The backend container runs `alembic upgrade head`, seeds the 8 alerts if the table is empty, then starts uvicorn.

Without Docker for the app: run Postgres, set `DATABASE_URL`, then in `backend/` run `alembic upgrade head`, `python -m app.seed`, `uvicorn app.main:app`; in `frontend/` run `npm install && npm run dev` (proxies `/api` to :8000).

## Run tests
```
cd backend
pip install -r requirements.txt pytest==8.3.4 httpx==0.28.1
pytest
```
Engine tests need nothing else. API tests need Postgres: start it with `docker compose up -d db` (published on host port 5433 to avoid clashing with a local Postgres on 5432). Each test run creates a temporary database named `risk_test_<random>`, builds it with the Alembic migrations, seeds it, and drops it when the run ends, so your app data is never touched. To use another server, set `TEST_DATABASE_URL` (e.g. `postgresql+psycopg2://user:pass@host:5432/postgres`); the user needs permission to create databases.

## API (all under `/api`)
| Method and path | Purpose | Status |
|---|---|---|
| `GET /alerts` | List alerts | 200 |
| `GET /cases` | Cases with alert_count, final_score, severity | 200 |
| `POST /cases` | Create with `name`, at least one entry in `alert_ids`, and optional `policies` (atomic) | 201, 400, 404, 422 |
| `POST /summary/preview` | Score an unsaved selection of `alert_ids` and `policies` | 200, 400, 404, 422 |
| `PATCH /cases/{id}` | Rename | 200, 404, 422 |
| `PUT /cases/{id}` | Replace alerts (at least one) and requested policies in one atomic call (used by the case page's Update button) | 200, 400, 404, 422 |
| `DELETE /cases/{id}` | Delete (cascade) | 204, 404 |
| `GET /cases/{id}` | Case with alerts and requested policies | 200, 404 |
| `POST /cases/{id}/alerts` | Add alert | 201, 404, 409 |
| `DELETE /cases/{id}/alerts/{alert_id}` | Remove alert (not the case's last one) | 204, 404, 422 |
| `PUT /cases/{id}/policies` | Replace requested policies | 200, 404, 400, 422 |
| `GET /cases/{id}/summary` | Scored summary | 200, 404 |

## Known limitations
- No authentication; anyone who can reach the app can change anything.
- Alerts are read-only and seeded; there is no alert ingestion.
- The Postgres port is published to the host for convenience; remove it in any shared environment.

## With more time
Authentication and per-user cases, alert ingestion, frontend tests, CI.

## Deployment
Set `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and `DATABASE_URL` (see `.env.example`). On container start the backend migrates (`alembic upgrade head`) and seeds idempotently.

## Time taken
Taken from the commit timestamps on `main` (2026-10-30). The planning discussion before the first commit is counted as 25 minutes.

| Step | Commit time | Since previous |
|---|---|---|
| Planning discussion | before 14:45 | 25 min |
| Repo config, SQLAlchemy models, initial migration and seed script | 14:45:51 | (first commit) |
| Scoring engine with unit tests | 14:51:02 | 5 min 11 s |
| Remove development requirements file | 14:54:34 | 3 min 32 s |
| Alerts, cases, policies, summary and preview endpoints with API tests | 14:56:36 | 2 min 02 s |
| Backend Dockerfile and entrypoint | 15:06:59 | 10 min 23 s |
| Frontend: new case, all cases and case pages | 15:13:06 | 6 min 07 s |
| Frontend Dockerfile, nginx config and Docker Compose | 15:27:34 | 14 min 28 s |

Total: 25 min discussion + 41 min 43 s from the first to the last code commit ≈ **67 minutes**.