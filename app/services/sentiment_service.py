from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.text_normalization_service import normalize_user_text

SentimentLabel = Literal["positive", "neutral", "negative"]

NEGATIVE_TERMS = ("angry", "unacceptable", "terrible", "frustrated", "upset", "furious", "bad")
POSITIVE_TERMS = ("thanks", "thank you", "great", "helpful", "appreciate")
URGENCY_TERMS = (
    "urgent",
    "immediately",
    "blocked",
    "production",
    "client demo",
    "losing money",
    "angry",
    "unacceptable",
)


@dataclass
class SentimentResult:
    sentiment: SentimentLabel
    urgency_score: float
    negative_sentiment: bool
    urgency_terms: list[str]


def analyze_sentiment(message: str) -> SentimentResult:
    """Rule-based sentiment and urgency detector."""
    text = normalize_user_text(message)
    urgency_terms = [term for term in URGENCY_TERMS if term in text]
    negative_hits = [term for term in NEGATIVE_TERMS if term in text]
    positive_hits = [term for term in POSITIVE_TERMS if term in text]

    if negative_hits or any(term in urgency_terms for term in ("angry", "unacceptable")):
        sentiment: SentimentLabel = "negative"
    elif positive_hits:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    urgency_score = min(1.0, round(len(urgency_terms) * 0.15, 2))
    if "production" in urgency_terms or "losing money" in urgency_terms:
        urgency_score = min(1.0, round(urgency_score + 0.25, 2))

    return SentimentResult(
        sentiment=sentiment,
        urgency_score=urgency_score,
        negative_sentiment=sentiment == "negative",
        urgency_terms=urgency_terms,
    )
