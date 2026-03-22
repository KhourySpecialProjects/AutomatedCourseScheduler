import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI

from app.core.auth import get_current_user
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

app.include_router(section.router, dependencies=[Depends(get_current_user)])
app.include_router(schedule.router, dependencies=[Depends(get_current_user)])
app.include_router(course.router, dependencies=[Depends(get_current_user)])
app.include_router(faculty.router, dependencies=[Depends(get_current_user)])
app.include_router(time_block.router, dependencies=[Depends(get_current_user)])
app.include_router(campus.router, dependencies=[Depends(get_current_user)])
app.include_router(upload.router, dependencies=[Depends(get_current_user)])
app.include_router(comment.router, dependencies=[Depends(get_current_user)])


@app.get("/")
def root():
    return {"message": "Automated Course Scheduler API"}
