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


def record_status_change(
    session: Session, ticket_id: str, old_status: str, new_status: str, performed_by: str = "system"
) -> TicketHistory:
    return log_event(
        session, ticket_id, action="status_changed",
        old_value=old_status, new_value=new_status, performed_by=performed_by,
    )


def record_team_assignment(
    session: Session, ticket_id: str, old_team: Optional[str], new_team: str, performed_by: str = "system"
) -> TicketHistory:
    return log_event(
        session, ticket_id, action="team_assigned",
        old_value=old_team, new_value=new_team, performed_by=performed_by,
    )


def record_priority_change(
    session: Session, ticket_id: str, old_priority: Optional[str], new_priority: str, performed_by: str = "system"
) -> TicketHistory:
    return log_event(
        session, ticket_id, action="priority_changed",
        old_value=old_priority, new_value=new_priority, performed_by=performed_by,
    )


def record_manual_escalation(
    session: Session, ticket_id: str, reason: str, performed_by: str = "user"
) -> TicketHistory:
    return log_event(session, ticket_id, action="escalated", new_value=reason, performed_by=performed_by)


def record_ai_analysis(
    session: Session, ticket_id: str, summary: str, performed_by: str = "ai"
) -> TicketHistory:
    return log_event(session, ticket_id, action="ai_analysis", new_value=summary, performed_by=performed_by)


def get_ticket_history(session: Session, ticket_id: str) -> List[TicketHistory]:
    query = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at)
    )
    return list(session.exec(query))
