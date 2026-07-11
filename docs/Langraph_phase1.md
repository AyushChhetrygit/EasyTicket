## 15. LangGraph setup

- [x]  Add LangGraph dependency.
- [x]  Create:

```
app/workflows/langgraph_ticket_workflow.py
```

- [x]  Define workflow state.
- [x]  Create graph builder function.
- [x]  Add individual workflow nodes.
- [x]  Add conditional edges.
- [x]  Add retry path.
- [x]  Add failure path.
- [x]  Add human approval node.

---

## 16. TicketState schema

Use the suggested workflow state from the plan.

- [x]  Create `TicketState`.
- [x]  Include:
    - [x]  `ticket`
    - [x]  `classification`
    - [x]  `priority`
    - [x]  `customer_context`
    - [x]  `retrieved_documents`
    - [x]  `draft_response`
    - [x]  `confidence`
    - [x]  `escalation_required`
    - [x]  `escalation_packet`
    - [x]  `errors`

---

## 17. LangGraph nodes

Create these nodes one by one:

- [x]  `ticket_intake_node`
- [x]  `classification_node`
- [x]  `priority_evaluation_node`
- [x]  `customer_context_node`
- [x]  `knowledge_retrieval_node`
- [x]  `response_generation_node`
- [x]  `verification_node`
- [x]  `decision_node`
- [x]  `reply_node`
- [x]  `ask_information_node`
- [x]  `escalation_node`
- [x]  `human_approval_node`
- [x]  `failure_node`

---

## 18. Conditional routing

The plan gives examples: if confidence is high, respond; if information is missing, ask the customer; if risk is high, escalate; if verification fails, retry once.

- [x]  If confidence is greater than or equal to threshold, route to response.
- [x]  If required information is missing, route to ask-information.
- [x]  If risk is high, route to escalation.
- [x]  If verification fails, retry once.
- [x]  If retry fails, route to failure path.
- [x]  If sensitive action exists, route to human approval.
- [x]  Save final action in state.

---

## 19. Verification node

- [x]  Check whether generated answer has sources.
- [x]  Check whether answer is grounded in retrieved documents.
- [x]  Check whether confidence is above threshold.
- [x]  Check whether sensitive actions are not auto-approved.
- [x]  Check whether required information is missing.
- [x]  Return pass/fail.
- [x]  Add reason for verification failure.
- [x]  Trigger retry once if failed.
