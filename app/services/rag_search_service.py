"""Knowledge-base retrieval service for EasyTicket RAG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from app.services.embedding_service import (
    EmbeddingServiceError,
    cosine_similarity,
    generate_embedding,
    generate_query_embedding,
    normalize_text,
)
from app.services.text_normalization_service import normalize_user_text

KNOWLEDGE_BASE_DIR = Path("knowledege base docs")
DEFAULT_CONFIDENCE_THRESHOLD = 0.18


@dataclass
class KnowledgeChunk:
    source_filename: str
    text: str
    embedding: list[float]


@dataclass
class RagSearchResult:
    passages: list[str]
    sources: list[str]
    confidence: float
    has_answer: bool


def search_knowledge_base(
    query: str,
    *,
    top_k: int = 3,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR,
) -> RagSearchResult:
    """Retrieve the most relevant KB passages for a query."""
    normalized_query = normalize_text(normalize_user_text(query))
    if not normalized_query:
        return no_answer_result()

    try:
        query_embedding = generate_query_embedding(normalized_query)
        chunks = load_knowledge_chunks(knowledge_base_dir)
    except (OSError, EmbeddingServiceError):
        return no_answer_result()

    scored = []
    for chunk in chunks:
        semantic_score = cosine_similarity(query_embedding, chunk.embedding)
        lexical_score = _lexical_overlap(normalized_query, chunk.text)
        score = max(semantic_score, lexical_score)
        if score >= confidence_threshold:
            scored.append((score, chunk))

    if not scored:
        return no_answer_result()

    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[:top_k]
    confidence = round(best[0][0], 2)
    sources = list(dict.fromkeys(chunk.source_filename for _, chunk in best))
    passages = [chunk.text for _, chunk in best]
    return RagSearchResult(
        passages=passages,
        sources=sources,
        confidence=confidence,
        has_answer=True,
    )


def load_knowledge_chunks(knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR) -> list[KnowledgeChunk]:
    """Load text files and split them into searchable chunks."""
    chunks: list[KnowledgeChunk] = []
    for path in sorted(knowledge_base_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        for chunk_text in _chunk_text(text):
            chunks.append(
                KnowledgeChunk(
                    source_filename=path.name,
                    text=chunk_text,
                    embedding=generate_embedding(chunk_text),
                )
            )
    return chunks


def no_answer_result() -> RagSearchResult:
    return RagSearchResult(passages=[], sources=[], confidence=0.0, has_answer=False)


def _chunk_text(text: str, *, max_chars: int = 900) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def _lexical_overlap(query: str, passage: str) -> float:
    query_terms = set(normalize_text(query).split())
    passage_terms = set(normalize_text(passage).split())
    if not query_terms or not passage_terms:
        return 0.0
    return len(query_terms & passage_terms) / len(query_terms)
