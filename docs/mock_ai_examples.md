# Mock AI Response Examples

Use `USE_MOCK_AI=true` for deterministic local development without Gemini API calls.

## Billing

Input:

```json
{"message": "My payment was deducted but my subscription is inactive."}
```

Output:

```json
{
  "category": "billing",
  "subcategory": "subscription_activation",
  "classification_confidence": 0.92,
  "priority": "P1",
  "assigned_team": "Billing Support",
  "reason": "The ticket describes a billing or subscription issue."
}
```

## Account

Input:

```json
{"message": "I cannot access my account."}
```

Output:

```json
{
  "category": "account",
  "subcategory": "account_access",
  "classification_confidence": 0.84,
  "priority": "P2",
  "assigned_team": "Account Support",
  "reason": "The ticket appears related to account access or account state."
}
```

## Failure Modes

- `MockAIService(failure_mode="fail")` raises a controlled mock failure.
- `MockAIService(failure_mode="invalid_json")` raises a controlled invalid JSON failure.
