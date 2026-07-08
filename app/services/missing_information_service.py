from __future__ import annotations

import re

from app.services.text_normalization_service import normalize_user_text

REQUIRED_FIELDS_BY_CATEGORY = {
    "billing": ["invoice_id", "payment_date", "payment_method", "subscription_plan"],
    "account": ["account_email", "error_message", "login_method"],
    "technical": ["error_code", "workspace_id", "browser_or_device", "steps_to_reproduce"],
    "refund": ["order_id", "refund_reason", "amount", "purchase_date"],
    "feature_request": ["desired_feature", "use_case", "business_impact"],
}


def detect_missing_information(message: str, category: str | None) -> list[str]:
    """Return required fields that are not evident in the ticket message."""
    normalized_message = normalize_user_text(message)
    normalized_category = _normalize_category(normalized_message, category)
    required_fields = REQUIRED_FIELDS_BY_CATEGORY.get(normalized_category, [])
    return [
        field
        for field in required_fields
        if not _field_present(field, normalized_message)
    ]


def _normalize_category(message: str, category: str | None) -> str:
    text = normalize_user_text(message)
    if category == "billing" and "refund" in text:
        return "refund"
    return str(category or "").lower()


def _field_present(field: str, message: str) -> bool:
    text = normalize_user_text(message)
    checks = {
        "invoice_id": lambda: bool(re.search(r"\b(inv|invoice)[-\s:]?[a-z0-9]+", text)),
        "payment_date": lambda: _has_date(text),
        "payment_method": lambda: any(term in text for term in ("card", "visa", "mastercard", "upi", "paypal", "bank")),
        "subscription_plan": lambda: any(term in text for term in ("free", "pro", "enterprise", "starter", "business")),
        "account_email": lambda: bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)),
        "error_message": lambda: any(term in text for term in ("error", "says", "message", "failed", "denied")),
        "login_method": lambda: any(term in text for term in ("google", "sso", "password", "email login", "magic link")),
        "error_code": lambda: bool(re.search(r"\b(4\d{2}|5\d{2}|[a-z]+_[a-z_]+)\b", text)),
        "workspace_id": lambda: bool(re.search(r"\b(workspace|ws)[-\s:]?[a-z0-9]+", text)),
        "browser_or_device": lambda: any(term in text for term in ("chrome", "safari", "firefox", "edge", "ios", "android", "mac", "windows")),
        "steps_to_reproduce": lambda: any(term in text for term in ("steps", "reproduce", "first", "then", "after i")),
        "order_id": lambda: bool(re.search(r"\b(order|ord)[-\s:]?[a-z0-9]+", text)),
        "refund_reason": lambda: any(term in text for term in ("because", "reason", "duplicate", "accidental", "not needed")),
        "amount": lambda: bool(re.search(r"(?:\$|usd\s*)\d+|\b\d+(?:\.\d{1,2})?\s?(?:usd|dollars)\b", text)),
        "purchase_date": lambda: _has_date(text),
        "desired_feature": lambda: any(term in text for term in ("feature", "add", "support", "would like", "need")),
        "use_case": lambda: any(term in text for term in ("so that", "use case", "we need to", "our team")),
        "business_impact": lambda: any(term in text for term in ("revenue", "customers", "blocked", "save time", "business")),
    }
    return checks[field]()


def _has_date(text: str) -> bool:
    return bool(
        re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        or re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text)
        or any(month in text for month in (
            "jan", "feb", "mar", "apr", "may", "jun",
            "jul", "aug", "sep", "oct", "nov", "dec",
            "today", "yesterday",
        ))
    )
