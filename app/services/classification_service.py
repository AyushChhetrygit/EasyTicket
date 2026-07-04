"""Ticket classification service backed by Gemini or deterministic mocks."""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.models.ai_schemas import TicketAnalysisResult
from config.llm_config import LLMConfig, get_llm_config


class ClassificationError(Exception):
    """Raised when ticket classification cannot produce valid structured output."""


class TicketClassificationService:
    """Analyze support tickets into category, priority, routing, and reasoning."""

    def __init__(
        self,
        client: genai.Client | None = None,
        config: LLMConfig | None = None,
    ) -> None:
        self.config = config or get_llm_config()
        self.client = client

    def analyze_ticket(
        self,
        ticket_message: str,
        customer_info: dict[str, Any] | None = None,
    ) -> TicketAnalysisResult:
        message = ticket_message.strip()
        if not message:
            raise ClassificationError("Ticket message cannot be empty.")

        if self.config.mock_ai_mode:
            return self._mock_analysis(message)

        client = self.client or self._build_client()
        payload = {"message": message}
        if customer_info:
            payload["customer"] = customer_info

        last_error: Exception | None = None
        for _ in range(2):
            try:
                response_text = self._generate_live_response(client, payload)
                return self._parse_response(response_text)
            except (ValidationError, json.JSONDecodeError, ClassificationError) as error:
                last_error = error

        raise ClassificationError(
            f"AI classification validation failed after retry: {last_error}"
        )

    def _build_client(self) -> genai.Client:
        api_key = self.config.gemini_api_key
        if api_key is None:
            raise ClassificationError("GEMINI_API_KEY is required for live AI mode.")
        return genai.Client(api_key=api_key.get_secret_value())

    def _generate_live_response(
        self,
        client: genai.Client,
        payload: dict[str, Any],
    ) -> str:
        response = client.models.generate_content(
            model=self.config.gemini_model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=f"{self._system_prompt()}\n\nInput:\n{json.dumps(payload)}"
                        )
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=512,
                http_options=types.HttpOptions(
                    timeout=int(self.config.ai_request_timeout_seconds * 1000)
                ),
            ),
        )

        if not response.text:
            raise ClassificationError("Gemini returned an empty classification response.")
        return response.text

    def _parse_response(self, response_text: str) -> TicketAnalysisResult:
        return TicketAnalysisResult.model_validate(json.loads(response_text))

    def _mock_analysis(self, message: str) -> TicketAnalysisResult:
        normalized = message.lower()

        if any(term in normalized for term in ("payment", "invoice", "subscription")):
            return TicketAnalysisResult(
                category="billing",
                subcategory="subscription_activation",
                classification_confidence=0.92,
                priority="P1",
                assigned_team="Billing Support",
                reason="The ticket describes a billing or subscription issue.",
            )

        if "refund" in normalized:
            return TicketAnalysisResult(
                category="refund",
                subcategory="refund_request",
                classification_confidence=0.88,
                priority="P2",
                assigned_team="Billing Support",
                reason="The customer is requesting or considering a refund.",
            )

        if any(term in normalized for term in ("login", "access", "account")):
            return TicketAnalysisResult(
                category="account",
                subcategory="account_access",
                classification_confidence=0.84,
                priority="P2",
                assigned_team="Account Management",
                reason="The ticket appears related to account access or account state.",
            )

        if any(term in normalized for term in ("feature", "request", "add")):
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

    def _system_prompt(self) -> str:
        return (
            "You are an expert ticket triage AI. Return strict JSON only. "
            "Schema fields: category, subcategory, classification_confidence, "
            "priority, assigned_team, reason. "
            "Allowed categories: account, billing, technical, refund, feature_request. "
            "Allowed priorities: P0, P1, P2, P3, P4. "
            "Allowed teams: Billing Support, Technical Support, Account Management, "
            "Product Team. "
            "Use concise, engineering-ready reasons."
        )
