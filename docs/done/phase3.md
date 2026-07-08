## 8. Mock AI service

A mock mode lets both teammates continue working without API failures or token costs.

- [ ]  Create `app/services/mock_ai_service.py`.
- [ ]  Return deterministic classifications.
- [ ]  Return deterministic priorities.
- [ ]  Return deterministic teams.
- [ ]  Enable using:

```
USE_MOCK_AI=true
```

- [ ]  Include artificial failure mode for testing fallback.
- [ ]  Include artificial invalid JSON mode.
- [ ]  Share mock response examples with Teammate 1.

---

## 9. Streamlit frontend

- [ ]  Create:

```
frontend/app.py
```

- [ ]  Add backend base URL configuration.
- [ ]  Create “Create Ticket” form.
- [ ]  Add customer selector.
- [ ]  Add ticket message input.
- [ ]  Call `POST /tickets`.
- [ ]  Show created ticket ID.
- [ ]  Add “Analyze Ticket” button.
- [ ]  Call `POST /tickets/{ticket_id}/analyze`.
- [ ]  Display:
    - [ ]  Category
    - [ ]  Subcategory
    - [ ]  Confidence
    - [ ]  Priority
    - [ ]  Assigned team
    - [ ]  Reason
    - [ ]  Analysis source
- [ ]  Create ticket list page.
- [ ]  Add filters for status, priority, and team.
- [ ]  Create ticket details page.
- [ ]  Add status update control.
- [ ]  Add manual escalation form.
- [ ]  Display ticket history.
- [ ]  Show clear backend error messages.
- [ ]  Show loading indicator while analysis runs.
- [ ]  Avoid exposing the LLM API key to Streamlit.

---

## 10. AI tests

- [ ]  Test valid classification output.
- [ ]  Test invalid category rejection.
- [ ]  Test confidence above `1.0`.
- [ ]  Test missing classification fields.
- [ ]  Test valid priority output.
- [ ]  Test invalid priority rejection.
- [ ]  Test valid team routing.
- [ ]  Test invalid team rejection.
- [ ]  Test orchestrator combined output.
- [ ]  Mock the LLM during tests.
- [ ]  Test LLM timeout.
- [ ]  Test malformed JSON.
- [ ]  Test retry behaviour.
- [ ]  Test controlled failure after retry.
- [ ]  Test no API key in mock mode.