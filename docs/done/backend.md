- [ ]  Clone the shared GitHub repository.
- [ ]  Create branch:

```
feature/backend-foundation
```

- [ ]  Create the base project folders:
    
    ```
    app/
    ├── main.py
    ├── models/
    ├── services/
    ├── agents/
    ├── workflows/
    ├── database/
    ├── api/
    └── utils/
    
    data/
    ├── knowledge_base/
    ├── customers.json
    └── sample_tickets.json
    
    tests/
    scripts/
    ```
    
- [ ]  Create `requirements.txt`.
- [ ]  Add FastAPI.
- [ ]  Add Uvicorn.
- [ ]  Add SQLAlchemy or SQLModel.
- [ ]  Add Pydantic.
- [ ]  Add Pytest.
- [ ]  Add `python-dotenv`.
- [ ]  Create `.env.example`.
- [ ]  Create `.gitignore`.
- [ ]  Add a basic `README.md`.
- [ ]  Confirm the application starts using:

```
uvicorn app.main:app--reload
```

The expected foundation includes a running FastAPI application, health endpoint, models, SQLite, and sample data.

---

## 2. FastAPI foundation

- [x]  Create `app/main.py`.
- [ ]  Create the FastAPI application instance.
- [ ]  Add application title and version.
- [ ]  Add CORS middleware for Streamlit.
- [ ]  Create health-check endpoint:

```
GET /health
```

- [ ]  Return:

```
{
  "status":"healthy"
}
```

- [ ]  Add a global exception handler.
- [ ]  Add request validation error handling.
- [ ]  Include ticket API router.

---

## 3. Database setup

- [ ]  Create `app/database/database.py`.
- [ ]  Configure SQLite connection.
- [ ]  Create database session dependency.
- [ ]  Create database initialization function.
- [ ]  Create database tables automatically during development.
- [ ]  Add a script to reset the local database.
- [ ]  Add a script to seed sample data.
- [ ]  Confirm data survives application restarts.

Suggested database:

```
data/tickets.db
```

---

## 4. Customer model

- [ ]  Create customer database model.
- [ ]  Add fields:
    - [ ]  `customer_id`
    - [ ]  `name`
    - [ ]  `plan`
    - [ ]  `account_status`
    - [ ]  `previous_tickets`
    - [ ]  `created_at`
- [ ]  Create Customer Pydantic schema.
- [ ]  Create Customer response schema.
- [ ]  Add sample customers.
- [ ]  Create service for retrieving a customer by ID.
- [ ]  Raise a clear error when the customer does not exist.

## 5. Ticket model

- [ ]  Create Ticket database model.
- [ ]  Add fields:
    - [ ]  `ticket_id`
    - [ ]  `customer_id`
    - [ ]  `message`
    - [ ]  `status`
    - [ ]  `category`
    - [ ]  `subcategory`
    - [ ]  `priority`
    - [ ]  `assigned_team`
    - [ ]  `classification_confidence`
    - [ ]  `ai_reason`
    - [ ]  `created_at`
    - [ ]  `updated_at`
- [ ]  Add a relationship or foreign key to Customer.
- [ ]  Create `TicketCreate` schema.
- [ ]  Create `TicketUpdate` schema.
- [ ]  Create `TicketResponse` schema.
- [ ]  Add enums for category, status, priority, and support team.
- [ ]  Prevent invalid status values.
- [ ]  Prevent invalid priority values.
- [ ]  Automatically generate ticket IDs.

Example:

```
TICKET-001
TICKET-002
```

---

## 6. Ticket history model

- [ ]  Create `TicketHistory` model.
- [ ]  Add fields:
    - [ ]  `history_id`
    - [ ]  `ticket_id`
    - [ ]  `action`
    - [ ]  `old_value`
    - [ ]  `new_value`
    - [ ]  `performed_by`
    - [ ]  `created_at`
- [ ]  Record ticket creation.
- [ ]  Record status changes.
- [ ]  Record team assignment.
- [ ]  Record priority changes.
- [ ]  Record manual escalation.
- [ ]  Record AI analysis.
- [ ]  Create service to retrieve ticket history.

## 7. Ticket API endpoints

Implement the endpoints specified in the project plan.

### Create ticket

- [ ]  Implement:

```
POST /tickets
```

- [ ]  Validate customer ID.
- [ ]  Save ticket.
- [ ]  Set initial status to `open`.
- [ ]  Create ticket history entry.
- [ ]  Return HTTP `201`.

### List tickets

- [ ]  Implement:

```
GET /tickets
```

- [ ]  Return all tickets.
- [ ]  Add filtering by status.
- [ ]  Add filtering by category.
- [ ]  Add filtering by priority.
- [ ]  Add filtering by assigned team.
- [ ]  Add pagination if time permits.

### View ticket

- [ ]  Implement:

```
GET /tickets/{ticket_id}
```

- [ ]  Return ticket details.
- [ ]  Return `404` for an invalid ticket ID.

### Update ticket

- [ ]  Implement:

```
PATCH /tickets/{ticket_id}
```

- [ ]  Allow status updates.
- [ ]  Allow priority updates.
- [ ]  Allow team reassignment.
- [ ]  Record every changed field in history.
- [ ]  Update `updated_at`.

### Manual escalation

- [ ]  Implement:

```
POST /tickets/{ticket_id}/escalate
```

- [ ]  Change status to `escalated`.
- [ ]  Accept escalation reason.
- [ ]  Assign Engineering when no team is supplied.
- [ ]  Store escalation in ticket history.
- [ ]  Return updated ticket.

### Ticket history

- [ ]  Implement:

```
GET /tickets/{ticket_id}/history
```

- [ ]  Return history in chronological order.

## 8. Rule-based fallback router

The project plan recommends implementing temporary keyword-based routing before depending on the LLM.

- [ ]  Create `app/services/rule_based_router.py`.
- [ ]  Add billing keywords:
    - [ ]  payment
    - [ ]  charged
    - [ ]  invoice
    - [ ]  subscription
- [ ]  Add refund keywords:
    - [ ]  refund
    - [ ]  money back
    - [ ]  cancel purchase
- [ ]  Add technical keywords:
    - [ ]  API
    - [ ]  error
    - [ ]  crash
    - [ ]  integration
- [ ]  Add account keywords:
    - [ ]  login
    - [ ]  password
    - [ ]  locked
    - [ ]  account
- [ ]  Add feature-request keywords:
    - [ ]  feature
    - [ ]  enhancement
    - [ ]  support for
    - [ ]  would like
- [ ]  Add outage keywords:
    - [ ]  entire service down
    - [ ]  everyone cannot access
    - [ ]  complete outage
- [ ]  Return category, priority, team, and reason.
- [ ]  Make this service callable without the AI module.
- [ ]  Use this service when AI analysis fails.

## 9. AI integration adapter

Teammate 1 should not implement the LLM logic, but should create the backend location where Teammate 2’s service will connect.

- [ ]  Create `app/services/analysis_service.py`.
- [ ]  Define an interface such as:

```
asyncdefanalyze_ticket(ticket,customer):
    ...
```

- [ ]  Temporarily return rule-based results.
- [ ]  Create:

```
POST /tickets/{ticket_id}/analyze
```

- [ ]  Call `analyze_ticket()`.
- [ ]  Save returned values to the ticket.
- [ ]  Add history entries.
- [ ]  Handle AI timeout.
- [ ]  Handle invalid AI output.
- [ ]  Fall back to rule-based routing.
- [ ]  Return a field showing whether AI or fallback was used.

Example:

```
{
  "analysis_source":"ai"
}
```

or:

```
{
  "analysis_source":"rule_based_fallback"
}
```

---

## 10. Backend tests

- [ ]  Test the health endpoint.
- [ ]  Test ticket creation.
- [ ]  Test invalid customer ID.
- [ ]  Test ticket listing.
- [ ]  Test ticket retrieval.
- [ ]  Test ticket update.
- [ ]  Test invalid status update.
- [ ]  Test manual escalation.
- [ ]  Test ticket history.
- [ ]  Test rule-based billing routing.
- [ ]  Test rule-based technical routing.
- [ ]  Test rule-based refund routing.
- [ ]  Test fallback when AI raises an exception.
- [ ]  Use a separate test SQLite database.
- [ ]  Ensure tests do not modify development data.