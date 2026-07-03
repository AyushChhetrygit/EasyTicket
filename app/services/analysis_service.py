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
        # Broad except is intentional: any failure in the AI path (network error,
        # bad JSON, unexpected exception) degrades to rule-based rather than a 500.
        # Log this in production rather than silently swallowing it.
        fallback = classify_ticket(ticket.message)
        return _rule_result_to_analysis(fallback)
