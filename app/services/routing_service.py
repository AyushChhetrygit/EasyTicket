"""Team routing service for analyzed support tickets."""

from __future__ import annotations

import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.agents.prompts.routing_prompt import ROUTING_SYSTEM_PROMPT
from app.models.ai_schemas import RoutingResult, TicketCategory, TicketPriority
from app.services.mock_ai_service import MockAIService
from config.llm_config import LLMConfig, get_llm_config


class RoutingError(Exception):
    """Raised when routing cannot produce valid output."""


class TeamRoutingService:
    def __init__(
        self,
        client: genai.Client | None = None,
        config: LLMConfig | None = None,
        mock_ai_service: MockAIService | None = None,
    ) -> None:
        self.config = config or get_llm_config()
        self.client = client
        self.mock_ai_service = mock_ai_service or MockAIService()

    def route_ticket(
        self,
        ticket_message: str,
        category: TicketCategory,
        subcategory: str,
        priority: TicketPriority,
    ) -> RoutingResult:
        message = ticket_message.strip()
        if not message:
            raise RoutingError("Ticket message cannot be empty.")

        if self.config.mock_ai_mode:
            return self.mock_ai_service.route_ticket(category, subcategory, priority)

        client = self.client or self._build_client()
        payload = {
            "message": message,
            "category": category,
            "subcategory": subcategory,
            "priority": priority,
        }

        last_error: Exception | None = None
        for _ in range(2):
            try:
                response_text = self._generate_live_response(client, payload)
                return RoutingResult.model_validate(json.loads(response_text))
            except (ValidationError, json.JSONDecodeError, RoutingError) as error:
                last_error = error

        raise RoutingError(f"Routing validation failed after retry: {last_error}")

    def _build_client(self) -> genai.Client:
        api_key = self.config.gemini_api_key
        if api_key is None:
            raise RoutingError("GEMINI_API_KEY is required for live AI mode.")
        return genai.Client(api_key=api_key.get_secret_value())

    def _generate_live_response(
        self,
        client: genai.Client,
        payload: dict[str, str],
    ) -> str:
        response = client.models.generate_content(
            model=self.config.gemini_model_name,
            contents=f"{ROUTING_SYSTEM_PROMPT}\n\nInput:\n{json.dumps(payload)}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=256,
                http_options=types.HttpOptions(
                    timeout=int(self.config.ai_request_timeout_seconds * 1000)
                ),
            ),
        )
        if not response.text:
            raise RoutingError("Gemini returned an empty routing response.")
        return response.text
