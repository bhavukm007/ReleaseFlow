# ReleaseFlow

ReleaseFlow is a single-user release checklist application for tracking software releases from planning through post-deployment verification. Checklist progress and release status are always computed together, so the displayed state cannot drift from the underlying steps.

## Project Links

- GitHub: [https://github.com/bhavukm007/ReleaseFlow](https://github.com/bhavukm007/ReleaseFlow)
- Live frontend: `https://releaseflow-web-bhavukm007.onrender.com` *(available after Blueprint deployment)*
- API: `https://releaseflow-api-bhavukm007.onrender.com` *(available after Blueprint deployment)*
- API documentation: `https://releaseflow-api-bhavukm007.onrender.com/docs` *(available after Blueprint deployment)*

If Render requires a different service name because one is already taken, replace the corresponding URL above and update `VITE_API_URL` and `CORS_ORIGINS` in the Render dashboard.

## Features

- Create, view, update, search, sort, and delete releases
- A fixed eight-step checklist with immediate optimistic updates
- Automatically computed `planned`, `ongoing`, and `done` statuses
- Progress count and animated progress bar
- Editable additional information
- Responsive desktop, tablet, and mobile interface
- Loading, empty, error, confirmation, and toast states
- OpenAPI documentation, Alembic migrations, sample data, and automated tests

## Architecture

The React/Vite single-page application calls a FastAPI REST API through a typed Axios service. FastAPI routes use dependency-injected SQLAlchemy sessions and a service layer. PostgreSQL stores one `releases` table, with checklist state embedded in a JSON column. Alembic manages schema changes.

```text
Browser
  |
  +-- React/Vite static site
          |
          +-- Axios / JSON REST API
                  |
                  +-- FastAPI + SQLAlchemy
                          |
                          +-- PostgreSQL
```

## Folder Structure

```text
ReleaseFlow/
|-- backend/
|   |-- alembic/              # Database migrations
|   |-- app/
|   |   |-- api/              # HTTP routes
|   |   |-- core/             # Environment configuration
|   |   |-- database/         # Engine and session dependency
|   |   |-- models/           # SQLAlchemy model
|   |   |-- schemas/          # Pydantic request/response contracts
|   |   |-- services/         # Release business logic
|   |   `-- main.py
|   |-- tests/
|   |-- Dockerfile
|   `-- seed.py
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- hooks/
|   |   `-- pages/
|   `-- Dockerfile
|-- docker-compose.yml
`-- render.yaml
```

## Database Schema

ReleaseFlow intentionally uses one table.

### `releases`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | integer | Primary key |
| `name` | varchar(200) | Required |
| `due_date` | date | Required |
| `additional_info` | text | Nullable |
| `steps` | JSON | Required; eight named boolean values |
| `created_at` | timestamp with time zone | Required |
| `updated_at` | timestamp with time zone | Required |

Every release contains exactly these steps:

1. Code Freeze
2. QA Completed
3. Documentation Updated
4. Security Review
5. Performance Testing
6. Deployment Ready
7. Production Deployment
8. Post Deployment Verification

There is no separate steps table.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/releases` | List releases ordered by due date |
| `GET` | `/releases/{id}` | Get one release |
| `POST` | `/releases` | Create a release |
| `PUT` | `/releases/{id}` | Replace editable release fields |
| `PATCH` | `/releases/{id}/steps` | Update the eight checklist states |
| `PATCH` | `/releases/{id}/info` | Update additional information |
| `DELETE` | `/releases/{id}` | Delete a release |
| `GET` | `/health` | Health check |

Local interactive API documentation is available at `http://localhost:8000/docs`.

## Status Computation

- `planned`: zero steps completed
- `ongoing`: at least one, but fewer than eight, completed
- `done`: all eight steps completed

Status, completed-step count, and total-step count are response fields. They are never stored in the database.

## Local Setup

Requirements: Python 3.12+, Node.js 20.19+ or 22.12+, and PostgreSQL 15+.

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Then install and run:

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

On Windows without a Unix-style `cp` command, copy `.env.example` to `.env` in File Explorer or run:

```powershell
Copy-Item .env.example .env
```

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

### Tests and Production Build

```bash
cd backend
pytest

cd ../frontend
npm test
npm run build
```

## Environment Variables

### Backend

| Variable | Example | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://releaseflow:releaseflow@localhost:5432/releaseflow` | SQLAlchemy connection URL |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed browser origins |
| `PORT` | `8000` | Container HTTP port; Render supplies this automatically |

The backend accepts both Render's `postgresql://` connection string and the explicit SQLAlchemy `postgresql+psycopg://` form.

### Frontend

| Variable | Example | Purpose |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Public API base URL embedded at build time |

## Docker

Start PostgreSQL, apply migrations, seed the three sample releases, and run both applications:

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

Stop the stack with:

```bash
docker compose down
```

The named `postgres_data` volume preserves database contents. Use `docker compose down -v` only when you intentionally want to delete local database data.

## Deploy to Render

The root-level `render.yaml` defines all required resources:

- `releaseflow-db-bhavukm007`: managed PostgreSQL
- `releaseflow-api-bhavukm007`: Docker-based FastAPI web service
- `releaseflow-web-bhavukm007`: React static site

The Blueprint connects `DATABASE_URL` to the managed database, restricts `CORS_ORIGINS` to the frontend URL, sets the frontend's `VITE_API_URL`, applies migrations, inserts idempotent sample data, configures the API health check, and adds an SPA rewrite.

### Exact Render Deployment Steps

1. Commit and push the latest repository changes to GitHub.
2. Sign in to [Render](https://dashboard.render.com/) and connect the GitHub account containing this repository.
3. Click **New +**, then **Blueprint**.
4. Select the `bhavukm007/ReleaseFlow` repository.
5. Keep the Blueprint file path as `render.yaml`.
6. Review the three proposed resources and click **Apply** or **Deploy Blueprint**.
7. Wait for the PostgreSQL database to become available.
8. Wait for the API deployment to finish. Its container automatically runs `alembic upgrade head`, runs the idempotent seed script, and starts Uvicorn on Render's assigned `PORT`.
9. Wait for the frontend static-site build and deployment to finish.
10. Open `https://releaseflow-api-bhavukm007.onrender.com/health` and confirm `{"status":"healthy"}`.
11. Open `https://releaseflow-api-bhavukm007.onrender.com/docs` and confirm the OpenAPI page loads.
12. Open `https://releaseflow-web-bhavukm007.onrender.com`.
13. Create a release, toggle a checklist item, edit its information, refresh the page, and confirm the changes remain.
14. If Render changed either public service name, update:
    - Backend `CORS_ORIGINS` to the exact frontend origin, without a trailing slash.
    - Frontend `VITE_API_URL` to the exact API origin, without a trailing slash.
    - Redeploy both services and update the Project Links section above.
15. Submit the GitHub URL and live frontend URL. The API documentation URL is useful as an additional reviewer link.

Render's free web service can spin down after inactivity, so the first request may take longer. Render's free PostgreSQL database expires after 30 days; deploy close to the assessment date or upgrade the database if the submission must remain available longer.

## Future Improvements

Possible extensions include authentication and teams, configurable checklist templates, ownership, audit history, notifications, release dependencies, and CI/CD integrations. They are intentionally excluded from this single-user assignment.
