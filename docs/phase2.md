Phase 4: Build the knowledge base and RAG
Duration: 4–6 days
The system should not answer from the model's memory alone.
Create a small fictional knowledge base containing 15–30 documents.
Example documents
How to reset a password
How to restore a missing workspace
Subscription activation troubleshooting
Refund eligibility policy
API authentication errors
Workspace migration errors
Enterprise support SLA
Account suspension policy
RAG pipeline
Knowledge documents
        ↓
Chunking
        ↓
Embeddings
        ↓
Vector database
        ↓
Similarity search
        ↓
Relevant passages
        ↓
LLM-generated response
Recommended starting tools
Chroma for local development
Sentence-transformers or API embeddings
Simple Markdown or text files as the knowledge base
Response requirements
Every generated answer should include:
{
  "answer": "Suggested customer response",
  "sources": [
    "subscription_activation.md"
  ],
  "confidence": 0.84
}
Phase deliverables
Document ingestion script
Chunking pipeline
Vector database
Knowledge search endpoint
Answers with source references
No-answer fallback
Phase 5: Build the escalation decision engine
Duration: 3–5 days
This is the core feature of the project.
The system must decide whether to:
resolve automatically
request more information
escalate to a human
Create an escalation score
Use a combination of signals.
Escalation score =
low retrieval confidence
+ high ticket priority
+ sensitive action
+ repeated customer attempts
+ enterprise customer
+ missing information
+ negative sentiment
Example decision logic
if priority in ["P0", "P1"]:
    escalate = True

elif retrieval_confidence < 0.65:
    escalate = True

elif category == "refund" and refund_amount > approval_limit:
    escalate = True

elif required_information_missing:
    action = "request_information"

else:
    action = "suggest_resolution"
Sensitive actions requiring human approval
Refunds
Account deletion
Subscription cancellation
Security incidents
Data-loss claims
High-value enterprise accounts
Production outages
Phase deliverables
Escalation rules
Confidence thresholds
Sensitive-action rules
Decision reason
Human approval flag
Escalation destination
Phase 6: Generate the escalation packet
Duration: 3–4 days
Do not simply forward the customer message.
Create a structured handoff package for the human agent.
Escalation packet format
{
  "ticket_id": "TICKET-102",
  "customer_summary": {
    "name": "Acme Technologies",
    "plan": "Enterprise",
    "previous_tickets": 2
  },
  "issue_summary": "Workspace disappeared after subscription upgrade.",
  "category": "technical",
  "priority": "P1",
  "business_impact": "Product launch is blocked.",
  "steps_already_attempted": [
    "Checked workspace status",
    "Reviewed account permissions",
    "Searched migration documentation"
  ],
  "knowledge_articles_checked": [
    "workspace_migration_errors.md"
  ],
  "missing_information": [
    "Workspace ID",
    "Approximate time of upgrade"
  ],
  "possible_cause": "Workspace migration job failure",
  "recommended_team": "Engineering",
  "recommended_next_actions": [
    "Check migration job logs",
    "Verify workspace ownership",
    "Retry migration after approval"
  ]
}
Generate two outputs
Internal note
Detailed and technical.
Customer reply
Clear, polite, and non-technical.
Phase deliverables
Engineering-ready summary
Internal note
Customer-facing response
Recommended next actions
Evidence and sources
Missing-information checklist
Phase 7: Convert the workflow into a LangGraph system
Duration: 4–7 days
Only introduce LangGraph after the basic components work independently.
Suggested graph
Ticket Intake
      ↓
Classification
      ↓
Priority Evaluation
      ↓
Customer Context
      ↓
Knowledge Retrieval
      ↓
Response Generation
      ↓
Verification
      ↓
Decision
 ┌────┼─────────┐
 ↓    ↓         ↓
Reply Ask Info Escalate
Suggested workflow state
class TicketState(TypedDict):
    ticket: dict
    classification: dict
    priority: dict
    customer_context: dict
    retrieved_documents: list
    draft_response: str
    confidence: float
    escalation_required: bool
    escalation_packet: dict
    errors: list
Add conditional edges
Examples:
If confidence ≥ threshold → response
If information is missing → ask customer
If risk is high → escalate
If verification fails → retry once
Phase deliverables
LangGraph workflow
Shared state
Conditional routing
Retry path
Failure path
Human approval node