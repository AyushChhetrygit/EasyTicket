from app.models.customer import Customer
from app.models.enums import SupportTeam
from app.models.ticket import Ticket
from app.services.customer_reply_service import generate_customer_reply
from app.services.escalation_decision_service import decide_escalation
from app.services.escalation_packet_service import generate_escalation_packet
from app.services.internal_note_service import generate_internal_note
from app.services.rag_search_service import search_knowledge_base
from app.services.response_generation_service import RagAnswer


def test_internal_note_contains_agent_context():
    ticket = Ticket(customer_id="CUST-1", message="API returns 401 in production.")
    customer = Customer(customer_id="CUST-1", name="Ava", plan="enterprise", previous_tickets=3)
    rag_result = search_knowledge_base("api returns 401 unauthorized")

    note = generate_internal_note(
        ticket=ticket,
        customer=customer,
        category="technical",
        priority="high",
        rag_result=rag_result,
        missing_information=["request_id"],
        possible_cause="Invalid API key.",
        recommended_next_actions=["Ask for request ID."],
    )

    assert ticket.ticket_id in note
    assert "previous_tickets=3" in note
    assert "api_authentication_errors.txt" in note
    assert "request_id" in note


def test_customer_reply_asks_for_missing_information():
    decision = decide_escalation(
        ticket_message="My invoice is wrong.",
        category="billing",
        priority="medium",
        retrieval_confidence=0.8,
        missing_information=["invoice_id"],
    )
    reply = generate_customer_reply(
        rag_answer=RagAnswer("Use this answer.", ["invoice_not_generated.txt"], 0.8, False),
        missing_information=["invoice_id"],
        escalation_decision=decision,
    )

    assert "invoice id" in reply.lower()
    assert "score" not in reply.lower()


def test_customer_reply_mentions_escalation_when_required():
    decision = decide_escalation(
        ticket_message="Production is blocked.",
        priority="P0",
        retrieval_confidence=0.9,
    )
    reply = generate_customer_reply(
        rag_answer=RagAnswer("Use this answer.", [], 0.9, False),
        missing_information=[],
        escalation_decision=decision,
    )

    assert "escalating" in reply.lower()


def test_escalation_packet_is_validated_and_includes_sources():
    ticket = Ticket(
        customer_id="CUST-1",
        message="API returns 401 unauthorized in production for workspace WS-123 in Chrome.",
        assigned_team=SupportTeam.ENGINEERING,
    )
    customer = Customer(customer_id="CUST-1", name="Ava", plan="enterprise", previous_tickets=2)
    rag_result = search_knowledge_base(ticket.message)
    decision = decide_escalation(
        ticket_message=ticket.message,
        category="technical",
        priority="high",
        assigned_team="engineering",
        retrieval_confidence=rag_result.confidence,
        customer_context={"plan": customer.plan, "previous_tickets": customer.previous_tickets},
    )

    packet = generate_escalation_packet(
        ticket=ticket,
        customer=customer,
        classification="technical",
        priority="high",
        rag_result=rag_result,
        escalation_decision=decision,
    )

    assert packet.ticket_id == ticket.ticket_id
    assert "api_authentication_errors.txt" in packet.knowledge_articles_checked
    assert packet.recommended_team == "engineering"
    assert packet.internal_note
    assert packet.customer_reply
