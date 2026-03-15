from fastapi import FastAPI

from app.core.database import Base, engine
from app.routers import section

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(section.router)


@app.get("/")
def root():
    return {"message": "Automated Course Scheduler API"}
