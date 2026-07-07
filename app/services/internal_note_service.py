from __future__ import annotations

from typing import Any

from app.services.rag_search_service import RagSearchResult


def generate_internal_note(
    *,
    ticket: Any,
    customer: Any,
    category: str,
    priority: str,
    rag_result: RagSearchResult,
    missing_information: list[str],
    possible_cause: str | None,
    recommended_next_actions: list[str],
) -> str:
    """Generate an agent-facing technical summary."""
    parts = [
        f"Ticket {ticket.ticket_id} from customer {customer.customer_id}.",
        (
            f"Customer context: name={customer.name}, plan={customer.plan}, "
            f"account_status={customer.account_status}, previous_tickets={customer.previous_tickets}."
        ),
        f"Issue category: {category}. Priority: {priority}.",
        f"Customer message: {ticket.message}",
        f"RAG sources checked: {_format_list(rag_result.sources)}.",
        f"Retrieval confidence: {rag_result.confidence}.",
        f"Missing information: {_format_list(missing_information)}.",
        f"Possible cause: {possible_cause or 'Not enough evidence yet.'}",
        f"Recommended next actions: {_format_list(recommended_next_actions)}.",
    ]
    return "\n".join(parts)


def _format_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)
