## 9. Missing information detector

- [x]  Create:

```
app/services/missing_information_service.py
```

- [x]  Detect missing information based on category.

For billing:

- [x]  Invoice ID
- [x]  Payment date
- [x]  Payment method
- [x]  Subscription plan

For account:

- [x]  Account email
- [x]  Error message
- [x]  Login method

For technical:

- [x]  Error code
- [x]  Workspace ID
- [x]  Browser/device
- [x]  Steps to reproduce

For refund:

- [x]  Order ID
- [x]  Refund reason
- [x]  Amount
- [x]  Purchase date

For feature request:

- [x]  Desired feature
- [x]  Use case
- [x]  Business impact

---

## 10. Sentiment and urgency detector

- [x]  Create:

```
app/services/sentiment_service.py
```

- [x]  Detect negative sentiment.
- [x]  Detect urgency words:
    - [x]  urgent
    - [x]  immediately
    - [x]  blocked
    - [x]  production
    - [x]  client demo
    - [x]  losing money
    - [x]  angry
    - [x]  unacceptable
- [x]  Return sentiment label:
    - [x]  positive
    - [x]  neutral
    - [x]  negative
- [x]  Return urgency score.
- [x]  Use rule-based logic first.
- [x]  Add LLM-based sentiment later only if needed.

## 11. Escalation packet schema

- [x]  Create:

```
app/models/escalation_packet_schemas.py
```

- [x]  Create `EscalationPacket`.
- [x]  Include:
    - [x]  Ticket ID
    - [x]  Customer summary
    - [x]  Issue summary
    - [x]  Category
    - [x]  Priority
    - [x]  Business impact
    - [x]  Steps already attempted
    - [x]  Knowledge articles checked
    - [x]  Missing information
    - [x]  Possible cause
    - [x]  Recommended team
    - [x]  Recommended next actions
    - [x]  Internal note
    - [x]  Customer reply
