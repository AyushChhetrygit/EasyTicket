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
from app.services import ticket_service, history_service, analysis_service
from app.services.customer_service import CustomerNotFoundError, get_customer_by_id
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
    customer_id: Optional[str] = None,
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
        customer_id=customer_id,
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
    # Confirm the ticket exists so an unknown ticket_id returns 404, not an empty list
    try:
        ticket_service.get_ticket_by_id(session, ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return history_service.get_ticket_history(session, ticket_id)


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
        history_service.log_event(
            session, ticket_id, "category_changed",
            str(old_category), str(ticket.category), performed_by,
        )
    if old_priority != ticket.priority:
        history_service.record_priority_change(
            session, ticket_id,
            str(old_priority) if old_priority else None,
            str(ticket.priority), performed_by,
        )
    if old_team != ticket.assigned_team:
        history_service.record_team_assignment(
            session, ticket_id,
            str(old_team) if old_team else None,
            str(ticket.assigned_team), performed_by,
        )
    history_service.record_ai_analysis(session, ticket_id, result.reason, performed_by=result.source)

    return ticket
