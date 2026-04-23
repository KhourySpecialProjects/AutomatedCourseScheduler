# Automated Course Scheduler

A web-based course scheduling platform built for Khoury College of Computer Sciences at Northeastern University. The system automates constraint-based schedule generation while providing intuitive tools for manual refinement, collaboration, and export.

## Overview

Each semester, scheduling administrators must coordinate course offerings, faculty preferences, time blocks, teaching loads, and various constraints to produce a viable course schedule. This platform replaces the current manual, spreadsheet-driven process with an integrated tool that combines algorithmic schedule generation with a collaborative editing interface.

### Key Features

- **CSV Data Ingestion** — Upload historical course offering data and faculty preferences via formatted CSV files
- **Scheduling Algorithm** — Constraint-based optimization that respects hard constraints, prioritizes ranked faculty preferences, and balances time block distribution
- **Schedule Visualization** — Grid-based views organized by professor, department, or time pattern with color-coded constraint violation indicators
- **Manual Editing** — Intuitive modifications with live WebSocket updates so all collaborators see changes in real time, backed by a two-phase warning system (immediate per-section feedback + holistic constraint scoring)
- **Collaboration** — Role-based access control, Notion-style commenting, draft versioning, and schedule finalization workflows
- **Export** — CSV export formatted for CourseLeaf entry, plus PDF/image exports for sharing

## Tech Stack

| Layer            | Technology                                    |
|------------------|-----------------------------------------------|
| Frontend         | React, TypeScript, Tailwind CSS v4, Orval     |
| Backend          | FastAPI, Pydantic, Python 3.12                |
| ORM              | SQLAlchemy                                    |
| Database         | PostgreSQL 16                                 |
| Authentication   | Auth0 (JWT, RBAC)                             |
| Containerization | Docker                                        |
| Deployment       | AWS ECS, ECR, S3, CloudFront                  |

## Project Structure

```
automated-course-scheduler/
├── frontend/                # React + TypeScript application
│   ├── src/
│   │   ├── api/             # API client functions
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── pages/           # Route-level page components
│   │   ├── types/           # TypeScript type definitions
│   │   └── utils/           # Helper utilities
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── core/            # Config, security, dependencies
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # Route handlers
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic & algorithm
│   │   └── main.py          # Application entry point
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)
- An [Auth0](https://auth0.com/) account with an API and SPA application configured

### Running with Docker

```bash
# Clone the repository
git clone https://github.com/KhourySpecialProjects/AutomatedCourseScheduler.git
cd AutomatedCourseScheduler

# Copy the example environment file and fill in your values
cp .env.example .env
```

The `.env` file requires Auth0 credentials before the app will start:

```
AUTH0_DOMAIN=your.domain.auth0.com
AUTH0_AUDIENCE=https://your.api.audience
AUTH0_SPA_CLIENT_ID=your_spa_client_id
```

See `.env.example` for the full list of required variables.

```bash
# Build and start all services
make build

# Seed the database with development data
make seed

# Bootstrap the first admin user (run once)
docker compose exec api python bootstrap_admin.py \
  --nuid <nuid> --first-name <First> --last-name <Last> --email <email>
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs

### Local Development

A `Makefile` at the root provides shortcuts for common tasks. Run `make help` to see all available commands.

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

make be-install   # pip install -r requirements.txt
make be-dev       # uvicorn app.main:app --reload
```

**Frontend:**

```bash
make fe-install   # npm install
make fe-dev       # npm run dev  (port 3000)
```

## User Roles

| Role        | Permissions                                                        |
|-------------|--------------------------------------------------------------------|
| **Admin**   | Upload data, run algorithm, edit schedules, override warnings, export |
| **Viewer**  | View schedules, leave comments                                     |

## Authentication

Auth0 handles all login/logout flows. The backend verifies JWT tokens on every request and enforces role-based access. Roles are assigned via Auth0 and synced to the local `User` table on first login.

The first admin user must be provisioned manually after the initial deploy:

```bash
docker compose exec api python bootstrap_admin.py \
  --nuid <nuid> --first-name <First> --last-name <Last> --email <email>
```

Required environment variables are listed in `.env.example` under the `Auth0` section.

## CI/CD

GitHub Actions runs on every pull request and on every push to `main`. The pipeline is path-scoped so only relevant jobs trigger based on what changed.

| Workflow | Trigger | Steps |
|---|---|---|
| **Backend CI** | PR with changes to `backend/**` | Ruff lint → Ruff format check → pytest |
| **Frontend CI** | PR with changes to `frontend/**` | ESLint → Vitest |
| **Deploy** | Push to `main` | Frontend: build → S3 sync → CloudFront invalidation; Backend: Docker build → ECR push → ECS service deploy |

All CI checks must pass before a PR can merge.

### Deployment secrets and variables

The Deploy workflow reads from GitHub Actions **Secrets** and **Variables**:

| Name | Type | Description |
|---|---|---|
| `AWS_ROLE_TO_ASSUME` | Secret | IAM role ARN for OIDC authentication |
| `VITE_API_BASE_URL` | Secret | Backend API URL for the production build |
| `VITE_AUTH0_DOMAIN` | Secret | Auth0 domain for the production SPA |
| `VITE_AUTH0_CLIENT_ID` | Secret | Auth0 SPA client ID |
| `VITE_AUTH0_AUDIENCE` | Secret | Auth0 API audience |
| `AWS_REGION` | Variable | AWS region (e.g. `us-east-1`) |
| `S3_BUCKET` | Variable | S3 bucket name for frontend assets |
| `CLOUDFRONT_DISTRIBUTION_ID` | Variable | CloudFront distribution to invalidate |
| `ECR_REPOSITORY` | Variable | ECR repository name for the backend image |
| `ECS_CLUSTER` | Variable | ECS cluster name |
| `ECS_SERVICE` | Variable | ECS service name |
| `ECS_TASK_FAMILY` | Variable | ECS task definition family |
| `ECS_CONTAINER_NAME` | Variable | Container name within the task definition |

To run the same CI checks locally:

**Backend:**

```bash
make be-lint      # ruff check .
make be-format    # ruff format --check .
make be-test      # pytest
```

**Frontend:**

```bash
make fe-lint      # eslint
make fe-test      # vitest run
```

## API Design

Backend API responses are defined using **Pydantic schemas** in `backend/app/schemas/`. These serve as the contract between the backend and frontend — every endpoint declares an explicit `response_model`, which FastAPI uses to validate and serialize output.

For example, `GET /sections` returns a list of `SectionResponse` objects:

```python
class SectionResponse(BaseModel):
    SectionID: int
    Schedule: int | None
    TimeBlock: int | None
    Course: int | None
    Capacity: int | None
    Instructor: int | None

    model_config = {"from_attributes": True}
```

`from_attributes = True` allows the schema to be constructed directly from SQLAlchemy ORM instances without a manual conversion step.

FastAPI automatically exposes the full OpenAPI spec at `/docs` (Swagger UI) and `/openapi.json`, which the frontend uses with **Orval** to generate a fully-typed TypeScript API client. This means frontend types stay in sync with backend schemas automatically — a schema change on the backend propagates to the frontend after re-running `npm run generate`.

### Real-Time Updates

The backend exposes a WebSocket endpoint (`/ws`) that broadcasts schedule change events to all connected clients. The frontend subscribes via the `useScheduleWebSocket` hook so edits made by one user are reflected immediately in other open sessions — no polling required.

## License

This project is developed for Khoury College of Computer Sciences at Northeastern University.