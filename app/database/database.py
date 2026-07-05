from pathlib import Path
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine

from app.utils.config import get_settings

settings = get_settings()

# Ensure the /data directory exists before SQLite tries to create the file
Path("data").mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False}  # required for SQLite + FastAPI
engine = create_engine(settings.database_url, echo=settings.debug, connect_args=connect_args)


def init_db() -> None:
    """Create all tables. Safe to call on every startup (no-op if they exist)."""
    # Import models here so SQLModel's metadata is aware of them
    from app.models import customer, ticket, ticket_history  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    with Session(engine) as session:
        yield session


def reset_db() -> None:
    """Drop and recreate all tables. Destructive — used by scripts/reset_db.py."""
    from app.models import customer, ticket, ticket_history  # noqa: F401

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
