"""LangGraph orchestration for ticket RAG, decision, and escalation flow."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.services.customer_reply_service import generate_customer_reply
from app.services.escalation_decision_service import decide_escalation
from app.services.escalation_packet_service import generate_escalation_packet
from app.services.missing_information_service import detect_missing_information
from app.services.rag_search_service import search_knowledge_base
from app.services.response_generation_service import generate_rag_answer
from app.services.rule_based_router import classify_ticket

CONFIDENCE_THRESHOLD = 0.65
WORKFLOW_RETRIEVAL_THRESHOLD = 0.55
ENGINEERING_RISK_TERMS = ("security", "breach", "compromise", "data leak", "unauthorized")
NO_ANSWER_FALLBACK = (
    "I do not have enough verified information to answer this safely. "
    "A support agent should review this ticket."
)


class TicketState(TypedDict, total=False):
    ticket: dict[str, Any]
    classification: str
    priority: str
    customer_context: dict[str, Any]
    retrieved_documents: list[dict[str, Any]]
    draft_response: str
    confidence: float
    escalation_required: bool
    escalation_packet: dict[str, Any]
    errors: list[str]
    missing_information: list[str]
    final_action: str
    retry_count: int
    verification_passed: bool
    verification_reason: str
    destination_team: str
    sensitive_action: bool
    human_approval_required: bool


def ticket_intake_node(state: TicketState) -> TicketState:
    ticket = state.get("ticket") or {}
    message = str(ticket.get("message", "")).strip()
    if not message:
        return {"errors": _append_error(state, "Ticket message is required.")}
    return {"ticket": {**ticket, "message": message}, "retry_count": state.get("retry_count", 0)}


def classification_node(state: TicketState) -> TicketState:
    result = classify_ticket(_ticket_message(state))
    return {
        "classification": result.category.value,
        "destination_team": result.assigned_team.value,
    }


def priority_evaluation_node(state: TicketState) -> TicketState:
    result = classify_ticket(_ticket_message(state))
    return {"priority": result.priority.value}


def customer_context_node(state: TicketState) -> TicketState:
    customer = state.get("customer_context") or {}
    return {
        "customer_context": {
            "customer_id": customer.get("customer_id", "UNKNOWN"),
            "name": customer.get("name", "Unknown Customer"),
            "plan": customer.get("plan", "free"),
            "account_status": customer.get("account_status", "active"),
            "previous_tickets": customer.get("previous_tickets", 0),
        }
    }


def knowledge_retrieval_node(state: TicketState) -> TicketState:
    rag_result = search_knowledge_base(
        _ticket_message(state),
        confidence_threshold=WORKFLOW_RETRIEVAL_THRESHOLD,
    )
    documents = [
        {"source": source, "passage": passage}
        for source, passage in zip(rag_result.sources, rag_result.passages)
    ]
    return {
        "retrieved_documents": documents,
        "confidence": rag_result.confidence,
    }


def response_generation_node(state: TicketState) -> TicketState:
    rag_answer = generate_rag_answer(
        _ticket_message(state),
        state.get("customer_context"),
        _rag_result_from_state(state),
    )
    return {"draft_response": rag_answer.answer}


def verification_node(state: TicketState) -> TicketState:
    if state.get("errors"):
        return {"verification_passed": False, "verification_reason": "State contains errors."}

    documents = state.get("retrieved_documents") or []
    draft = state.get("draft_response", "")
    if not documents:
        return _verification_failed(state, "Generated answer has no retrieved sources.")
    if not draft:
        return _verification_failed(state, "Generated answer is empty.")
    if state.get("confidence", 0.0) < WORKFLOW_RETRIEVAL_THRESHOLD:
        return _verification_failed(state, "Retrieval confidence is below workflow threshold.")

    return {"verification_passed": True, "verification_reason": "Answer has sources and non-zero confidence."}


def decision_node(state: TicketState) -> TicketState:
    missing = detect_missing_information(_ticket_message(state), state.get("classification"))
    decision = decide_escalation(
        ticket_message=_ticket_message(state),
        category=state.get("classification"),
        priority=state.get("priority"),
        assigned_team=_decision_team(state),
        retrieval_confidence=state.get("confidence", 0.0),
        customer_context=state.get("customer_context"),
        missing_information=missing,
    )
    return {
        "missing_information": missing,
        "escalation_required": decision.escalation_required,
        "destination_team": decision.destination_team,
        "sensitive_action": decision.sensitive_action,
        "human_approval_required": decision.human_approval_required,
        "final_action": decision.action,
    }


def reply_node(state: TicketState) -> TicketState:
    return {"final_action": "reply", "escalation_required": False}


def ask_information_node(state: TicketState) -> TicketState:
    decision = _decision_from_state(state, action="request_information")
    reply = generate_customer_reply(
        rag_answer=_rag_answer_from_state(state),
        missing_information=state.get("missing_information", []),
        escalation_decision=decision,
    )
    return {"final_action": "ask_information", "draft_response": reply}


def escalation_node(state: TicketState) -> TicketState:
    packet = _build_packet(state)
    return {
        "final_action": "escalate",
        "escalation_required": True,
        "escalation_packet": packet.model_dump(),
        "draft_response": packet.customer_reply,
    }


def human_approval_node(state: TicketState) -> TicketState:
    packet = _build_packet(state)
    return {
        "final_action": "human_approval_required",
        "escalation_required": True,
        "escalation_packet": packet.model_dump(),
        "draft_response": packet.customer_reply,
    }


def failure_node(state: TicketState) -> TicketState:
    return {
        "final_action": "failure",
        "draft_response": NO_ANSWER_FALLBACK,
        "verification_passed": False,
    }


def route_after_verification(state: TicketState) -> Literal["retry", "decision", "failure"]:
    if state.get("errors"):
        return "failure"
    if state.get("verification_passed"):
        return "decision"
    if state.get("retry_count", 0) < 1:
        return "retry"
    return "failure"


def route_after_decision(
    state: TicketState,
) -> Literal["ask_information", "human_approval", "escalation", "reply", "failure"]:
    if state.get("errors"):
        return "failure"
    if state.get("missing_information"):
        return "ask_information"
    if state.get("sensitive_action") or state.get("human_approval_required"):
        return "human_approval"
    if state.get("escalation_required"):
        return "escalation"
    if state.get("confidence", 0.0) >= CONFIDENCE_THRESHOLD:
        return "reply"
    return "failure"


def build_ticket_workflow():
    graph = StateGraph(TicketState)
    graph.add_node("ticket_intake_node", ticket_intake_node)
    graph.add_node("classification_node", classification_node)
    graph.add_node("priority_evaluation_node", priority_evaluation_node)
    graph.add_node("customer_context_node", customer_context_node)
    graph.add_node("knowledge_retrieval_node", knowledge_retrieval_node)
    graph.add_node("response_generation_node", response_generation_node)
    graph.add_node("verification_node", verification_node)
    graph.add_node("decision_node", decision_node)
    graph.add_node("reply_node", reply_node)
    graph.add_node("ask_information_node", ask_information_node)
    graph.add_node("escalation_node", escalation_node)
    graph.add_node("human_approval_node", human_approval_node)
    graph.add_node("failure_node", failure_node)

    graph.set_entry_point("ticket_intake_node")
    graph.add_edge("ticket_intake_node", "classification_node")
    graph.add_edge("classification_node", "priority_evaluation_node")
    graph.add_edge("priority_evaluation_node", "customer_context_node")
    graph.add_edge("customer_context_node", "knowledge_retrieval_node")
    graph.add_edge("knowledge_retrieval_node", "response_generation_node")
    graph.add_edge("response_generation_node", "verification_node")
    graph.add_conditional_edges(
        "verification_node",
        route_after_verification,
        {
            "retry": "knowledge_retrieval_node",
            "decision": "decision_node",
            "failure": "failure_node",
        },
    )
    graph.add_conditional_edges(
        "decision_node",
        route_after_decision,
        {
            "ask_information": "ask_information_node",
            "human_approval": "human_approval_node",
            "escalation": "escalation_node",
            "reply": "reply_node",
            "failure": "failure_node",
        },
    )
    graph.add_edge("reply_node", END)
    graph.add_edge("ask_information_node", END)
    graph.add_edge("escalation_node", END)
    graph.add_edge("human_approval_node", END)
    graph.add_edge("failure_node", END)
    return graph.compile()


def _ticket_message(state: TicketState) -> str:
    return str((state.get("ticket") or {}).get("message", ""))


def _append_error(state: TicketState, message: str) -> list[str]:
    return [*(state.get("errors") or []), message]


def _decision_team(state: TicketState) -> str | None:
    message = _ticket_message(state).lower()
    if any(term in message for term in ENGINEERING_RISK_TERMS):
        return None
    return state.get("destination_team")


def _verification_failed(state: TicketState, reason: str) -> TicketState:
    return {
        "verification_passed": False,
        "verification_reason": reason,
        "retry_count": state.get("retry_count", 0) + 1,
    }


def _rag_result_from_state(state: TicketState):
    from app.services.rag_search_service import RagSearchResult

    documents = state.get("retrieved_documents") or []
    return RagSearchResult(
        passages=[str(doc.get("passage", "")) for doc in documents],
        sources=[str(doc.get("source", "")) for doc in documents],
        confidence=state.get("confidence", 0.0),
        has_answer=bool(documents),
    )


def _rag_answer_from_state(state: TicketState):
    from app.services.response_generation_service import RagAnswer

    return RagAnswer(
        answer=state.get("draft_response", ""),
        sources=[doc["source"] for doc in state.get("retrieved_documents", [])],
        confidence=state.get("confidence", 0.0),
        should_escalate=state.get("escalation_required", False),
    )


def _decision_from_state(state: TicketState, *, action: str):
    from app.models.escalation_schemas import EscalationDecision

    return EscalationDecision(
        action=action,
        escalation_required=state.get("escalation_required", False),
        escalation_score=1.0 if state.get("escalation_required") else 0.0,
        human_approval_required=state.get("human_approval_required", False),
        sensitive_action=state.get("sensitive_action", False),
        destination_team=state.get("destination_team", "tier1_support"),
        reason="LangGraph workflow decision.",
        missing_information=state.get("missing_information", []),
    )


def _build_packet(state: TicketState):
    ticket = state.get("ticket") or {}
    customer = state.get("customer_context") or {}
    return generate_escalation_packet(
        ticket=SimpleNamespace(
            ticket_id=ticket.get("ticket_id", "TKT-LANGGRAPH"),
            customer_id=ticket.get("customer_id", customer.get("customer_id", "UNKNOWN")),
            message=ticket.get("message", ""),
        ),
        customer=SimpleNamespace(
            customer_id=customer.get("customer_id", "UNKNOWN"),
            name=customer.get("name", "Unknown Customer"),
            plan=customer.get("plan", "free"),
            account_status=customer.get("account_status", "active"),
            previous_tickets=customer.get("previous_tickets", 0),
        ),
        classification=state.get("classification", "general"),
        priority=state.get("priority", "low"),
        rag_result=_rag_result_from_state(state),
        escalation_decision=_decision_from_state(
            state,
            action="escalate_to_human" if state.get("escalation_required") else "suggest_resolution",
        ),
        rag_answer=_rag_answer_from_state(state),
    )
