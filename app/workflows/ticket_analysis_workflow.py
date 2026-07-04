"""Async ticket analysis workflow."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import ValidationError

from app.models.ai_schemas import TicketAnalysisResult
from app.services.classification_service import (
    ClassificationError,
    TicketClassificationService,
)
from app.services.priority_service import PriorityEstimationError, PriorityEstimationService
from app.services.routing_service import RoutingError, TeamRoutingService
from config.llm_config import LLMConfig, get_llm_config

logger = logging.getLogger(__name__)


class TicketAnalysisWorkflowError(Exception):
    """Raised when the ticket analysis workflow cannot complete."""


async def analyze_ticket(
    ticket: dict[str, Any],
    customer: dict[str, Any] | None = None,
    *,
    classification_service: TicketClassificationService | None = None,
    priority_service: PriorityEstimationService | None = None,
    routing_service: TeamRoutingService | None = None,
    timeout_seconds: float | None = None,
) -> TicketAnalysisResult:
    """Analyze a ticket without depending on FastAPI or direct database writes."""

    config = get_llm_config()
    timeout = timeout_seconds or config.ai_request_timeout_seconds
    message = str(ticket.get("message", "")).strip()
    if not message:
        raise TicketAnalysisWorkflowError("Ticket message cannot be empty.")

    try:
        return await asyncio.wait_for(
            _analyze_ticket_once(
                message=message,
                customer=customer,
                config=config,
                classification_service=classification_service,
                priority_service=priority_service,
                routing_service=routing_service,
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError as error:
        logger.warning("Ticket analysis timed out.")
        raise TicketAnalysisWorkflowError("Ticket analysis timed out.") from error
    except (
        ClassificationError,
        PriorityEstimationError,
        RoutingError,
        ValidationError,
    ) as error:
        logger.warning("Ticket analysis failed validation: %s", type(error).__name__)
        raise TicketAnalysisWorkflowError("Ticket analysis failed.") from error


async def _analyze_ticket_once(
    *,
    message: str,
    customer: dict[str, Any] | None,
    config: LLMConfig,
    classification_service: TicketClassificationService | None,
    priority_service: PriorityEstimationService | None,
    routing_service: TeamRoutingService | None,
) -> TicketAnalysisResult:
    classifier = classification_service or TicketClassificationService(config=config)
    prioritizer = priority_service or PriorityEstimationService(config=config)
    router = routing_service or TeamRoutingService(config=config)

    classification = await asyncio.to_thread(
        classifier.analyze_ticket,
        message,
        customer,
    )
    priority = await asyncio.to_thread(
        prioritizer.estimate_priority,
        message,
        customer,
    )
    routing = await asyncio.to_thread(
        router.route_ticket,
        message,
        classification.category,
        classification.subcategory,
        priority.priority,
    )

    return TicketAnalysisResult.model_validate(
        {
            "category": classification.category,
            "subcategory": classification.subcategory,
            "classification_confidence": classification.classification_confidence,
            "priority": priority.priority,
            "assigned_team": routing.assigned_team,
            "reason": (
                f"{classification.reason} Priority: {priority.reason} "
                f"Routing: {routing.reason}"
            ),
        }
    )
