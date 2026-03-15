# ------------------------------------------------------------
# This file creates a shared DB connection resource.
# Import `get_db` as a FastAPI dependency in your routes,
# or use `engine` directly for raw SQL / table creation.
# ------------------------------------------------------------
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL"
) or "postgresql://{user}:{password}@{host}:5432/{db}".format(
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ.get("POSTGRES_HOST", "db"),
    db=os.environ["POSTGRES_DB"],
)
# The engine is the shared connection pool — one instance for the app.
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory; each request gets its own session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is used for declaring ORM models later: class MyModel(Base): ...
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session per request
    and closes it when the request is done.

    Usage in a route:
        from app.core.database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            result = db.execute(text("SELECT 1")).fetchone()
            return {"result": result[0]}
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
