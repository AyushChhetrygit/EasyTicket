from __future__ import annotations

import re
from typing import Any

from app.models.escalation_packet_schemas import EscalationPacket
from app.models.escalation_schemas import EscalationDecision
from app.services.customer_reply_service import generate_customer_reply
from app.services.internal_note_service import generate_internal_note
from app.services.missing_information_service import detect_missing_information
from app.services.rag_search_service import RagSearchResult
from app.services.response_generation_service import RagAnswer, generate_rag_answer


def generate_escalation_packet(
    *,
    ticket: Any,
    customer: Any,
    classification: str,
    priority: str,
    rag_result: RagSearchResult,
    escalation_decision: EscalationDecision,
    rag_answer: RagAnswer | None = None,
) -> EscalationPacket:
    """Generate and validate a structured escalation packet."""
    category = _as_text(classification)
    priority_value = _as_text(priority)
    answer = rag_answer or generate_rag_answer(
        ticket.message,
        _customer_context(customer),
        rag_result,
    )
    missing_information = escalation_decision.missing_information or detect_missing_information(
        ticket.message,
        category,
    )
    possible_cause = _extract_possible_cause(rag_result.passages)
    next_actions = _recommended_next_actions(escalation_decision, missing_information)
    customer_reply = generate_customer_reply(
        rag_answer=answer,
        missing_information=missing_information,
        escalation_decision=escalation_decision,
    )
    internal_note = generate_internal_note(
        ticket=ticket,
        customer=customer,
        category=category,
        priority=priority_value,
        rag_result=rag_result,
        missing_information=missing_information,
        possible_cause=possible_cause,
        recommended_next_actions=next_actions,
    )

    return EscalationPacket(
        ticket_id=ticket.ticket_id,
        customer_summary=_customer_summary(customer),
        issue_summary=ticket.message,
        category=category,
        priority=priority_value,
        business_impact=_business_impact(ticket.message),
        steps_already_attempted=_steps_attempted(ticket.message),
        knowledge_articles_checked=rag_result.sources,
        missing_information=missing_information,
        possible_cause=possible_cause,
        recommended_team=escalation_decision.destination_team,
        recommended_next_actions=next_actions,
        internal_note=internal_note,
        customer_reply=customer_reply,
    )


def _customer_context(customer: Any) -> dict[str, Any]:
    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "plan": customer.plan,
        "account_status": customer.account_status,
        "previous_tickets": customer.previous_tickets,
    }


def _customer_summary(customer: Any) -> str:
    return (
        f"{customer.name} ({customer.customer_id}), {customer.plan} plan, "
        f"{customer.account_status} account, {customer.previous_tickets} previous tickets."
    )


def _extract_possible_cause(passages: list[str]) -> str | None:
    combined = "\n\n".join(passages)
    match = re.search(r"Problem description:\s*(.+?)(?:\n\n[A-Z][A-Za-z ]+:|\Z)", combined, re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _recommended_next_actions(
    decision: EscalationDecision,
    missing_information: list[str],
) -> list[str]:
    if missing_information:
        return [f"Request {field.replace('_', ' ')} from the customer." for field in missing_information]
    if decision.escalation_required:
        return [
            f"Escalate to {decision.destination_team}.",
            "Attach RAG sources and internal note for reviewer context.",
        ]
    return ["Send the customer reply and monitor for follow-up."]


def _business_impact(message: str) -> str | None:
    text = message.lower()
    if "production" in text or "blocked" in text:
        return "Customer reports a blocked production or business workflow."
    if "losing money" in text or "revenue" in text:
        return "Customer reports direct financial impact."
    return None


def _steps_attempted(message: str) -> list[str]:
    text = message.lower()
    attempted = []
    if "refresh" in text:
        attempted.append("Customer tried refreshing.")
    if "sign out" in text or "logged out" in text:
        attempted.append("Customer tried signing out and back in.")
    if "rotated" in text:
        attempted.append("Customer rotated credentials.")
    return attempted


def _as_text(value: Any) -> str:
    return str(getattr(value, "value", value))
