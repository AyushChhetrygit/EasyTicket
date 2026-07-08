from app.services.escalation_decision_service import decide_escalation


def test_p0_priority_escalates_to_human():
    decision = decide_escalation(
        ticket_message="The entire service is down.",
        priority="P0",
        retrieval_confidence=0.9,
    )

    assert decision.action == "escalate_to_human"
    assert decision.escalation_required is True
    assert "priority is P0" in decision.reason


def test_low_retrieval_confidence_escalates():
    decision = decide_escalation(
        ticket_message="Something unusual is happening.",
        priority="medium",
        retrieval_confidence=0.4,
    )

    assert decision.action == "escalate_to_human"
    assert decision.escalation_score >= 0.25


def test_missing_information_requests_information_first():
    decision = decide_escalation(
        ticket_message="My invoice is wrong.",
        priority="medium",
        retrieval_confidence=0.8,
        missing_information=["invoice_number", "billing_email"],
    )

    assert decision.action == "request_information"
    assert decision.escalation_required is False
    assert decision.missing_information == ["invoice_number", "billing_email"]


def test_high_value_refund_requires_human_approval():
    decision = decide_escalation(
        ticket_message="I want a refund of $250.",
        category="refund",
        priority="medium",
        retrieval_confidence=0.9,
    )

    assert decision.action == "escalate_to_human"
    assert decision.human_approval_required is True
    assert decision.destination_team == "billing_team"


def test_sensitive_account_deletion_requires_human_approval():
    decision = decide_escalation(
        ticket_message="Please delete account permanently.",
        category="account",
        priority="low",
        retrieval_confidence=0.9,
    )

    assert decision.action == "escalate_to_human"
    assert decision.sensitive_action is True
    assert decision.human_approval_required is True


def test_security_incident_routes_to_engineering():
    decision = decide_escalation(
        ticket_message="We suspect a security breach and data leak.",
        priority="medium",
        retrieval_confidence=0.9,
    )

    assert decision.action == "escalate_to_human"
    assert decision.destination_team == "engineering"


def test_enterprise_repeated_negative_ticket_increases_score():
    decision = decide_escalation(
        ticket_message="I am frustrated that this keeps failing.",
        priority="medium",
        retrieval_confidence=0.9,
        customer_context={"plan": "enterprise", "previous_tickets": 4},
    )

    assert decision.escalation_score == 0.35
    assert decision.action == "suggest_resolution"


def test_normal_case_suggests_resolution():
    decision = decide_escalation(
        ticket_message="How do I reset my password?",
        category="account",
        priority="low",
        retrieval_confidence=0.9,
    )

    assert decision.action == "suggest_resolution"
    assert decision.escalation_required is False
    assert decision.human_approval_required is False
