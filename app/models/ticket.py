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


class TicketEscalateRequest(SQLModel):
    reason: str
    team: Optional[SupportTeam] = None
