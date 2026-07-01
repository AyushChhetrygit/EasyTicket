# EasyTicket Project Context

## Overview

EasyTicket is an AI Escalation Orchestrator: a production-inspired multi-agent AI system for SaaS customer support teams.

The goal is not to build another chatbot. EasyTicket should behave more like an intelligent support operations layer that can understand tickets, gather context, retrieve internal knowledge, judge confidence, and either draft a reliable customer response or escalate the issue to the right human team with a complete internal summary.

This project is intended to showcase modern AI engineering practices with an emphasis on reliability, maintainability, and production-style architecture.

## Problem

Customer support teams spend significant time manually:

- reading and interpreting tickets
- classifying intent, urgency, and affected product area
- searching docs and internal knowledge bases
- checking customer context across systems
- reviewing logs or product signals
- routing issues to the right team
- preparing engineering summaries and internal notes

EasyTicket should automate the repetitive parts while keeping humans in control for complex, low-confidence, sensitive, or high-risk cases.

## High-Level Workflow

1. A customer submits a support request.
2. The system performs ticket intake and normalization.
3. The ticket is classified by intent, category, severity, and priority.
4. Customer context is retrieved from connected systems.
5. Relevant documentation and historical knowledge are retrieved.
6. The system evaluates confidence and risk.
7. If confidence is high, it drafts a customer-facing response.
8. If confidence is low, it creates an escalation package for the appropriate human team.
9. Human review, feedback, and outcomes can later be used for evaluation and improvement.

## Planned Agent Architecture

EasyTicket should be composed of specialized agents with clear responsibilities:

- Intent Agent
- Classification Agent
- Priority Agent
- Customer Context Agent
- Knowledge Retrieval Agent
- Response Generation Agent
- Verification Agent
- Escalation Agent
- Human Approval Agent
- Evaluation Agent
- Reflection Agent, future
- Memory Agent, future

The orchestrator should coordinate these agents rather than relying on one large general-purpose prompt.

## Planned MCP Integrations

The architecture should make enterprise integrations replaceable through MCP-style adapters.

Potential integrations include:

- CRM
- Ticketing System
- Knowledge Base
- Billing System
- Product Analytics
- Application Logs
- Slack
- Jira
- Email

Early versions can use mock services and local fixtures. The system should be modular enough to replace those mocks with real integrations later.

## Reliability Principles

EasyTicket should prefer correctness over speed. As the project matures, it should include:

- confidence scoring
- verification before customer-facing responses
- retry mechanisms
- reflection loops
- human approval checkpoints
- structured logging
- agent tracing
- error handling
- evaluation metrics
- cost tracking
- latency monitoring

## Incremental Roadmap

### Version 1

- Ticket intake
- Intent classification
- Knowledge retrieval
- AI-generated response draft

### Version 2

- Multi-agent orchestration
- Customer context retrieval
- Escalation workflow

### Version 3

- MCP integrations
- Evaluation framework
- Human approval workflow
- Observability

### Version 4

- Long-term memory
- Reflection loops
- Self-improving workflows
- Advanced analytics

## Preferred Stack

- Backend: Python and FastAPI
- Agent framework: LangGraph
- LLM: Gemini
- Vector database: Qdrant or Chroma
- Database: PostgreSQL
- Frontend: Next.js
- Deployment: Docker
- Observability: LangSmith, Phoenix, and OpenTelemetry

## Development Philosophy

Requirements are expected to evolve during the early stages. The project should therefore be built incrementally with simple, complete workflow slices.

Design choices should prioritize:

- clear module boundaries
- easy refactoring
- testable agent behavior
- replaceable integrations
- production-style reliability
- recruiter-friendly architecture and documentation

Avoid unnecessary complexity in the MVP. Add abstractions only when they make the system easier to understand, test, or extend.
