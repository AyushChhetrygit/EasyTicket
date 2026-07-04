from dataclasses import dataclass
from typing import Optional

from app.models.enums import TicketCategory, TicketPriority, SupportTeam

# --- Keyword banks ---

BILLING_KEYWORDS = ["payment", "charged", "invoice", "subscription"]
REFUND_KEYWORDS = ["refund", "money back", "cancel purchase"]
TECHNICAL_KEYWORDS = ["api", "error", "crash", "integration"]
ACCOUNT_KEYWORDS = ["login", "password", "locked", "account"]
FEATURE_REQUEST_KEYWORDS = ["feature", "enhancement", "support for", "would like"]
OUTAGE_KEYWORDS = ["entire service down", "everyone cannot access", "complete outage"]


@dataclass
class RuleBasedResult:
    category: TicketCategory
    subcategory: Optional[str]
    priority: TicketPriority
    assigned_team: SupportTeam
    reason: str
    confidence: float


def _matches(text: str, keywords: list[str]) -> Optional[str]:
    """Return the first matching keyword, or None."""
    for kw in keywords:
        if kw in text:
            return kw
    return None


def classify_ticket(message: str) -> RuleBasedResult:
    text = message.lower()

    # Outage takes priority over everything else — highest urgency, widest impact
    if hit := _matches(text, OUTAGE_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.TECHNICAL,
            subcategory="outage",
            priority=TicketPriority.URGENT,
            assigned_team=SupportTeam.ENGINEERING,
            reason=f"Matched outage keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, REFUND_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.BILLING,
            subcategory="refund_request",
            priority=TicketPriority.HIGH,
            assigned_team=SupportTeam.BILLING,
            reason=f"Matched refund keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, BILLING_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.BILLING,
            subcategory=None,
            priority=TicketPriority.MEDIUM,
            assigned_team=SupportTeam.BILLING,
            reason=f"Matched billing keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, TECHNICAL_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.TECHNICAL,
            subcategory=None,
            priority=TicketPriority.MEDIUM,
            assigned_team=SupportTeam.TIER2,
            reason=f"Matched technical keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, ACCOUNT_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.ACCOUNT,
            subcategory=None,
            priority=TicketPriority.LOW,
            assigned_team=SupportTeam.TIER1,
            reason=f"Matched account keyword: '{hit}'.",
            confidence=0.6,
        )

    if hit := _matches(text, FEATURE_REQUEST_KEYWORDS):
        return RuleBasedResult(
            category=TicketCategory.FEATURE_REQUEST,
            subcategory=None,
            priority=TicketPriority.LOW,
            assigned_team=SupportTeam.ACCOUNT_MANAGEMENT,
            reason=f"Matched feature-request keyword: '{hit}'.",
            confidence=0.6,
        )

    # No keyword matched — generic default, low confidence
    return RuleBasedResult(
        category=TicketCategory.GENERAL,
        subcategory=None,
        priority=TicketPriority.LOW,
        assigned_team=SupportTeam.TIER1,
        reason="No keyword rule matched; defaulted to general/tier1.",
        confidence=0.3,
    )
