# ReleaseFlow

ReleaseFlow is a focused, single-user release checklist application. It keeps release dates, context, and the eight critical readiness checks in one responsive interface. Status and progress are always derived from the checklist, so they cannot drift out of sync.

## Features

- Create, view, update, search, sort, and delete releases
- Fixed eight-step checklist with instant optimistic updates
- Computed planned, ongoing, and done statuses
- Progress count and animated progress bar
- Editable release notes
- Responsive desktop, tablet, and mobile UI
- Loading, empty, error, confirmation, and toast states
- OpenAPI-documented REST API, migrations, sample data, and automated tests

## Architecture

The React/Vite SPA calls a FastAPI REST API through a typed Axios service. FastAPI routes use injected SQLAlchemy sessions and a service layer. PostgreSQL stores a single `releases` table; Alembic owns schema evolution. Nginx serves the production frontend.

## Folder Structure

```text
ReleaseFlow/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # HTTP routes
│   │   ├── core/             # Configuration
│   │   ├── database/         # Engine and sessions
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic contracts
│   │   ├── services/         # Business logic
│   │   └── main.py
│   ├── tests/
│   └── seed.py
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── hooks/
│       └── pages/
└── docker-compose.yml
```

## Database Schema

The `releases` table contains `id`, `name`, `due_date`, nullable `additional_info`, JSON `steps`, `created_at`, and `updated_at`. Steps are deliberately embedded as JSON; there is no steps table.

Every new release receives exactly: Code Freeze, QA Completed, Documentation Updated, Security Review, Performance Testing, Deployment Ready, Production Deployment, and Post Deployment Verification.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/releases` | List releases by due date |
| GET | `/releases/{id}` | Get one release |
| POST | `/releases` | Create a release |
| PUT | `/releases/{id}` | Replace editable release fields |
| PATCH | `/releases/{id}/steps` | Update the checklist |
| PATCH | `/releases/{id}/info` | Update additional information |
| DELETE | `/releases/{id}` | Delete a release |
| GET | `/health` | Service health |

Interactive API documentation is available at `http://localhost:8000/docs`.

## Status Computation

- **planned**: zero of eight steps completed
- **ongoing**: one through seven steps completed
- **done**: all eight steps completed

Status is calculated in the backend response and never stored.

## Local Setup

Requirements: Python 3.12+, Node.js 22+, and PostgreSQL 15+.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

### Tests

```bash
cd backend && pytest
cd frontend && npm test
```

## Docker

```bash
docker compose up --build
docker compose exec backend python seed.py
```

Open the application at `http://localhost:8080`; the API is at `http://localhost:8000`.

## Environment Variables

Backend:

- `DATABASE_URL`: SQLAlchemy PostgreSQL connection URL
- `CORS_ORIGINS`: comma-separated allowed browser origins

Frontend:

- `VITE_API_URL`: public base URL of the API, embedded during the Vite build

## Deployment

Use managed PostgreSQL and set `DATABASE_URL` to its TLS-enabled connection string. Run `alembic upgrade head` as a release step before starting Uvicorn. Build the frontend with the public API URL supplied as `VITE_API_URL`, serve the generated assets through Nginx/CDN, and restrict `CORS_ORIGINS` to the production origin. The included containers are stateless except for the database volume and are ready for an orchestrated container platform.

## Future Improvements

Authentication and teams, configurable checklist templates, release ownership, audit history, notifications, dependency tracking, and CI/CD integrations are natural extensions while preserving the current simple core.
