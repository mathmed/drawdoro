from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Environment = Environment.DEVELOPMENT
    app_name: str = "Drawdoro"
    log_level: str = "INFO"
    cors_origins: list[str] = []
    database_url: str = "postgresql+asyncpg://drawdoro:drawdoro@localhost:5432/drawdoro"
    auth_enabled: bool = True
    cognito_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    # Lets trusted services (the MCP server) call the API without a user session.
    service_api_key: str = ""
    # Personal gallery limits. Images are stored in Postgres, so keep them small.
    gallery_max_image_bytes: int = 2 * 1024 * 1024
    gallery_max_shapes_bytes: int = 5 * 1024 * 1024
    # Diagram history: a person's saves within this many minutes share one revision.
    revision_interval_minutes: int = Field(default=10, ge=0)
    # Revisions older than this many days are deleted (0 keeps them regardless of age).
    revision_retention_days: int = Field(default=30, ge=0)
    # At most this many revisions are kept per diagram, newest first (0 keeps any number).
    revision_max_per_diagram: int = Field(default=100, ge=0)

    @property
    def is_production(self) -> bool:
        return self.env == Environment.PRODUCTION

    @property
    def cognito_issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
