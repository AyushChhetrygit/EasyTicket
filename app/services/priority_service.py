"""Priority estimation service for support tickets."""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.agents.prompts.priority_prompt import PRIORITY_SYSTEM_PROMPT
from app.models.ai_schemas import PriorityResult
from config.llm_config import LLMConfig, get_llm_config


class PriorityEstimationError(Exception):
    """Raised when priority estimation cannot produce valid output."""


class PriorityEstimationService:
    def __init__(
        self,
        client: genai.Client | None = None,
        config: LLMConfig | None = None,
    ) -> None:
        self.config = config or get_llm_config()
        self.client = client

    def estimate_priority(
        self,
        ticket_message: str,
        customer_info: dict[str, Any] | None = None,
    ) -> PriorityResult:
        message = ticket_message.strip()
        if not message:
            raise PriorityEstimationError("Ticket message cannot be empty.")

        if self.config.mock_ai_mode:
            return self._mock_priority(message, customer_info)

        client = self.client or self._build_client()
        payload: dict[str, Any] = {"message": message}
        if customer_info:
            payload["customer"] = customer_info

        last_error: Exception | None = None
        for _ in range(2):
            try:
                response_text = self._generate_live_response(client, payload)
                return PriorityResult.model_validate(json.loads(response_text))
            except (ValidationError, json.JSONDecodeError, PriorityEstimationError) as error:
                last_error = error

        raise PriorityEstimationError(
            f"Priority validation failed after retry: {last_error}"
        )

    def _build_client(self) -> genai.Client:
        api_key = self.config.gemini_api_key
        if api_key is None:
            raise PriorityEstimationError("GEMINI_API_KEY is required for live AI mode.")
        return genai.Client(api_key=api_key.get_secret_value())

    def _generate_live_response(
        self,
        client: genai.Client,
        payload: dict[str, Any],
    ) -> str:
        response = client.models.generate_content(
            model=self.config.gemini_model_name,
            contents=f"{PRIORITY_SYSTEM_PROMPT}\n\nInput:\n{json.dumps(payload)}",
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
            raise PriorityEstimationError("Gemini returned an empty priority response.")
        return response.text

    def _mock_priority(
        self,
        message: str,
        customer_info: dict[str, Any] | None,
    ) -> PriorityResult:
        normalized = message.lower()
        plan = str((customer_info or {}).get("plan", "")).lower()

        if any(
            term in normalized
            for term in ("all users", "complete outage", "system down", "service down")
        ):
            return PriorityResult(priority="P0", reason="A complete outage is reported.")
        if any(term in normalized for term in ("security", "data leak", "breach")):
            return PriorityResult(priority="P0", reason="Security impact requires immediate handling.")
        if any(term in normalized for term in ("payment", "charged", "deducted", "invoice")):
            return PriorityResult(priority="P1", reason="Financial impact requires urgent support.")
        if (
            "enterprise" in plan
            and any(term in normalized for term in ("cannot access", "blocked", "login"))
        ) or "business-critical" in normalized:
            return PriorityResult(priority="P1", reason="Business-critical access is blocked.")
        if any(term in normalized for term in ("workaround", "alternative", "csv download")):
            return PriorityResult(priority="P2", reason="Impact exists but a workaround is available.")
        if any(term in normalized for term in ("feature", "nice to have", "request")):
            return PriorityResult(priority="P4", reason="Low-impact feature request.")
        return PriorityResult(priority="P3", reason="Normal issue with limited immediate impact.")
