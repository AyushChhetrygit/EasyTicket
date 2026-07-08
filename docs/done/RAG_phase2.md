## 6. Escalation schema

- [x]  Create:

```
app/models/escalation_schemas.py
```

- [x]  Create `EscalationDecision`.
- [x]  Add fields:
    - [x]  `action`
    - [x]  `escalation_required`
    - [x]  `escalation_score`
    - [x]  `human_approval_required`
    - [x]  `sensitive_action`
    - [x]  `destination_team`
    - [x]  `reason`
    - [x]  `missing_information`

Allowed actions:

- [x]  `suggest_resolution`
- [x]  `request_information`
- [x]  `escalate_to_human`

---

## 7. Escalation scoring logic

- [x]  Create:

```
app/services/escalation_decision_service.py
```

- [x]  Add score for low retrieval confidence.
- [x]  Add score for P0/P1 priority.
- [x]  Add score for refund requests.
- [x]  Add score for account deletion.
- [x]  Add score for subscription cancellation.
- [x]  Add score for security incidents.
- [x]  Add score for data-loss claims.
- [x]  Add score for enterprise customers.
- [x]  Add score for repeated customer attempts.
- [x]  Add score for negative sentiment.
- [x]  Add score for missing required information.
- [x]  Normalize final score between `0.0` and `1.0`.

---

## 8. Escalation decision rules

Use the decision logic from the plan as the foundation.

- [x]  If priority is `P0`, escalate.
- [x]  If priority is `P1`, escalate.
- [x]  If retrieval confidence is below `0.65`, escalate.
- [x]  If category is `refund` and amount is above approval limit, escalate.
- [x]  If required information is missing, request information.
- [x]  If action is sensitive, require human approval.
- [x]  Otherwise, suggest resolution.
- [x]  Return clear decision reason.
- [x]  Return recommended destination team.
