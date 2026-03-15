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
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route-level page components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API client functions
│   │   ├── types/           # TypeScript type definitions
│   │   └── utils/           # Helper utilities
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── routers/         # Route handlers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic & algorithm
│   │   ├── core/            # Config, security, dependencies
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
docker compose up --build
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs

### Local Development

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable              | Description                     | Default                |
|-----------------------|---------------------------------|------------------------|
| `DATABASE_URL`        | PostgreSQL connection string    | see `.env.example`     |
| `SECRET_KEY`          | JWT signing key                 | —                      |
| `CORS_ORIGINS`        | Allowed frontend origins        | `http://localhost:3000`|

## User Roles

| Role        | Permissions                                                        |
|-------------|--------------------------------------------------------------------|
| **Admin**   | Upload data, run algorithm, edit schedules, override warnings, export |
| **Viewer**  | View schedules, leave comments                                     |

## License

This project is developed for Khoury College of Computer Sciences at Northeastern University.