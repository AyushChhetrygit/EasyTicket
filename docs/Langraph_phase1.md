## 15. LangGraph setup

- [ ]  Add LangGraph dependency.
- [ ]  Create:

```
app/workflows/langgraph_ticket_workflow.py
```

- [ ]  Define workflow state.
- [ ]  Create graph builder function.
- [ ]  Add individual workflow nodes.
- [ ]  Add conditional edges.
- [ ]  Add retry path.
- [ ]  Add failure path.
- [ ]  Add human approval node.

---

## 16. TicketState schema

Use the suggested workflow state from the plan.

- [ ]  Create `TicketState`.
- [ ]  Include:
    - [ ]  `ticket`
    - [ ]  `classification`
    - [ ]  `priority`
    - [ ]  `customer_context`
    - [ ]  `retrieved_documents`
    - [ ]  `draft_response`
    - [ ]  `confidence`
    - [ ]  `escalation_required`
    - [ ]  `escalation_packet`
    - [ ]  `errors`

---

## 17. LangGraph nodes

Create these nodes one by one:

- [ ]  `ticket_intake_node`
- [ ]  `classification_node`
- [ ]  `priority_evaluation_node`
- [ ]  `customer_context_node`
- [ ]  `knowledge_retrieval_node`
- [ ]  `response_generation_node`
- [ ]  `verification_node`
- [ ]  `decision_node`
- [ ]  `reply_node`
- [ ]  `ask_information_node`
- [ ]  `escalation_node`
- [ ]  `human_approval_node`
- [ ]  `failure_node`

---

## 18. Conditional routing

The plan gives examples: if confidence is high, respond; if information is missing, ask the customer; if risk is high, escalate; if verification fails, retry once.

- [ ]  If confidence is greater than or equal to threshold, route to response.
- [ ]  If required information is missing, route to ask-information.
- [ ]  If risk is high, route to escalation.
- [ ]  If verification fails, retry once.
- [ ]  If retry fails, route to failure path.
- [ ]  If sensitive action exists, route to human approval.
- [ ]  Save final action in state.

---

## 19. Verification node

- [ ]  Check whether generated answer has sources.
- [ ]  Check whether answer is grounded in retrieved documents.
- [ ]  Check whether confidence is above threshold.
- [ ]  Check whether sensitive actions are not auto-approved.
- [ ]  Check whether required information is missing.
- [ ]  Return pass/fail.
- [ ]  Add reason for verification failure.
- [ ]  Trigger retry once if failed.