# EasyTicket

EasyTicket is a production-inspired AI escalation orchestrator for SaaS customer support teams. It is designed to automate the repetitive parts of support escalation: understanding incoming tickets, classifying intent and priority, retrieving customer and knowledge-base context, deciding whether AI can respond confidently, and preparing engineering-ready escalation packages when human help is needed.

The project is intentionally being built incrementally. Early requirements may change as the system takes shape, so the architecture should stay modular, understandable, and easy to refactor.

## Current Direction

- Backend: Python and FastAPI
- Agent orchestration: LangGraph
- LLM: Gemini
- Retrieval: Qdrant or Chroma
- Database: PostgreSQL
- Frontend: Next.js
- Deployment: Docker
- Observability: LangSmith, Phoenix, and OpenTelemetry

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for the full project context and roadmap.
