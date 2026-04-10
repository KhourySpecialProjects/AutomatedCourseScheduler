from dotenv import load_dotenv
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
    section_lock,
    time_block,
    upload,
    user,
    websocket,
)

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Automated Course Scheduler API",
    version="1.0.0",
    description="API for the Automated Course Scheduler system",
    openapi_tags=[],
)

app.openapi_schema = None


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

setup_cors(app)

app.include_router(section.router, dependencies=[Depends(get_current_user)])
app.include_router(schedule.router, dependencies=[Depends(get_current_user)])
app.include_router(course.router, dependencies=[Depends(get_current_user)])
app.include_router(faculty.router, dependencies=[Depends(get_current_user)])
app.include_router(time_block.router, dependencies=[Depends(get_current_user)])
app.include_router(campus.router, dependencies=[Depends(get_current_user)])
app.include_router(upload.router, dependencies=[Depends(get_current_user)])
app.include_router(comment.router, dependencies=[Depends(get_current_user)])
app.include_router(section_lock.router, dependencies=[Depends(get_current_user)])


# custom auth dependencies
app.include_router(user.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    return {"message": "Automated Course Scheduler API"}
