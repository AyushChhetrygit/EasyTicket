from app.services.rag_search_service import search_knowledge_base


def test_search_returns_relevant_passage_and_source():
    result = search_knowledge_base("payment succeeded but subscription is not active")

    assert result.has_answer is True
    assert result.confidence > 0
    assert "subscription_activation.txt" in result.sources
    assert any("subscription" in passage.lower() for passage in result.passages)


def test_search_returns_no_answer_for_unrelated_query():
    result = search_knowledge_base(
        "how do I bake sourdough bread with cinnamon",
        confidence_threshold=0.6,
    )

    assert result.has_answer is False
    assert result.sources == []
    assert result.passages == []
    assert result.confidence == 0.0


def test_search_returns_api_authentication_source():
    result = search_knowledge_base("api returns 401 unauthorized invalid token")

    assert result.has_answer is True
    assert "api_authentication_errors.txt" in result.sources
