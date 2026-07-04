from unittest.mock import patch

from app.services import analysis_service


def test_create_ticket(client, sample_customer):
    response = client.post("/tickets", json={
        "customer_id": sample_customer.customer_id,
        "message": "I can't log into my account.",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"
    assert body["ticket_id"].startswith("TKT-")


def test_create_ticket_invalid_customer(client):
    response = client.post("/tickets", json={
        "customer_id": "CUST-NOPE",
        "message": "Test message",
    })
    assert response.status_code == 404


def test_list_tickets(client, sample_customer):
    client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket A"})
    client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket B"})

    response = client.get("/tickets")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_ticket(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.get(f"/tickets/{created['ticket_id']}")
    assert response.status_code == 200
    assert response.json()["ticket_id"] == created["ticket_id"]


def test_get_ticket_not_found(client):
    response = client.get("/tickets/TKT-DOESNOTEXIST")
    assert response.status_code == 404


def test_update_ticket(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.patch(f"/tickets/{created['ticket_id']}", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_ticket_invalid_status(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.patch(f"/tickets/{created['ticket_id']}", json={"status": "not_a_real_status"})
    assert response.status_code == 422


def test_manual_escalation(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()

    response = client.post(f"/tickets/{created['ticket_id']}/escalate", json={"reason": "Customer very upset"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "escalated"
    assert body["assigned_team"] == "engineering"  # default when no team supplied


def test_ticket_history(client, sample_customer):
    created = client.post("/tickets", json={"customer_id": sample_customer.customer_id, "message": "Ticket"}).json()
    client.patch(f"/tickets/{created['ticket_id']}", json={"status": "in_progress"})

    response = client.get(f"/tickets/{created['ticket_id']}/history")
    assert response.status_code == 200
    actions = [entry["action"] for entry in response.json()]
    assert "created" in actions
    assert "status_changed" in actions


def test_create_ticket_then_analyze_uses_ai_workflow(client, sample_customer):
    created = client.post("/tickets", json={
        "customer_id": sample_customer.customer_id,
        "message": "I was charged twice on my invoice this month.",
    }).json()

    response = client.post(f"/tickets/{created['ticket_id']}/analyze")
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "billing"
    assert body["priority"] == "high"
    assert body["assigned_team"] == "billing_team"
    assert body["classification_confidence"] is not None
    assert body["ai_reason"] is not None
    assert body["analysis_source"] == "ai"

    saved = client.get(f"/tickets/{created['ticket_id']}").json()
    assert saved["category"] == body["category"]
    assert saved["priority"] == body["priority"]
    assert saved["assigned_team"] == body["assigned_team"]


def test_analyze_ticket_not_found(client):
    """/analyze on a non-existent ticket should return 404."""
    response = client.post("/tickets/TKT-GHOST/analyze")
    assert response.status_code == 404


def test_analyze_ticket_writes_history(client, sample_customer):
    """After /analyze, the audit trail should contain an ai_analysis entry."""
    created = client.post("/tickets", json={
        "customer_id": sample_customer.customer_id,
        "message": "The API returns a 500 error when I call the integration endpoint.",
    }).json()

    client.post(f"/tickets/{created['ticket_id']}/analyze")

    history_resp = client.get(f"/tickets/{created['ticket_id']}/history")
    actions = [e["action"] for e in history_resp.json()]
    assert "ai_analysis" in actions


def test_analyze_endpoint_falls_back_when_ai_fails(client, sample_customer):
    created = client.post("/tickets", json={
        "customer_id": sample_customer.customer_id,
        "message": "The API returns a crash during integration sync.",
    }).json()

    with patch.object(
        analysis_service, "_call_ai_service", side_effect=Exception("simulated AI failure")
    ):
        response = client.post(f"/tickets/{created['ticket_id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_source"] == "rule_based_fallback"
    assert body["category"] == "technical"
    assert body["assigned_team"] == "tier2_support"
