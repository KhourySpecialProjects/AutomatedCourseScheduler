# API Endpoints

This document lists all API endpoints.

## Core Endpoints (Must Have)

### 1. Upload Data
- `POST /upload/courses` - Upload course CSV
- `POST /upload/faculty-preferences` - Upload faculty preferences CSV

### 2. Schedule Generation
- `POST /schedules/{id}/generate` - Run algorithm, returns updated schedule

### 3. Schedules (CRUD)
- `GET /schedules` - List all schedules
- `GET /schedules/{id}` - Get schedule with sections, violations, and score 
- `POST /schedules` - Create new schedule
- `PUT /schedules/{id}` - Update schedule name/metadata
- `DELETE /schedules/{id}` - Delete schedule

### 4. Sections (CRUD for editing)
- `GET /sections?schedule_id={id}` - Get sections for a schedule
- `POST /sections` - Create section
- `PUT /sections/{id}` - Update section 
- `DELETE /sections/{id}` - Delete section

### 5. Viewing Data (Read-only for visualization)
- `GET /courses` - List courses
- `GET /faculty` - List faculty
- `GET /time-blocks` - List time blocks
- `GET /campuses` - List campuses

### 6. Export
- `GET /schedules/{id}/export/csv` - Export to CSV

### 7. Comments 
- `GET /comments?schedule_id={id}` - Get comments for schedule
- `POST /comments` - Create comment

