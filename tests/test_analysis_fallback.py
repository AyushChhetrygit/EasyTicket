import pytest
from unittest.mock import patch

from app.services import analysis_service


@pytest.mark.asyncio
async def test_fallback_when_ai_raises(session, sample_customer):
    from app.models.ticket import Ticket

    ticket = Ticket(customer_id=sample_customer.customer_id, message="I was charged twice on my invoice.")
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    with patch.object(
        analysis_service, "_call_ai_service", side_effect=Exception("simulated AI failure")
    ):
        result = await analysis_service.analyze_ticket(ticket, sample_customer)

    assert result.source == "rule_based_fallback"
    assert result.category == "billing"
