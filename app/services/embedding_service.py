"""Offline embedding helpers for RAG search.

This module intentionally uses deterministic mock embeddings so local tests do
not need an API key or network access. The interface can later be swapped for
hosted embeddings without changing the search service.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.services.text_normalization_service import normalize_user_text

EMBEDDING_DIMENSIONS = 64


class EmbeddingServiceError(Exception):
    """Raised when text cannot be embedded."""


def normalize_text(text: str | None) -> str:
    """Lowercase text and collapse punctuation/whitespace for retrieval."""
    normalized_user_text = normalize_user_text(text)
    if not normalized_user_text:
        return ""
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized_user_text)
    return re.sub(r"\s+", " ", normalized).strip()


def generate_embedding(text: str | None, *, mock_mode: bool = True) -> list[float]:
    """Generate a deterministic embedding for a document chunk or query."""
    if not mock_mode:
        raise EmbeddingServiceError("API embeddings are not configured yet.")

    normalized = normalize_text(text)
    if not normalized:
        return [0.0] * EMBEDDING_DIMENSIONS

    try:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        for token in normalized.split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSIONS
            weight = 1.0 + (len(token) / 20.0)
            vector[index] += weight
        return _unit_vector(vector)
    except Exception as error:
        raise EmbeddingServiceError("Embedding generation failed.") from error


def generate_chunk_embeddings(chunks: list[str], *, mock_mode: bool = True) -> list[list[float]]:
    """Generate embeddings for multiple chunks."""
    return [generate_embedding(chunk, mock_mode=mock_mode) for chunk in chunks]


def generate_query_embedding(query: str | None, *, mock_mode: bool = True) -> list[float]:
    """Generate an embedding for a user query."""
    return generate_embedding(query, mock_mode=mock_mode)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for normalized or raw vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _unit_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
