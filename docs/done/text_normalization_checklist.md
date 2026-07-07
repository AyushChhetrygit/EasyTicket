## Text normalization for messy user messages

Goal: normalize contractions, slang, and common support shorthand before RAG search, routing, sentiment detection, and missing-information checks.

---

## 1. Dependency decision

- [x] Decide whether to add `contractions>=0.1.73` to `requirements.txt`.
- [x] Keep a local fallback dictionary so the project still works without network/API access.
- [x] Do not add spellchecking yet unless tests show it is needed.

Decision: do not add a new dependency yet. Use a local dictionary first so tests and local RAG work offline.

---

## 2. Text normalization service

- [x] Create:

```
app/services/text_normalization_service.py
```

- [x] Add `normalize_user_text(text: str | None) -> str`.
- [x] Expand contractions:
    - [x] `can't` -> `cannot`
    - [x] `won't` -> `will not`
    - [x] `wouldn't` -> `would not`
    - [x] `I'm` -> `I am`
    - [x] `you're` -> `you are`
- [x] Expand support slang and shorthand:
    - [x] `pls` / `plz` -> `please`
    - [x] `wanna` -> `want to`
    - [x] `gonna` -> `going to`
    - [x] `u` -> `you`
    - [x] `ur` -> `your`
    - [x] `asap` -> `as soon as possible`
    - [x] `idk` -> `I do not know`
    - [x] `sub` -> `subscription`
    - [x] `acct` -> `account`
    - [x] `pwd` -> `password`
- [x] Preserve important technical tokens:
    - [x] HTTP status codes like `401`, `403`, `500`
    - [x] Workspace IDs like `WS-123`
    - [x] Invoice/order IDs
    - [x] Email addresses
- [x] Collapse extra whitespace.
- [x] Handle empty text safely.

---

## 3. Service integration

- [x] Use normalized text in `embedding_service.normalize_text`.
- [x] Use normalized text in `rag_search_service.search_knowledge_base`.
- [x] Use normalized text in `missing_information_service.detect_missing_information`.
- [x] Use normalized text in `sentiment_service.analyze_sentiment`.
- [x] Use normalized text in `rule_based_router.classify_ticket`.
- [x] Keep original ticket message unchanged for audit/history display.

---

## 4. Tests

- [x] Add:

```
tests/test_text_normalization_service.py
```

- [x] Test contractions:
    - [x] `can't login` -> `cannot login`
    - [x] `wouldn't work` -> `would not work`
- [x] Test slang:
    - [x] `pls help` -> `please help`
    - [x] `wanna cancel my sub asap` -> `want to cancel my subscription as soon as possible`
- [x] Test integration with account routing:
    - [x] `pls help i can't login` routes as account-related.
- [x] Test integration with RAG:
    - [x] `i paid for pro but my sub isn't active` retrieves `subscription_activation.txt`.
- [x] Test integration with sentiment:
    - [x] `pls fix asap production blocked` returns urgency score above `0`.
- [x] Run full test suite.

---

## 5. Documentation

- [x] Update `docs/run_project_steps.txt` if a new dependency is added.
- [x] Add a manual normalization check command.
- [x] Mention that original user text is stored as-is, while normalized text is used for matching/retrieval.
