from app.services.embedding_service import (
    EMBEDDING_DIMENSIONS,
    EmbeddingServiceError,
    generate_chunk_embeddings,
    generate_query_embedding,
    normalize_text,
)


def test_normalize_text():
    assert normalize_text(" API  Key!! ") == "api key"


def test_generate_query_embedding_is_deterministic():
    first = generate_query_embedding("invoice not generated")
    second = generate_query_embedding("invoice not generated")
    assert first == second
    assert len(first) == EMBEDDING_DIMENSIONS


def test_generate_embedding_handles_empty_text():
    assert generate_query_embedding("") == [0.0] * EMBEDDING_DIMENSIONS


def test_generate_chunk_embeddings():
    embeddings = generate_chunk_embeddings(["password reset", "api auth"])
    assert len(embeddings) == 2


def test_api_embeddings_not_configured():
    try:
        generate_query_embedding("hello", mock_mode=False)
    except EmbeddingServiceError as error:
        assert "not configured" in str(error)
    else:
        raise AssertionError("Expected EmbeddingServiceError")
