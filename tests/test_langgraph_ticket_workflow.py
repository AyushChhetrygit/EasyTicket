from app.workflows.langgraph_ticket_workflow import build_ticket_workflow


def test_langgraph_workflow_compiles():
    workflow = build_ticket_workflow()

    assert workflow is not None


def test_subscription_ticket_routes_to_ask_information():
    workflow = build_ticket_workflow()

    result = workflow.invoke({
        "ticket": {
            "ticket_id": "TKT-LG-1",
            "customer_id": "CUST-1",
            "message": "I paid for Pro but my subscription is still inactive.",
        },
        "customer_context": {
            "customer_id": "CUST-1",
            "name": "Demo User",
            "plan": "pro",
            "previous_tickets": 0,
        },
    })

    assert result["classification"] == "billing"
    assert "subscription_activation.txt" in [
        doc["source"] for doc in result["retrieved_documents"]
    ]
    assert result["final_action"] == "ask_information"
    assert result["missing_information"]


def test_high_risk_security_ticket_routes_to_human_approval():
    workflow = build_ticket_workflow()

    result = workflow.invoke({
        "ticket": {
            "ticket_id": "TKT-LG-2",
            "customer_id": "CUST-ENT",
            "message": (
                "Security breach in production with API 401 for workspace WS-123 "
                "in Chrome after I rotate credentials."
            ),
        },
        "customer_context": {
            "customer_id": "CUST-ENT",
            "name": "Enterprise User",
            "plan": "enterprise",
            "previous_tickets": 3,
        },
    })

    assert result["final_action"] == "human_approval_required"
    assert result["escalation_required"] is True
    assert result["escalation_packet"]["recommended_team"] == "engineering"


def test_unrelated_ticket_uses_failure_path_after_retry():
    workflow = build_ticket_workflow()

    result = workflow.invoke({
        "ticket": {
            "ticket_id": "TKT-LG-3",
            "customer_id": "CUST-1",
            "message": "How do I bake sourdough bread?",
        },
        "customer_context": {"customer_id": "CUST-1", "name": "Demo User"},
    })

    assert result["final_action"] == "failure"
    assert result["retry_count"] == 1
    assert result["verification_passed"] is False
