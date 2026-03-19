from fastapi import FastAPI

import app.models
from app.core.cors_middleware import setup_cors
from app.core.database import Base, engine
from app.routers import (
    campus,
    comment,
    course,
    faculty,
    schedule,
    section,
    time_block,
    upload,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Automated Course Scheduler API",
    version="1.0.0",
    description="API for the Automated Course Scheduler system",
)

setup_cors(app)

app.include_router(section.router)
app.include_router(schedule.router)
app.include_router(course.router)
app.include_router(faculty.router)
app.include_router(time_block.router)
app.include_router(campus.router)
app.include_router(upload.router)
app.include_router(comment.router)


@app.get("/")
def root():
    return {"message": "Automated Course Scheduler API"}
