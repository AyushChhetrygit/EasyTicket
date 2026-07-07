from __future__ import annotations

import re

CONTRACTION_EXPANSIONS = {
    "can't": "cannot",
    "cant": "cannot",
    "won't": "will not",
    "wouldn't": "would not",
    "isn't": "is not",
    "aren't": "are not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "i'm": "i am",
    "you're": "you are",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "i've": "i have",
    "we've": "we have",
    "i'll": "i will",
    "we'll": "we will",
}

SUPPORT_SHORTHAND_EXPANSIONS = {
    "pls": "please",
    "plz": "please",
    "wanna": "want to",
    "gonna": "going to",
    "u": "you",
    "ur": "your",
    "asap": "as soon as possible",
    "idk": "i do not know",
    "sub": "subscription",
    "acct": "account",
    "pwd": "password",
}


def normalize_user_text(text: str | None) -> str:
    """Normalize messy user text while preserving useful support tokens."""
    if not text:
        return ""

    normalized = text.lower()
    normalized = _expand_terms(normalized, CONTRACTION_EXPANSIONS)
    normalized = _expand_terms(normalized, SUPPORT_SHORTHAND_EXPANSIONS)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _expand_terms(text: str, expansions: dict[str, str]) -> str:
    for source, replacement in expansions.items():
        pattern = rf"(?<![a-z0-9]){re.escape(source)}(?![a-z0-9])"
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text
