from fastapi import FastAPI

from app.core.cors_middleware import setup_cors
from app.core.database import Base, engine
from app.routers import section

Base.metadata.create_all(bind=engine)

app = FastAPI()

setup_cors(app)

app.include_router(section.router)


@app.get("/")
def root():
    return {"message": "Automated Course Scheduler API"}
