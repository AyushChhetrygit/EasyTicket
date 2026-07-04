"""Ticket classification service backed by Gemini or deterministic mocks."""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.agents.prompts.classification_prompt import CLASSIFICATION_SYSTEM_PROMPT
from app.models.ai_schemas import TicketAnalysisResult
from app.services.mock_ai_service import MockAIService
from config.llm_config import LLMConfig, get_llm_config


class ClassificationError(Exception):
    """Raised when ticket classification cannot produce valid structured output."""


class TicketClassificationService:
    """Analyze support tickets into category, priority, routing, and reasoning."""

    def __init__(
        self,
        client: genai.Client | None = None,
        config: LLMConfig | None = None,
        mock_ai_service: MockAIService | None = None,
    ) -> None:
        self.config = config or get_llm_config()
        self.client = client
        self.mock_ai_service = mock_ai_service or MockAIService()

    def analyze_ticket(
        self,
        ticket_message: str,
        customer_info: dict[str, Any] | None = None,
    ) -> TicketAnalysisResult:
        message = ticket_message.strip()
        if not message:
            raise ClassificationError("Ticket message cannot be empty.")

        if self.config.mock_ai_mode:
            return self.mock_ai_service.classify_ticket(message, customer_info)

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

    def _system_prompt(self) -> str:
        return (
            CLASSIFICATION_SYSTEM_PROMPT
        )
