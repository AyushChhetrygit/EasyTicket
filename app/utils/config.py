from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Support Ticket Backend"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str = "sqlite:///./data/tickets.db"
    cors_origins_raw: str = "http://localhost:8501,http://127.0.0.1:8501"

    model_config = {
        "env_file": ".env",
        "env_prefix": "",
        "populate_by_name": True,
        "extra": "ignore",
    }

    # Map CORS_ORIGINS env var to cors_origins_raw field
    @classmethod
    def model_fields_set_from_env(cls):
        return {}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
