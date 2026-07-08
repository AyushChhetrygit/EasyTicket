## 4. Priority estimation service

- [ ]  Create `app/services/priority_service.py`.
- [ ]  Define clear priority rules in the system prompt.
- [ ]  Consider:
    - [ ]  Number of users affected
    - [ ]  Complete outage
    - [ ]  Business impact
    - [ ]  Availability of workaround
    - [ ]  Customer plan
    - [ ]  Security impact
    - [ ]  Financial impact
    - [ ]  Time sensitivity
- [ ]  Return only P0–P4.
- [ ]  Return a short reason.
- [ ]  Validate output using Pydantic.
- [ ]  Retry once on invalid output.
- [ ]  Test complete outage as P0.
- [ ]  Test business-critical access issue as P1.
- [ ]  Test issue with workaround as P2.
- [ ]  Test normal issue as P3.
- [ ]  Test low-impact feature request as P4.

## 5. Team-routing service

- [ ]  Create `app/services/routing_service.py`.
- [ ]  Accept:
    - [ ]  Ticket message
    - [ ]  Category
    - [ ]  Subcategory
    - [ ]  Priority
- [ ]  Route account issues to Account Support.
- [ ]  Route billing and refund issues to Billing Support.
- [ ]  Route normal technical issues to Technical Support.
- [ ]  Route severe bugs and outages to Engineering.
- [ ]  Route feature requests to Product Team.
- [ ]  Return assigned team.
- [ ]  Return routing reason.
- [ ]  Validate team value using Pydantic.
- [ ]  Test each support team.
- [ ]  Test high-priority override to Engineering.

---

## 6. AI orchestrator

- [ ]  Create `app/workflows/ticket_analysis_workflow.py`.
- [ ]  Implement:

```
asyncdefanalyze_ticket(ticket,customer):
    ...
```

- [ ]  Call ticket classification.
- [ ]  Pass classification to priority estimation.
- [ ]  Pass classification and priority to team routing.
- [ ]  Combine all outputs into one result.
- [ ]  Return one validated `TicketAnalysisResult`.
- [ ]  Add timeout handling.
- [ ]  Add invalid-output handling.
- [ ]  Add retry handling.
- [ ]  Do not write directly to the database.
- [ ]  Keep the orchestrator independent from FastAPI.
- [ ]  Allow the service to be tested with plain Python.
- [ ]  Add logging without exposing API keys or sensitive prompts.

## 7. Prompt files

- [ ]  Create:

```
app/agents/prompts/
```

- [ ]  Add:
    - [ ]  `classification_prompt.py`
    - [ ]  `priority_prompt.py`
    - [ ]  `routing_prompt.py`
- [ ]  Define categories explicitly.
- [ ]  Define priorities explicitly.
- [ ]  Define teams explicitly.
- [ ]  Tell the model not to invent categories.
- [ ]  Tell the model not to invent teams.
- [ ]  Require JSON output.
- [ ]  Add two or three examples per service.
- [ ]  Keep prompts versioned in Git.
- [ ]  Avoid embedding API keys or environment-specific values.