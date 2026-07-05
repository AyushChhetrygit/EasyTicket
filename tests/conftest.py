import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ["DATABASE_URL"] = "sqlite:///./data/test_tickets.db"

import pytest
from sqlmodel import SQLModel, Session, create_engine
from fastapi.testclient import TestClient

from app.main import app
from app.database.database import get_session
from app.models.customer import Customer

TEST_DB_PATH = Path("data/test_tickets.db")
engine = create_engine(
    "sqlite:///./data/test_tickets.db",
    connect_args={"check_same_thread": False},
)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Path("data").mkdir(exist_ok=True)
    # Import models here so SQLModel's metadata is aware of them
    from app.models import customer, ticket, ticket_history  # noqa: F401
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session():
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_customer(session):
    customer = Customer(customer_id="CUST-TEST-1", name="Test User", plan="pro")
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer
