from app.models.enums import TicketCategory
from app.services.rag_search_service import search_knowledge_base
from app.services.rule_based_router import classify_ticket
from app.services.sentiment_service import analyze_sentiment
from app.services.text_normalization_service import normalize_user_text


def test_expands_contractions():
    assert normalize_user_text("can't login") == "cannot login"
    assert normalize_user_text("wouldn't work") == "would not work"


def test_expands_support_slang():
    assert normalize_user_text("pls help") == "please help"
    assert (
        normalize_user_text("wanna cancel my sub asap")
        == "want to cancel my subscription as soon as possible"
    )


def test_preserves_important_support_tokens():
    text = normalize_user_text("API 401 for WS-123 and invoice INV-77 user@example.com")

    assert "401" in text
    assert "ws-123" in text
    assert "inv-77" in text
    assert "user@example.com" in text


def test_messy_account_message_routes_to_account():
    result = classify_ticket("pls help i can't login")

    assert result.category == TicketCategory.ACCOUNT


def test_messy_subscription_message_retrieves_subscription_article():
    result = search_knowledge_base("i paid for pro but my sub isn't active")

    assert result.has_answer is True
    assert "subscription_activation.txt" in result.sources


def test_messy_urgent_message_affects_sentiment_urgency():
    result = analyze_sentiment("pls fix asap production blocked")

    assert result.urgency_score > 0
    assert "production" in result.urgency_terms
    assert "blocked" in result.urgency_terms
