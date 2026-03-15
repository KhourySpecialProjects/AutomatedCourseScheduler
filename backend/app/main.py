from fastapi import FastAPI

from app.routers import section
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(section.router)


@app.get("/")
def root():
    return {"message": "Automated Course Scheduler API"}
