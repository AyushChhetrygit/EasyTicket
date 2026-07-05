import asyncio
from dataclasses import dataclass
from typing import Literal, Optional

from app.models.customer import Customer
from app.models.enums import SupportTeam, TicketCategory, TicketPriority
from app.models.ticket import Ticket
from app.services.rule_based_router import classify_ticket, RuleBasedResult
from app.workflows.ticket_analysis_workflow import analyze_ticket as run_ai_workflow

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
    customer_payload = {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "plan": customer.plan,
        "account_status": customer.account_status,
        "previous_tickets": customer.previous_tickets,
    }
    ai_result = await run_ai_workflow(
        {"ticket_id": ticket.ticket_id, "message": ticket.message},
        customer_payload,
    )
    return AnalysisResult(
        category=_map_category(ai_result.category).value,
        subcategory=ai_result.subcategory,
        priority=_map_priority(ai_result.priority).value,
        assigned_team=_map_team(ai_result.assigned_team).value,
        reason=ai_result.reason,
        confidence=ai_result.classification_confidence,
        source="ai",
    )


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


def _map_category(category: str) -> TicketCategory:
    if category == "refund":
        return TicketCategory.BILLING
    try:
        return TicketCategory(category)
    except ValueError as error:
        raise InvalidAIOutputError(f"invalid category: {category}") from error


def _map_priority(priority: str) -> TicketPriority:
    mapping = {
        "P0": TicketPriority.URGENT,
        "P1": TicketPriority.HIGH,
        "P2": TicketPriority.MEDIUM,
        "P3": TicketPriority.LOW,
        "P4": TicketPriority.LOW,
    }
    try:
        return mapping[priority]
    except KeyError as error:
        raise InvalidAIOutputError(f"invalid priority: {priority}") from error


def _map_team(team: str) -> SupportTeam:
    mapping = {
        "Billing Support": SupportTeam.BILLING,
        "Technical Support": SupportTeam.TIER2,
        "Account Support": SupportTeam.TIER1,
        "Engineering": SupportTeam.ENGINEERING,
        "Product Team": SupportTeam.ACCOUNT_MANAGEMENT,
    }
    try:
        return mapping[team]
    except KeyError as error:
        raise InvalidAIOutputError(f"invalid team: {team}") from error


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

    except (InvalidAIOutputError, Exception):
        # Broad except is intentional: any failure in the AI path (network error,
        # bad JSON, unexpected exception) degrades to rule-based rather than a 500.
        # Log this in production rather than silently swallowing it.
        fallback = classify_ticket(ticket.message)
        return _rule_result_to_analysis(fallback)
