from app.services.missing_information_service import detect_missing_information


def test_billing_missing_information():
    missing = detect_missing_information(
        "My Pro payment by card failed on 2026-07-01.",
        "billing",
    )

    assert "invoice_id" in missing
    assert "payment_date" not in missing
    assert "payment_method" not in missing
    assert "subscription_plan" not in missing


def test_account_missing_information():
    missing = detect_missing_information(
        "Login says invalid password for user@example.com.",
        "account",
    )

    assert "account_email" not in missing
    assert "error_message" not in missing
    assert "login_method" not in missing


def test_technical_missing_information():
    missing = detect_missing_information(
        "API returns 500 in Chrome for workspace WS-123 after I click export.",
        "technical",
    )

    assert "error_code" not in missing
    assert "workspace_id" not in missing
    assert "browser_or_device" not in missing
    assert "steps_to_reproduce" not in missing


def test_refund_missing_information():
    missing = detect_missing_information(
        "Refund $150 for order ORD-99 because duplicate purchase yesterday.",
        "refund",
    )

    assert missing == []


def test_feature_request_missing_information():
    missing = detect_missing_information(
        "Please add bulk export so that our team can save time for customers.",
        "feature_request",
    )

    assert missing == []
