from app.services.rule_based_router import classify_ticket
from app.models.enums import TicketCategory, SupportTeam


def test_billing_routing():
    result = classify_ticket("I was charged twice on my invoice this month.")
    assert result.category == TicketCategory.BILLING
    assert result.assigned_team == SupportTeam.BILLING


def test_technical_routing():
    result = classify_ticket("The API keeps returning an error when I integrate it.")
    assert result.category == TicketCategory.TECHNICAL
    assert result.assigned_team == SupportTeam.TIER2


def test_refund_routing():
    result = classify_ticket("I would like a refund for my last purchase, please.")
    assert result.category == TicketCategory.BILLING
    assert result.subcategory == "refund_request"
