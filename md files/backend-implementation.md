# Backend Implementation Guide

A complete, step-by-step implementation of the FastAPI backend: project scaffolding, database layer, and the Customer / Ticket models. Follow the sections in order — each one is runnable and testable before you move to the next.

---

## 1. Project Setup

### 1.1 Create the base project folders

Run this from your project root:

```bash
mkdir -p app/models app/services app/agents app/workflows app/database app/api app/utils
mkdir -p data/knowledge_base
mkdir -p tests scripts

touch app/__init__.py app/models/__init__.py app/services/__init__.py \
      app/agents/__init__.py app/workflows/__init__.py app/database/__init__.py \
      app/api/__init__.py app/utils/__init__.py
```

Resulting structure:

```
app/
├── __init__.py
├── main.py
├── models/
│   ├── __init__.py
│   ├── customer.py
│   └── ticket.py
├── services/
│   ├── __init__.py
│   ├── customer_service.py
│   └── ticket_service.py
├── agents/
│   └── __init__.py
├── workflows/
│   └── __init__.py
├── database/
│   ├── __init__.py
│   └── database.py
├── api/
│   ├── __init__.py
│   └── tickets.py
└── utils/
    └── __init__.py

data/
├── knowledge_base/
├── customers.json
├── sample_tickets.json
└── tickets.db          # created automatically on first run

tests/
├── __init__.py
├── test_health.py
├── test_customers.py
└── test_tickets.py

scripts/
├── reset_db.py
└── seed_data.py
```

### 1.2 Create `requirements.txt`

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlmodel==0.0.22
pydantic==2.9.2
pytest==8.3.3
python-dotenv==1.0.1
httpx==0.27.2
```

Notes:
- `sqlmodel` gives you SQLAlchemy + Pydantic in one model definition — recommended over raw SQLAlchemy for this project.
- `httpx` is included so `TestClient`/async tests work cleanly with FastAPI.
- `uvicorn[standard]` pulls in `websockets` and `watchfiles` for reliable `--reload` behavior.

Install:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3 Create `.env.example`

```env
# App
APP_NAME=Support Ticket Backend
APP_VERSION=0.1.0
DEBUG=True

# Database
DATABASE_URL=sqlite:///./data/tickets.db

# CORS (comma-separated origins allowed to call this API)
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

# LLM / Agent config (fill in when agents are implemented)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

Copy it locally (never commit the real `.env`):

```bash
cp .env.example .env
```

### 1.4 Create `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
venv/
.venv/

# Env
.env

# Database
data/tickets.db
data/*.db-journal

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
```

### 1.5 Add a basic `README.md`

```markdown
# Support Ticket Backend

FastAPI backend for AI-assisted support ticket triage and management.

## Setup

\`\`\`bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
\`\`\`

## Run

\`\`\`bash
uvicorn app.main:app --reload
\`\`\`

API docs: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health

## Scripts

\`\`\`bash
python scripts/seed_data.py    # load sample customers/tickets
python scripts/reset_db.py     # drop and recreate all tables
\`\`\`

## Tests

\`\`\`bash
pytest
\`\`\`
```

### 1.6 Confirm the application starts

```bash
uvicorn app.main:app --reload
```

Expected console output includes `Application startup complete.` and the app should respond at `GET /health` (built in section 2). Note the correct spacing: `uvicorn app.main:app --reload` (a space, not `app:app--reload`).

---

## 2. FastAPI Foundation

### 2.1 `app/main.py`

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database.database import init_db
from app.api.tickets import router as tickets_router
from app.utils.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up %s v%s", settings.app_name, settings.app_version)
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for AI-assisted support ticket triage.",
    lifespan=lifespan,
)

# --- CORS (allow the Streamlit frontend to call this API) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global exception handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected error occurred.",
        },
    )


# --- Routers ---
app.include_router(tickets_router)


# --- Health check ---
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "healthy"}
```

### 2.2 `app/utils/config.py`

Centralizes settings loading (used by `main.py` and `database.py`):

```python
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Support Ticket Backend"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str = "sqlite:///./data/tickets.db"
    cors_origins_raw: str = "http://localhost:8501,http://127.0.0.1:8501"

    class Config:
        env_file = ".env"
        env_prefix = ""
        fields = {"cors_origins_raw": {"env": "CORS_ORIGINS"}}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

> Add `pydantic-settings==2.5.2` to `requirements.txt` (Pydantic v2 moved `BaseSettings` into a separate package).

### 2.3 Verify

```bash
uvicorn app.main:app --reload
curl http://127.0.0.1:8000/health
# {"status":"healthy"}
```

Visit `http://127.0.0.1:8000/docs` to confirm the interactive OpenAPI docs render and the ticket routes appear.

---

## 3. Database Setup

### 3.1 `app/database/database.py`

```python
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
    from app.models import customer, ticket  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    with Session(engine) as session:
        yield session


def reset_db() -> None:
    """Drop and recreate all tables. Destructive — used by scripts/reset_db.py."""
    from app.models import customer, ticket  # noqa: F401

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
```

Key points:
- `data/tickets.db` is created automatically the first time `init_db()` runs (called in `main.py`'s lifespan handler), so tables — and any rows you insert — persist across restarts.
- `check_same_thread: False` is required because SQLite by default only allows the thread that created a connection to use it; FastAPI serves requests from a thread pool.
- `get_session` is used as a FastAPI `Depends(...)` in the API layer (see section 5).

### 3.2 `scripts/reset_db.py`

```python
"""Drop and recreate all tables. Usage: python scripts/reset_db.py"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.database import reset_db

if __name__ == "__main__":
    confirm = input("This will DELETE all data in tickets.db. Type 'yes' to continue: ")
    if confirm.strip().lower() == "yes":
        reset_db()
        print("Database reset complete.")
    else:
        print("Aborted.")
```

### 3.3 `scripts/seed_data.py`

```python
"""Load sample customers and tickets from data/*.json into the database.
Usage: python scripts/seed_data.py
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database.database import engine, init_db
from app.models.customer import Customer
from app.models.ticket import Ticket

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def seed():
    init_db()
    with Session(engine) as session:
        customers_path = DATA_DIR / "customers.json"
        if customers_path.exists():
            customers = json.loads(customers_path.read_text())
            for c in customers:
                if not session.get(Customer, c["customer_id"]):
                    session.add(Customer(**c))
            session.commit()
            print(f"Seeded {len(customers)} customers.")

        tickets_path = DATA_DIR / "sample_tickets.json"
        if tickets_path.exists():
            tickets = json.loads(tickets_path.read_text())
            for t in tickets:
                if not session.get(Ticket, t.get("ticket_id")):
                    session.add(Ticket(**t))
            session.commit()
            print(f"Seeded {len(tickets)} tickets.")


if __name__ == "__main__":
    seed()
```

### 3.4 Confirm data survives restarts

```bash
python scripts/seed_data.py
uvicorn app.main:app --reload
# Ctrl+C to stop, then start again
uvicorn app.main:app --reload
curl http://127.0.0.1:8000/api/tickets
# Seeded tickets should still be returned
```

Since SQLite persists to `data/tickets.db` on disk (not `:memory:`), restarting the app does not clear data — only running `scripts/reset_db.py` does.

---

## 4. Customer Model

### 4.1 `app/models/customer.py`

```python
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    customer_id: str = Field(primary_key=True, index=True)
    name: str
    plan: str = Field(default="free")  # e.g. free / pro / enterprise
    account_status: str = Field(default="active")  # active / suspended / churned
    previous_tickets: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tickets: List["Ticket"] = Relationship(back_populates="customer")


# --- Pydantic schemas (request/response) ---

class CustomerCreate(SQLModel):
    customer_id: str
    name: str
    plan: str = "free"
    account_status: str = "active"
    previous_tickets: int = 0


class CustomerResponse(SQLModel):
    customer_id: str
    name: str
    plan: str
    account_status: str
    previous_tickets: int
    created_at: datetime
```

### 4.2 Sample customers — `data/customers.json`

```json
[
  {
    "customer_id": "CUST-1001",
    "name": "Ava Thompson",
    "plan": "enterprise",
    "account_status": "active",
    "previous_tickets": 12
  },
  {
    "customer_id": "CUST-1002",
    "name": "Marcus Lee",
    "plan": "pro",
    "account_status": "active",
    "previous_tickets": 3
  },
  {
    "customer_id": "CUST-1003",
    "name": "Priya Nair",
    "plan": "free",
    "account_status": "active",
    "previous_tickets": 0
  },
  {
    "customer_id": "CUST-1004",
    "name": "Diego Fernandez",
    "plan": "pro",
    "account_status": "suspended",
    "previous_tickets": 7
  },
  {
    "customer_id": "CUST-1005",
    "name": "Hana Kobayashi",
    "plan": "enterprise",
    "account_status": "active",
    "previous_tickets": 25
  }
]
```

### 4.3 `app/services/customer_service.py`

```python
from sqlmodel import Session

from app.models.customer import Customer


class CustomerNotFoundError(Exception):
    """Raised when a customer_id does not exist in the database."""

    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        super().__init__(f"Customer '{customer_id}' was not found.")


def get_customer_by_id(session: Session, customer_id: str) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise CustomerNotFoundError(customer_id)
    return customer
```

Wire the error into a clean HTTP response by catching it in the API layer (see `app/api/tickets.py` pattern in section 5) or add a dedicated handler in `main.py`:

```python
from fastapi import status
from fastapi.responses import JSONResponse
from app.services.customer_service import CustomerNotFoundError

@app.exception_handler(CustomerNotFoundError)
async def customer_not_found_handler(request, exc: CustomerNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "customer_not_found", "detail": str(exc)},
    )
```

---

## 5. Ticket Model

### 5.1 Enums — `app/models/enums.py`

```python
from enum import Enum


class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


class TicketStatus(str, Enum):
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportTeam(str, Enum):
    TIER1 = "tier1_support"
    TIER2 = "tier2_support"
    BILLING = "billing_team"
    ENGINEERING = "engineering"
    ACCOUNT_MANAGEMENT = "account_management"
```

Using `str, Enum` subclasses with SQLModel/SQLAlchemy automatically restricts stored values to the enum's members — any other value raises a `ValueError` (or a `422` via Pydantic) before it reaches the database, satisfying "prevent invalid status/priority values."

### 5.2 `app/models/ticket.py`

```python
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from app.models.enums import TicketCategory, TicketStatus, TicketPriority, SupportTeam

if TYPE_CHECKING:
    from app.models.customer import Customer


def generate_ticket_id() -> str:
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    ticket_id: str = Field(default_factory=generate_ticket_id, primary_key=True, index=True)
    customer_id: str = Field(foreign_key="customers.customer_id", index=True)

    message: str
    status: TicketStatus = Field(default=TicketStatus.NEW)
    category: Optional[TicketCategory] = Field(default=None)
    subcategory: Optional[str] = Field(default=None)
    priority: Optional[TicketPriority] = Field(default=None)
    assigned_team: Optional[SupportTeam] = Field(default=None)

    classification_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    ai_reason: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    customer: Optional["Customer"] = Relationship(back_populates="tickets")


# --- Pydantic schemas ---

class TicketCreate(SQLModel):
    customer_id: str
    message: str
    category: Optional[TicketCategory] = None
    subcategory: Optional[str] = None
    priority: Optional[TicketPriority] = None
    assigned_team: Optional[SupportTeam] = None


class TicketUpdate(SQLModel):
    status: Optional[TicketStatus] = None
    category: Optional[TicketCategory] = None
    subcategory: Optional[str] = None
    priority: Optional[TicketPriority] = None
    assigned_team: Optional[SupportTeam] = None
    classification_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    ai_reason: Optional[str] = None


class TicketResponse(SQLModel):
    ticket_id: str
    customer_id: str
    message: str
    status: TicketStatus
    category: Optional[TicketCategory]
    subcategory: Optional[str]
    priority: Optional[TicketPriority]
    assigned_team: Optional[SupportTeam]
    classification_confidence: Optional[float]
    ai_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
```

Notes on the checklist items:
- **Foreign key to Customer**: `customer_id: str = Field(foreign_key="customers.customer_id", ...)` plus the two-way `Relationship` declarations in both models.
- **Auto-generated ticket IDs**: `default_factory=generate_ticket_id` produces IDs like `TKT-3F9A21B4` without the client needing to supply one.
- **Invalid status/priority prevented**: enforced by the `TicketStatus` / `TicketPriority` enum types at both the Pydantic validation layer (`TicketCreate`/`TicketUpdate`) and the database column type.

### 5.3 `app/services/ticket_service.py`

```python
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.ticket import Ticket, TicketCreate, TicketUpdate
from app.services.customer_service import get_customer_by_id


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id
        super().__init__(f"Ticket '{ticket_id}' was not found.")


def create_ticket(session: Session, data: TicketCreate) -> Ticket:
    # Validates the customer exists; raises CustomerNotFoundError otherwise
    get_customer_by_id(session, data.customer_id)

    ticket = Ticket(**data.model_dump())
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def get_ticket_by_id(session: Session, ticket_id: str) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    return ticket


def list_tickets(
    session: Session,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> List[Ticket]:
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    if customer_id:
        query = query.where(Ticket.customer_id == customer_id)
    return list(session.exec(query))


def update_ticket(session: Session, ticket_id: str, data: TicketUpdate) -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(ticket, field, value)
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
```

### 5.4 `app/api/tickets.py`

```python
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database.database import get_session
from app.models.ticket import TicketCreate, TicketUpdate, TicketResponse
from app.services import ticket_service
from app.services.customer_service import CustomerNotFoundError
from app.services.ticket_service import TicketNotFoundError

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, session: Session = Depends(get_session)):
    try:
        return ticket_service.create_ticket(session, payload)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status_filter: Optional[str] = None,
    customer_id: Optional[str] = None,
    session: Session = Depends(get_session),
):
    return ticket_service.list_tickets(session, status=status_filter, customer_id=customer_id)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: str, session: Session = Depends(get_session)):
    try:
        return ticket_service.get_ticket_by_id(session, ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: str, payload: TicketUpdate, session: Session = Depends(get_session)):
    try:
        return ticket_service.update_ticket(session, ticket_id, payload)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
```

### 5.5 Sample tickets — `data/sample_tickets.json`

```json
[
  {
    "customer_id": "CUST-1001",
    "message": "I was charged twice for my enterprise subscription this month.",
    "status": "new",
    "category": "billing",
    "subcategory": "duplicate_charge",
    "priority": "high",
    "assigned_team": "billing_team",
    "classification_confidence": 0.94,
    "ai_reason": "Message explicitly mentions duplicate billing charge."
  },
  {
    "customer_id": "CUST-1002",
    "message": "The API keeps returning a 500 error when I upload files over 10MB.",
    "status": "open",
    "category": "technical",
    "subcategory": "api_error",
    "priority": "urgent",
    "assigned_team": "engineering",
    "classification_confidence": 0.89,
    "ai_reason": "Server error with a reproducible technical trigger."
  },
  {
    "customer_id": "CUST-1003",
    "message": "How do I reset my password? I can't find the option in settings.",
    "status": "new",
    "category": "account",
    "subcategory": "password_reset",
    "priority": "low",
    "assigned_team": "tier1_support",
    "classification_confidence": 0.97,
    "ai_reason": "Straightforward account self-service question."
  }
]
```

---

## Verification Checklist

Run through this once all sections above are implemented:

```bash
# 1. Install & configure
pip install -r requirements.txt
cp .env.example .env

# 2. Seed and start
python scripts/seed_data.py
uvicorn app.main:app --reload

# 3. Smoke test
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/tickets
curl -X POST http://127.0.0.1:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1001", "message": "Test ticket"}'

# 4. Restart and confirm persistence
# (Ctrl+C, then re-run uvicorn) — GET /api/tickets should show the same data.

# 5. Run tests
pytest
```

If all five steps succeed, the foundation (FastAPI app, health endpoint, SQLite persistence, Customer/Ticket models, and sample data) is complete and ready for the agent/workflow layers.
