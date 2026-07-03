# Backend Implementation Guide — Part 2

Continues directly from `backend-implementation.md`. Covers: ticket history, the full ticket API surface, the rule-based fallback router, the AI integration adapter (the seam your teammate's AI service plugs into), and the test suite.

---

## 6. Ticket History Model

### 6.1 `app/models/ticket_history.py`

```python
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


def generate_history_id() -> str:
    return f"HIST-{uuid.uuid4().hex[:8].upper()}"


class TicketHistory(SQLModel, table=True):
    __tablename__ = "ticket_history"

    history_id: str = Field(default_factory=generate_history_id, primary_key=True, index=True)
    ticket_id: str = Field(foreign_key="tickets.ticket_id", index=True)

    action: str  # e.g. "created", "status_changed", "team_assigned", "priority_changed",
                 # "escalated", "ai_analysis"
    old_value: Optional[str] = Field(default=None)
    new_value: Optional[str] = Field(default=None)
    performed_by: str = Field(default="system")  # "system", "ai", or a user/agent id

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TicketHistoryResponse(SQLModel):
    history_id: str
    ticket_id: str
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    performed_by: str
    created_at: datetime
```

Register it with the database so `create_all` picks it up — update the imports in `app/database/database.py`:

```python
def init_db() -> None:
    from app.models import customer, ticket, ticket_history  # noqa: F401
    SQLModel.metadata.create_all(engine)
```

(Do the same in `reset_db()`.)

### 6.2 `app/services/history_service.py`

One helper per event type, plus a generic `log_event` underneath so new event types are cheap to add later.

```python
from typing import List, Optional

from sqlmodel import Session, select

from app.models.ticket_history import TicketHistory


def log_event(
    session: Session,
    ticket_id: str,
    action: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    performed_by: str = "system",
) -> TicketHistory:
    entry = TicketHistory(
        ticket_id=ticket_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def record_ticket_created(session: Session, ticket_id: str, performed_by: str = "system") -> TicketHistory:
    return log_event(session, ticket_id, action="created", new_value="open", performed_by=performed_by)


def record_status_change(session: Session, ticket_id: str, old_status: str, new_status: str, performed_by: str = "system") -> TicketHistory:
    return log_event(session, ticket_id, action="status_changed", old_value=old_status, new_value=new_status, performed_by=performed_by)


def record_team_assignment(session: Session, ticket_id: str, old_team: Optional[str], new_team: str, performed_by: str = "system") -> TicketHistory:
    return log_event(session, ticket_id, action="team_assigned", old_value=old_team, new_value=new_team, performed_by=performed_by)


def record_priority_change(session: Session, ticket_id: str, old_priority: Optional[str], new_priority: str, performed_by: str = "system") -> TicketHistory:
    return log_event(session, ticket_id, action="priority_changed", old_value=old_priority, new_value=new_priority, performed_by=performed_by)


def record_manual_escalation(session: Session, ticket_id: str, reason: str, performed_by: str = "user") -> TicketHistory:
    return log_event(session, ticket_id, action="escalated", new_value=reason, performed_by=performed_by)


def record_ai_analysis(session: Session, ticket_id: str, summary: str, performed_by: str = "ai") -> TicketHistory:
    return log_event(session, ticket_id, action="ai_analysis", new_value=summary, performed_by=performed_by)


def get_ticket_history(session: Session, ticket_id: str) -> List[TicketHistory]:
    query = select(TicketHistory).where(TicketHistory.ticket_id == ticket_id).order_by(TicketHistory.created_at)
    return list(session.exec(query))
```

---

## 7. Ticket API Endpoints

This section replaces the minimal `app/api/tickets.py` from Part 1 with the full endpoint set, wired to `history_service`.

### 7.1 Updated `app/services/ticket_service.py`

Adds history logging on every mutation, plus an `escalate_ticket` function.

```python
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.ticket import Ticket, TicketCreate, TicketUpdate, TicketStatus, SupportTeam
from app.services.customer_service import get_customer_by_id
from app.services import history_service


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id
        super().__init__(f"Ticket '{ticket_id}' was not found.")


def create_ticket(session: Session, data: TicketCreate, performed_by: str = "system") -> Ticket:
    # Raises CustomerNotFoundError if the customer doesn't exist
    get_customer_by_id(session, data.customer_id)

    ticket = Ticket(**data.model_dump(), status=TicketStatus.OPEN)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    history_service.record_ticket_created(session, ticket.ticket_id, performed_by=performed_by)
    return ticket


def get_ticket_by_id(session: Session, ticket_id: str) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    return ticket


def list_tickets(
    session: Session,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_team: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> List[Ticket]:
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)
    if priority:
        query = query.where(Ticket.priority == priority)
    if assigned_team:
        query = query.where(Ticket.assigned_team == assigned_team)

    query = query.order_by(Ticket.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return list(session.exec(query))


def update_ticket(session: Session, ticket_id: str, data: TicketUpdate, performed_by: str = "system") -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)
    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        old_value = getattr(ticket, field)
        if old_value == value:
            continue

        if field == "status":
            history_service.record_status_change(session, ticket_id, str(old_value), str(value), performed_by)
        elif field == "assigned_team":
            history_service.record_team_assignment(session, ticket_id, str(old_value) if old_value else None, str(value), performed_by)
        elif field == "priority":
            history_service.record_priority_change(session, ticket_id, str(old_value) if old_value else None, str(value), performed_by)

        setattr(ticket, field, value)

    ticket.updated_at = datetime.now(timezone.utc)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def escalate_ticket(session: Session, ticket_id: str, reason: str, team: Optional[str] = None, performed_by: str = "user") -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)

    old_status = ticket.status
    ticket.status = TicketStatus.ESCALATED
    ticket.assigned_team = team or SupportTeam.ENGINEERING
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    history_service.record_status_change(session, ticket_id, str(old_status), str(ticket.status), performed_by)
    history_service.record_manual_escalation(session, ticket_id, reason, performed_by)
    return ticket
```

Note on the checklist item "assign Engineering when no team is supplied": `ticket.assigned_team = team or SupportTeam.ENGINEERING` handles that directly.

### 7.2 Request schemas for escalation — add to `app/models/ticket.py`

```python
class TicketEscalateRequest(SQLModel):
    reason: str
    team: Optional[SupportTeam] = None
```

### 7.3 Full `app/api/tickets.py`

```python
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database.database import get_session
from app.models.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketEscalateRequest,
)
from app.models.ticket_history import TicketHistoryResponse
from app.services import ticket_service, history_service
from app.services.customer_service import CustomerNotFoundError
from app.services.ticket_service import TicketNotFoundError

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, session: Session = Depends(get_session)):
    try:
        return ticket_service.create_ticket(session, payload)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_team: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return ticket_service.list_tickets(
        session,
        status=status_filter,
        category=category,
        priority=priority,
        assigned_team=assigned_team,
        page=page,
        page_size=page_size,
    )


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


@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
def escalate_ticket(ticket_id: str, payload: TicketEscalateRequest, session: Session = Depends(get_session)):
    try:
        return ticket_service.escalate_ticket(
            session, ticket_id, reason=payload.reason, team=payload.team
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{ticket_id}/history", response_model=List[TicketHistoryResponse])
def get_ticket_history(ticket_id: str, session: Session = Depends(get_session)):
    # Confirm the ticket exists first so an unknown ticket_id returns 404, not an empty list
    try:
        ticket_service.get_ticket_by_id(session, ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return history_service.get_ticket_history(session, ticket_id)
```

> **Path change from Part 1:** the router prefix moves from `/api/tickets` to `/tickets` to match the project plan's `POST /tickets`, `GET /tickets`, etc. Update the `include_router` call and any Streamlit/frontend calls accordingly. If your frontend already depends on `/api/tickets`, keep that prefix instead and just mentally substitute it in the examples below.

---

## 8. Rule-Based Fallback Router

Deterministic keyword router. No LLM dependency, so it works immediately and gives the AI service something to fall back to.

### 8.1 `app/services/rule_based_router.py`

```python
from dataclasses import dataclass
from typing import Optional

from app.models.enums import TicketCategory, TicketPriority, SupportTeam

# --- Keyword banks ---

BILLING_KEYWORDS = ["payment", "charged", "invoice", "subscription"]
REFUND_KEYWORDS = ["refund", "money back", "cancel purchase"]
TECHNICAL_KEYWORDS = ["api", "error", "crash", "integration"]
ACCOUNT_KEYWORDS = ["login", "password", "locked", "account"]
FEATURE_REQUEST_KEYWORDS = ["feature", "enhancement", "support for", "would like"]
OUTAGE_KEYWORDS = ["entire service down", "everyone cannot access", "complete outage"]


@dataclass
class RuleBasedResult:
    category: TicketCategory
    subcategory: Optional[str]
    priority: TicketPriority
    assigned_team: SupportTeam
    reason: str
    confidence: float


def _matches(text: str, keywords: list[str]) -> Optional[str]:
    """Return the first matching keyword, or None."""
    for kw in keywords:
        if kw in text:
            return kw
    return None


def classify_ticket(message: str) -> RuleBasedResult:
    text = message.lower()

    # Outage takes priority over everything else — highest urgency, widest impact
    if hit := _matches(text, OUTAGE_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.TECHNICAL,
            subcategory="outage",
            priority=TicketPriority.URGENT,
            assigned_team=SupportTeam.ENGINEERING,
            reason=f"Matched outage keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, REFUND_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.BILLING,
            subcategory="refund_request",
            priority=TicketPriority.HIGH,
            assigned_team=SupportTeam.BILLING,
            reason=f"Matched refund keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, BILLING_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.BILLING,
            subcategory=None,
            priority=TicketPriority.MEDIUM,
            assigned_team=SupportTeam.BILLING,
            reason=f"Matched billing keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, TECHNICAL_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.TECHNICAL,
            subcategory=None,
            priority=TicketPriority.MEDIUM,
            assigned_team=SupportTeam.TIER2,
            reason=f"Matched technical keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, ACCOUNT_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.ACCOUNT,
            subcategory=None,
            priority=TicketPriority.LOW,
            assigned_team=SupportTeam.TIER1,
            reason=f"Matched account keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, FEATURE_REQUEST_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.FEATURE_REQUEST,
            subcategory=None,
            priority=TicketPriority.LOW,
            assigned_team=SupportTeam.ACCOUNT_MANAGEMENT,
            reason=f"Matched feature-request keyword: '{hit}'.",
            confidence=0.6,
        )

    # No keyword matched — generic default, low confidence
    return RuleBasedResult(
        category=TicketCategory.GENERAL,
        subcategory=None,
        priority=TicketPriority.LOW,
        assigned_team=SupportTeam.TIER1,
        reason="No keyword rule matched; defaulted to general/tier1.",
        confidence=0.3,
    )
```

Design notes:
- Checked in priority order (outage → refund → billing → technical → account → feature request) so a message hitting multiple banks resolves predictably instead of arbitrarily.
- Returns a plain dataclass, not a DB row — deliberately decoupled from `Ticket` so it stays callable with just a string, from anywhere (a script, a test, the AI adapter's fallback path).
- `confidence` is fixed per rule type since it's not a probabilistic model; you can tune these numbers as you see real ticket data.

---

## 9. AI Integration Adapter

This is the seam for your teammate's AI service. It defines the interface, returns rule-based results today, and is built so swapping in the real LLM call later means editing one function body — not any of the call sites.

### 9.1 `app/services/analysis_service.py`

```python
import asyncio
from dataclasses import dataclass
from typing import Literal, Optional

from app.models.customer import Customer
from app.models.ticket import Ticket
from app.services.rule_based_router import classify_ticket, RuleBasedResult

AnalysisSource = Literal["ai", "rule_based_fallback"]

AI_TIMEOUT_SECONDS = 10


@dataclass
class AnalysisResult:
    category: str
    subcategory: Optional[str]
    priority: str
    assigned_team: str
    reason: str
    confidence: float
    source: AnalysisSource


class InvalidAIOutputError(Exception):
    """Raised when the AI service returns a result that fails validation."""


async def _call_ai_service(ticket: Ticket, customer: Customer) -> AnalysisResult:
    """
    Placeholder for Teammate 2's AI service call.

    Replace this function body with the real implementation, e.g.:

        response = await ai_client.analyze(ticket=ticket, customer=customer)
        return AnalysisResult(
            category=response.category,
            subcategory=response.subcategory,
            priority=response.priority,
            assigned_team=response.assigned_team,
            reason=response.reason,
            confidence=response.confidence,
            source="ai",
        )

    Until then, this intentionally raises so `analyze_ticket()` exercises the
    fallback path — remove the `raise` once the real call is wired in.
    """
    raise NotImplementedError("AI service not yet implemented")


def _rule_result_to_analysis(result: RuleBasedResult) -> AnalysisResult:
    return AnalysisResult(
        category=result.category.value,
        subcategory=result.subcategory,
        priority=result.priority.value,
        assigned_team=result.assigned_team.value,
        reason=result.reason,
        confidence=result.confidence,
        source="rule_based_fallback",
    )


def _validate_ai_result(result: AnalysisResult) -> None:
    if not (0.0 <= result.confidence <= 1.0):
        raise InvalidAIOutputError(f"confidence out of range: {result.confidence}")
    if not result.category or not result.priority or not result.assigned_team:
        raise InvalidAIOutputError("AI result missing required field(s).")


async def analyze_ticket(ticket: Ticket, customer: Customer) -> AnalysisResult:
    """
    Analyze a ticket and return category/priority/team/reason.

    Tries the AI service first; falls back to the rule-based router on
    timeout, exception, or invalid output so this endpoint never hard-fails.
    """
    try:
        result = await asyncio.wait_for(
            _call_ai_service(ticket, customer), timeout=AI_TIMEOUT_SECONDS
        )
        _validate_ai_result(result)
        return result

    except asyncio.TimeoutError:
        fallback = classify_ticket(ticket.message)
        return _rule_result_to_analysis(fallback)

    except (InvalidAIOutputError, NotImplementedError, Exception):
        # Broad except is intentional here: any failure in the AI path
        # (network error, bad JSON, unexpected exception type, etc.) should
        # degrade to the rule-based router rather than surface a 500 to the
        # caller. Log this in production rather than silently swallowing it.
        fallback = classify_ticket(ticket.message)
        return _rule_result_to_analysis(fallback)
```

> **Handoff note for Teammate 2:** implement the real AI call inside `_call_ai_service`, keeping the return type `AnalysisResult` with `source="ai"`. Everything downstream (`analyze_ticket`, the endpoint, history logging) already handles both sources uniformly — no other file needs to change.

### 9.2 `POST /tickets/{ticket_id}/analyze` — add to `app/api/tickets.py`

```python
from app.services import analysis_service
from app.services.customer_service import get_customer_by_id


@router.post("/{ticket_id}/analyze", response_model=TicketResponse)
async def analyze_ticket(ticket_id: str, session: Session = Depends(get_session)):
    try:
        ticket = ticket_service.get_ticket_by_id(session, ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    try:
        customer = get_customer_by_id(session, ticket.customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    result = await analysis_service.analyze_ticket(ticket, customer)

    old_category = ticket.category
    old_priority = ticket.priority
    old_team = ticket.assigned_team

    ticket.category = result.category
    ticket.subcategory = result.subcategory
    ticket.priority = result.priority
    ticket.assigned_team = result.assigned_team
    ticket.classification_confidence = result.confidence
    ticket.ai_reason = result.reason

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    performed_by = "ai" if result.source == "ai" else "system"
    if old_category != ticket.category:
        history_service.log_event(session, ticket_id, "category_changed", str(old_category), str(ticket.category), performed_by)
    if old_priority != ticket.priority:
        history_service.record_priority_change(session, ticket_id, str(old_priority) if old_priority else None, str(ticket.priority), performed_by)
    if old_team != ticket.assigned_team:
        history_service.record_team_assignment(session, ticket_id, str(old_team) if old_team else None, str(ticket.assigned_team), performed_by)
    history_service.record_ai_analysis(session, ticket_id, result.reason, performed_by=result.source)

    response = TicketResponse.model_validate(ticket, from_attributes=True).model_dump()
    response["analysis_source"] = result.source
    return response
```

Since `analysis_source` isn't a column on `Ticket`, the response is assembled as a dict rather than returned straight through `response_model=TicketResponse` (which would silently drop the extra field). If you'd rather keep strict typing, add an `AnalyzeTicketResponse(TicketResponse)` schema with `analysis_source: str` and use that as the route's `response_model` instead.

Example response:

```json
{
  "ticket_id": "TKT-3F9A21B4",
  "category": "billing",
  "priority": "high",
  "assigned_team": "billing_team",
  "classification_confidence": 0.6,
  "ai_reason": "Matched refund keyword: 'refund'.",
  "analysis_source": "rule_based_fallback"
}
```

---

## 10. Backend Tests

### 10.1 Separate test database — `tests/conftest.py`

Uses an isolated SQLite file (not `data/tickets.db`) so tests never touch development data, and overrides the `get_session` dependency so the API layer transparently uses it.

```python
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
```

Add `data/test_tickets.db` to `.gitignore` alongside `data/tickets.db`.

### 10.2 `tests/test_health.py`

```python
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

### 10.3 `tests/test_customers.py`

```python
from app.services.customer_service import get_customer_by_id, CustomerNotFoundError


def test_get_customer_by_id(session, sample_customer):
    customer = get_customer_by_id(session, sample_customer.customer_id)
    assert customer.customer_id == sample_customer.customer_id


def test_get_customer_invalid_id_raises(session):
    try:
        get_customer_by_id(session, "CUST-DOES-NOT-EXIST")
        assert False, "expected CustomerNotFoundError"
    except CustomerNotFoundError:
        pass
```

### 10.4 `tests/test_tickets.py`

```python
def test_create_ticket(client, sample_customer):
    response = client.post("/tickets", json={
        "customer_id": sample_customer.customer_id,
        "message": "I can't log into my account.",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"
    assert body["ticket_id"].startswith("TKT-")


def test_create_ticket_invalid_customer(client):
    response = client.post("/tickets", json={
        "customer_id": "CUST-NOPE",
        "message": "Test message",
    })
    assert response.status_code == 404


def test_list_tickets(client, sample_customer):
    client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket A"})
    client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket B"})

    response = client.get("/tickets")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_ticket(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.get(f"/tickets/{created['ticket_id']}")
    assert response.status_code == 200
    assert response.json()["ticket_id"] == created["ticket_id"]


def test_get_ticket_not_found(client):
    response = client.get("/tickets/TKT-DOESNOTEXIST")
    assert response.status_code == 404


def test_update_ticket(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.patch(f"/tickets/{created['ticket_id']}", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_ticket_invalid_status(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.patch(f"/tickets/{created['ticket_id']}", json={"status": "not_a_real_status"})
    assert response.status_code == 422


def test_manual_escalation(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.post(f"/tickets/{created['ticket_id']}/escalate", json={"reason": "Customer very upset"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "escalated"
    assert body["assigned_team"] == "engineering"  # default when no team supplied


def test_ticket_history(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()
    client.patch(f"/tickets/{created['ticket_id']}", json={"status": "in_progress"})

    response = client.get(f"/tickets/{created['ticket_id']}/history")
    assert response.status_code == 200
    actions = [entry["action"] for entry in response.json()]
    assert "created" in actions
    assert "status_changed" in actions
```

### 10.5 `tests/test_rule_based_router.py`

```python
from app.services.rule_based_router import classify_ticket
from app.models.enums import TicketCategory, SupportTeam


def test_billing_routing():
    result = classify_ticket("I was charged twice on my invoice this month.")
    assert result.category == TicketCategory.BILLING
    assert result.assigned_team == SupportTeam.BILLING


def test_technical_routing():
    result = classify_ticket("The API keeps returning an error when I integrate it.")
    assert result.category == TicketCategory.TECHNICAL
    assert result.assigned_team == SupportTeam.TIER2


def test_refund_routing():
    result = classify_ticket("I would like a refund for my last purchase, please.")
    assert result.category == TicketCategory.BILLING
    assert result.subcategory == "refund_request"
```

### 10.6 `tests/test_analysis_fallback.py`

```python
import pytest
from unittest.mock import patch

from app.services import analysis_service


@pytest.mark.asyncio
async def test_fallback_when_ai_raises(session, sample_customer):
    from app.models.ticket import Ticket

    ticket = Ticket(customer_id=sample_customer.customer_id, message="I was charged twice on my invoice.")
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    with patch.object(
        analysis_service, "_call_ai_service", side_effect=Exception("simulated AI failure")
    ):
        result = await analysis_service.analyze_ticket(ticket, sample_customer)

    assert result.source == "rule_based_fallback"
    assert result.category == "billing"
```

> Add `pytest-asyncio==0.24.0` to `requirements.txt` and either mark async tests with `@pytest.mark.asyncio` (as above) or set `asyncio_mode = auto` in a `pytest.ini`:
>
> ```ini
> [pytest]
> asyncio_mode = auto
> ```

### 10.7 Run the suite

```bash
pip install -r requirements.txt   # picks up pytest-asyncio
pytest -v
```

All tests run against `data/test_tickets.db`, created fresh and dropped on every test function — `data/tickets.db` (your real dev data) is never opened during a test run.

---

## Verification Checklist

```bash
# 1. Start the app
uvicorn app.main:app --reload

# 2. Create a ticket
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1001", "message": "I was charged twice this month."}'

# 3. Analyze it (uses rule-based fallback until the AI adapter is implemented)
curl -X POST http://127.0.0.1:8000/tickets/<ticket_id>/analyze

# 4. Escalate it
curl -X POST http://127.0.0.1:8000/tickets/<ticket_id>/escalate \
  -H "Content-Type: application/json" \
  -d '{"reason": "Customer requested manager"}'

# 5. Check history
curl http://127.0.0.1:8000/tickets/<ticket_id>/history

# 6. Run the test suite
pytest -v
```

If all six succeed, the ticket lifecycle (create → analyze → escalate → audit trail) is fully implemented and the AI seam at `app/services/analysis_service.py::_call_ai_service` is ready for your teammate to plug the real model into.
