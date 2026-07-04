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
    customer_id: Optional[str] = None,
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
    if customer_id:
        query = query.where(Ticket.customer_id == customer_id)

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
            history_service.record_team_assignment(
                session, ticket_id, str(old_value) if old_value else None, str(value), performed_by
            )
        elif field == "priority":
            history_service.record_priority_change(
                session, ticket_id, str(old_value) if old_value else None, str(value), performed_by
            )

        setattr(ticket, field, value)

    ticket.updated_at = datetime.now(timezone.utc)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def escalate_ticket(
    session: Session,
    ticket_id: str,
    reason: str,
    team: Optional[str] = None,
    performed_by: str = "user",
) -> Ticket:
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
