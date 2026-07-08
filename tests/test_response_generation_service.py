from app.services.rag_search_service import search_knowledge_base
from app.services.response_generation_service import (
    NO_ANSWER_MESSAGE,
    generate_rag_answer,
)


def test_generate_answer_uses_retrieved_knowledge():
    search_result = search_knowledge_base("paid but subscription is inactive")

    answer = generate_rag_answer(
        "I paid but my subscription is inactive.",
        {"plan": "pro"},
        search_result,
    )

    assert answer.confidence > 0
    assert answer.sources
    assert answer.should_escalate is False
    assert "invoice number" in answer.answer.lower()


def test_generate_answer_returns_no_answer_fallback():
    search_result = search_knowledge_base("unrelated cooking question", confidence_threshold=0.7)

    answer = generate_rag_answer(
        "How do I bake bread?",
        {},
        search_result,
    )

    assert answer.answer == NO_ANSWER_MESSAGE
    assert answer.sources == []
    assert answer.confidence == 0.0
    assert answer.should_escalate is True
