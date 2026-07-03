from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    customer_id: str = Field(primary_key=True, index=True)
    name: str
    plan: str = Field(default="free")          # free / pro / enterprise
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
