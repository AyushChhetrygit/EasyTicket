"""Deterministic mock AI responses for local development and tests."""

from __future__ import annotations

from typing import Any, Literal

from app.models.ai_schemas import PriorityResult, RoutingResult, TicketAnalysisResult

MockFailureMode = Literal["none", "fail", "invalid_json"]


class MockAIError(Exception):
    """Raised for controlled mock AI failures."""


class MockAIService:
    """Offline AI substitute with deterministic outputs."""

    def __init__(self, failure_mode: MockFailureMode = "none") -> None:
        self.failure_mode = failure_mode

    def invalid_json_response(self) -> str:
        return "{not valid json"

    def classify_ticket(
        self,
        ticket_message: str,
        customer_info: dict[str, Any] | None = None,
    ) -> TicketAnalysisResult:
        self._maybe_fail()
        message = ticket_message.lower()
        if any(term in message for term in ("payment", "invoice", "subscription", "charged")):
            return TicketAnalysisResult(
                category="billing",
                subcategory="subscription_activation",
                classification_confidence=0.92,
                priority="P1",
                assigned_team="Billing Support",
                reason="The ticket describes a billing or subscription issue.",
            )
        if "refund" in message:
            return TicketAnalysisResult(
                category="refund",
                subcategory="refund_request",
                classification_confidence=0.88,
                priority="P2",
                assigned_team="Billing Support",
                reason="The customer is requesting or considering a refund.",
            )
        if any(term in message for term in ("login", "access", "account")):
            return TicketAnalysisResult(
                category="account",
                subcategory="account_access",
                classification_confidence=0.84,
                priority="P2",
                assigned_team="Account Support",
                reason="The ticket appears related to account access or account state.",
            )
        if any(term in message for term in ("feature", "request", "add")):
            return TicketAnalysisResult(
                category="feature_request",
                subcategory="product_feedback",
                classification_confidence=0.8,
                priority="P4",
                assigned_team="Product Team",
                reason="The ticket asks for product capability changes.",
            )
        return TicketAnalysisResult(
            category="technical",
            subcategory="general_support",
            classification_confidence=0.65,
            priority="P3",
            assigned_team="Technical Support",
            reason="The ticket needs technical triage but lacks a more specific signal.",
        )

    def estimate_priority(
        self,
        ticket_message: str,
        customer_info: dict[str, Any] | None = None,
    ) -> PriorityResult:
        self._maybe_fail()
        message = ticket_message.lower()
        plan = str((customer_info or {}).get("plan", "")).lower()
        if any(term in message for term in ("all users", "complete outage", "system down", "service down")):
            return PriorityResult(priority="P0", reason="A complete outage is reported.")
        if any(term in message for term in ("security", "data leak", "breach")):
            return PriorityResult(priority="P0", reason="Security impact requires immediate handling.")
        if any(term in message for term in ("payment", "charged", "deducted", "invoice")):
            return PriorityResult(priority="P1", reason="Financial impact requires urgent support.")
        if ("enterprise" in plan and any(term in message for term in ("cannot access", "blocked", "login"))) or "business-critical" in message:
            return PriorityResult(priority="P1", reason="Business-critical access is blocked.")
        if any(term in message for term in ("workaround", "alternative", "csv download")):
            return PriorityResult(priority="P2", reason="Impact exists but a workaround is available.")
        if any(term in message for term in ("feature", "nice to have", "request")):
            return PriorityResult(priority="P4", reason="Low-impact feature request.")
        return PriorityResult(priority="P3", reason="Normal issue with limited immediate impact.")

    def route_ticket(
        self,
        category: str,
        subcategory: str,
        priority: str,
    ) -> RoutingResult:
        self._maybe_fail()
        severe = priority == "P0" or (priority == "P1" and category == "technical") or "outage" in subcategory.lower()
        if severe:
            return RoutingResult(assigned_team="Engineering", reason="Severe bugs and outages require Engineering ownership.")
        if category in ("billing", "refund"):
            return RoutingResult(assigned_team="Billing Support", reason="Billing and refund issues route to Billing Support.")
        if category == "account":
            return RoutingResult(assigned_team="Account Support", reason="Account issues route to Account Support.")
        if category == "feature_request":
            return RoutingResult(assigned_team="Product Team", reason="Feature requests route to Product Team.")
        return RoutingResult(assigned_team="Technical Support", reason="Normal technical issues route to Technical Support.")

    def _maybe_fail(self) -> None:
        if self.failure_mode == "fail":
            raise MockAIError("Artificial mock AI failure.")
        if self.failure_mode == "invalid_json":
            raise MockAIError(self.invalid_json_response())
