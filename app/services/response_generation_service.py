"""RAG answer generation constrained to retrieved knowledge."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.services.rag_search_service import RagSearchResult

NO_ANSWER_MESSAGE = (
    "I do not have enough verified information to answer this safely. "
    "A support agent should review this ticket."
)


@dataclass
class RagAnswer:
    answer: str
    sources: list[str]
    confidence: float
    should_escalate: bool


def generate_rag_answer(
    ticket_message: str,
    customer_context: dict[str, Any] | None,
    retrieved_knowledge: RagSearchResult,
) -> RagAnswer:
    """Return a customer-facing answer using only retrieved passages."""
    if not retrieved_knowledge.has_answer or retrieved_knowledge.confidence <= 0.0:
        return no_answer()

    answer = _extract_suggested_response(retrieved_knowledge.passages)
    if not answer:
        return no_answer()

    return RagAnswer(
        answer=answer,
        sources=retrieved_knowledge.sources,
        confidence=retrieved_knowledge.confidence,
        should_escalate=False,
    )


def no_answer() -> RagAnswer:
    return RagAnswer(
        answer=NO_ANSWER_MESSAGE,
        sources=[],
        confidence=0.0,
        should_escalate=True,
    )


def _extract_suggested_response(passages: list[str]) -> str:
    combined = "\n\n".join(passages)
    match = re.search(
        r"Suggested customer response:\s*(.+?)(?:\n\n[A-Z][A-Za-z ]+:|Source filename:|\Z)",
        combined,
        flags=re.DOTALL,
    )
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()
