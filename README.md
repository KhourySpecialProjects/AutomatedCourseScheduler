# Automated Course Scheduler

A web-based course scheduling platform built for Khoury College of Computer Sciences at Northeastern University. The system automates constraint-based schedule generation while providing intuitive tools for manual refinement, collaboration, and export.

## Overview

Each semester, scheduling administrators must coordinate course offerings, faculty preferences, time blocks, teaching loads, and various constraints to produce a viable course schedule. This platform replaces the current manual, spreadsheet-driven process with an integrated tool that combines algorithmic schedule generation with a collaborative editing interface.

### Key Features

- **CSV Data Ingestion** — Upload historical course offering data and faculty preferences via formatted CSV files
- **Scheduling Algorithm** — Constraint-based optimization that respects hard constraints, prioritizes ranked faculty preferences, and balances time block distribution
- **Schedule Visualization** — Grid-based views organized by professor, department, or time pattern with color-coded constraint violation indicators
- **Manual Editing** — Intuitive drag-and-drop modifications with a two-phase warning system (immediate feedback + holistic scoring)
- **Collaboration** — Role-based access control, Notion-style commenting, draft versioning, and schedule finalization workflows
- **Export** — CSV export formatted for CourseLeaf entry, plus PDF/image exports for sharing

## Tech Stack

| Layer            | Technology                                 |
|------------------|--------------------------------------------|
| Frontend         | React, TypeScript, Tailwind CSS, Orval     |
| Backend          | FastAPI, Pydantic, Python                  |
| ORM              | SQLAlchemy                                 |
| Database         | PostgreSQL                                 |
| Containerization | Docker                                     |

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
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Running with Docker

```bash
# Clone the repository
git clone https://github.com/KhourySpecialProjects/AutomatedCourseScheduler.git
cd automated-course-scheduler

# Copy the example environment file and configure
cp .env.example .env

# Build and start all services
make docker-build
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

## CI

GitHub Actions runs on every pull request targeting `main`. The pipeline is path-scoped so only relevant jobs trigger based on what changed.

| Workflow | Trigger | Steps |
|---|---|---|
| **Backend CI** | Changes to `backend/**` | Ruff lint → Ruff format check → pytest |
| **Frontend CI** | Changes to `frontend/**` | ESLint → Vitest |

All checks must pass before a PR can merge.

To run the same checks locally:

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

## License

This project is developed for Khoury College of Computer Sciences at Northeastern University.