from app.models.escalation_packet_schemas import EscalationPacket


def test_escalation_packet_schema_contains_required_context():
    packet = EscalationPacket(
        ticket_id="TKT-123",
        customer_summary="Enterprise customer with 4 previous tickets.",
        issue_summary="API authentication fails in production.",
        category="technical",
        priority="high",
        business_impact="Production integration is blocked.",
        steps_already_attempted=["Checked token format"],
        knowledge_articles_checked=["api_authentication_errors.txt"],
        missing_information=["request_id"],
        possible_cause="Expired or revoked token.",
        recommended_team="engineering",
        recommended_next_actions=["Review API logs", "Ask for request ID"],
        internal_note="Escalate if valid token fails across endpoints.",
        customer_reply="Please send the request ID and timestamp with secrets removed.",
    )

    assert packet.ticket_id == "TKT-123"
    assert packet.knowledge_articles_checked == ["api_authentication_errors.txt"]
    assert packet.missing_information == ["request_id"]
