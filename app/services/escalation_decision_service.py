from __future__ import annotations

import re
from typing import Any

from app.models.escalation_schemas import EscalationDecision
from app.models.enums import SupportTeam

LOW_CONFIDENCE_THRESHOLD = 0.65
REFUND_APPROVAL_LIMIT = 100.0

SECURITY_TERMS = ("security", "breach", "compromise", "data leak", "unauthorized")
DATA_LOSS_TERMS = ("data loss", "lost data", "missing workspace", "deleted project")
DELETE_TERMS = ("delete account", "account deletion", "close my account")
CANCEL_TERMS = ("cancel subscription", "subscription cancellation", "cancel my plan")
NEGATIVE_TERMS = ("angry", "furious", "upset", "unacceptable", "terrible", "frustrated")


def decide_escalation(
    *,
    ticket_message: str,
    category: str | None = None,
    priority: str | None = None,
    assigned_team: str | None = None,
    retrieval_confidence: float = 0.0,
    customer_context: dict[str, Any] | None = None,
    missing_information: list[str] | None = None,
    refund_amount: float | None = None,
) -> EscalationDecision:
    text = ticket_message.lower()
    customer = customer_context or {}
    missing = missing_information or []
    score = 0.0
    reasons: list[str] = []

    if retrieval_confidence < LOW_CONFIDENCE_THRESHOLD:
        score += 0.25
        reasons.append("retrieval confidence is below 0.65")

    priority_value = _normalize_priority(priority)
    if priority_value == "P0":
        score += 0.45
        reasons.append("priority is P0")
    elif priority_value == "P1":
        score += 0.35
        reasons.append("priority is P1")

    is_refund = category == "refund" or "refund" in text
    amount = refund_amount if refund_amount is not None else _extract_money_amount(text)
    if is_refund:
        score += 0.15
        reasons.append("ticket mentions a refund request")
        if amount is not None and amount > REFUND_APPROVAL_LIMIT:
            score += 0.25
            reasons.append("refund amount is above approval limit")

    sensitive_action = any(term in text for term in DELETE_TERMS + CANCEL_TERMS + SECURITY_TERMS + DATA_LOSS_TERMS)
    if any(term in text for term in DELETE_TERMS):
        score += 0.25
        reasons.append("account deletion is sensitive")
    if any(term in text for term in CANCEL_TERMS):
        score += 0.2
        reasons.append("subscription cancellation is sensitive")
    if any(term in text for term in SECURITY_TERMS):
        score += 0.35
        reasons.append("security incident requires human review")
    if any(term in text for term in DATA_LOSS_TERMS):
        score += 0.35
        reasons.append("data-loss claim requires human review")

    if str(customer.get("plan", "")).lower() == "enterprise":
        score += 0.15
        reasons.append("customer is on an enterprise plan")

    previous_tickets = int(customer.get("previous_tickets") or 0)
    if previous_tickets >= 3:
        score += 0.1
        reasons.append("customer has repeated support attempts")

    if any(term in text for term in NEGATIVE_TERMS):
        score += 0.1
        reasons.append("negative customer sentiment detected")

    if missing:
        score += min(0.2, 0.05 * len(missing))
        reasons.append("required information is missing")

    normalized_score = round(min(score, 1.0), 2)
    destination_team = _destination_team(assigned_team, category, text)
    human_approval_required = sensitive_action or (is_refund and amount is not None and amount > REFUND_APPROVAL_LIMIT)

    if missing:
        action = "request_information"
        escalation_required = False
    elif priority_value in {"P0", "P1"} or retrieval_confidence < LOW_CONFIDENCE_THRESHOLD or normalized_score >= 0.65:
        action = "escalate_to_human"
        escalation_required = True
    else:
        action = "suggest_resolution"
        escalation_required = False

    if human_approval_required and action == "suggest_resolution":
        action = "escalate_to_human"
        escalation_required = True

    reason = "; ".join(reasons) if reasons else "RAG confidence and ticket signals allow a suggested resolution."
    return EscalationDecision(
        action=action,
        escalation_required=escalation_required,
        escalation_score=normalized_score,
        human_approval_required=human_approval_required,
        sensitive_action=sensitive_action,
        destination_team=destination_team,
        reason=reason,
        missing_information=missing,
    )


def _normalize_priority(priority: str | None) -> str:
    value = str(priority or "").lower()
    if value in {"p0", "urgent"}:
        return "P0"
    if value in {"p1", "high"}:
        return "P1"
    if value in {"p2", "medium"}:
        return "P2"
    return "P3"


def _destination_team(assigned_team: str | None, category: str | None, text: str) -> str:
    if assigned_team:
        return str(assigned_team)
    if any(term in text for term in SECURITY_TERMS + DATA_LOSS_TERMS):
        return SupportTeam.ENGINEERING.value
    if category in {"billing", "refund"} or "refund" in text:
        return SupportTeam.BILLING.value
    if category == "account" or any(term in text for term in DELETE_TERMS + CANCEL_TERMS):
        return SupportTeam.TIER1.value
    return SupportTeam.TIER2.value


def _extract_money_amount(text: str) -> float | None:
    match = re.search(r"(?:\$|usd\s*)(\d+(?:\.\d{1,2})?)", text)
    if not match:
        return None
    return float(match.group(1))
