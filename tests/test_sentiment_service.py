from app.services.sentiment_service import analyze_sentiment


def test_detects_negative_sentiment_and_urgency_terms():
    result = analyze_sentiment(
        "This is unacceptable, production is blocked and we are losing money."
    )

    assert result.sentiment == "negative"
    assert result.negative_sentiment is True
    assert result.urgency_score > 0.5
    assert "production" in result.urgency_terms
    assert "blocked" in result.urgency_terms


def test_detects_positive_sentiment():
    result = analyze_sentiment("Thanks, the new workflow is great.")

    assert result.sentiment == "positive"
    assert result.urgency_score == 0.0


def test_detects_neutral_sentiment():
    result = analyze_sentiment("How do I reset my password?")

    assert result.sentiment == "neutral"
    assert result.negative_sentiment is False
