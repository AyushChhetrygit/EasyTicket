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
                 # "escalated", "ai_analysis", "category_changed"
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
