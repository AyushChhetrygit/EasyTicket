from __future__ import annotations

from app.models.escalation_schemas import EscalationDecision
from app.services.response_generation_service import RagAnswer


def generate_customer_reply(
    *,
    rag_answer: RagAnswer,
    missing_information: list[str],
    escalation_decision: EscalationDecision,
) -> str:
    """Generate a short customer-facing response without internal reasoning."""
    if missing_information:
        requested = ", ".join(_humanize(field) for field in missing_information)
        return (
            "Thanks for reaching out. To help us review this quickly, "
            f"please share: {requested}. Once we have that, we can continue investigating."
        )

    if escalation_decision.escalation_required:
        return (
            "Thanks for sharing the details. This needs a support specialist to review it, "
            "so we are escalating it to the right team and will follow up with the next update."
        )

    return rag_answer.answer


def _humanize(field: str) -> str:
    return field.replace("_", " ")
