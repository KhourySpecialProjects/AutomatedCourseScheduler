from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized application configuration loaded from environment variables.
    All values are read from the .env file at startup."""

    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_HOST: str = "db"  # host is set to db but overrided if set in env
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    @property
    def db_url(self) -> str:
        """Returns DATABASE_URL if provided, otherwise build it manually."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:5432/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": Path(__file__).parent.parent.parent.parent / ".env"}


settings = Settings()
