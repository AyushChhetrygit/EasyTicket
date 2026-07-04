"""Streamlit frontend for EasyTicket."""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

BACKEND_BASE_URL = os.getenv("EASYTICKET_BACKEND_URL", "http://localhost:8000")
CUSTOMERS = {
    "CUST-1001 Enterprise": {"customer_id": "CUST-1001", "plan": "enterprise"},
    "CUST-1002 Pro": {"customer_id": "CUST-1002", "plan": "pro"},
    "CUST-1003 Free": {"customer_id": "CUST-1003", "plan": "free"},
}


def api_request(method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
    try:
        response = httpx.request(
            method,
            f"{BACKEND_BASE_URL}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        detail = error.response.text
        raise RuntimeError(f"Backend error {error.response.status_code}: {detail}") from error
    except httpx.RequestError as error:
        raise RuntimeError(f"Could not reach backend: {error}") from error


def create_ticket_page() -> None:
    st.header("Create Ticket")
    customer_label = st.selectbox("Customer", list(CUSTOMERS))
    message = st.text_area("Ticket message", height=140)

    if st.button("Create Ticket", type="primary"):
        payload = {
            "customer_id": CUSTOMERS[customer_label]["customer_id"],
            "message": message,
        }
        try:
            ticket = api_request("POST", "/tickets", json=payload)
            st.session_state["active_ticket_id"] = ticket.get("ticket_id") or ticket.get("id")
            st.success(f"Created ticket: {st.session_state['active_ticket_id']}")
        except RuntimeError as error:
            st.error(str(error))

    ticket_id = st.text_input("Ticket ID", value=st.session_state.get("active_ticket_id", ""))
    if st.button("Analyze Ticket") and ticket_id:
        with st.spinner("Analyzing ticket..."):
            try:
                result = api_request("POST", f"/tickets/{ticket_id}/analyze")
                st.subheader("AI Analysis")
                st.write("Category:", result.get("category"))
                st.write("Subcategory:", result.get("subcategory"))
                st.write("Confidence:", result.get("classification_confidence"))
                st.write("Priority:", result.get("priority"))
                st.write("Assigned team:", result.get("assigned_team"))
                st.write("Reason:", result.get("ai_reason"))
                st.write("Analysis source:", result.get("analysis_source", "backend"))
            except RuntimeError as error:
                st.error(str(error))


def ticket_list_page() -> None:
    st.header("Tickets")
    status = st.selectbox("Status", ["all", "new", "open", "in_progress", "resolved", "escalated", "closed"])
    priority = st.selectbox("Priority", ["all", "low", "medium", "high", "urgent"])
    team = st.selectbox(
        "Team",
        ["all", "tier1_support", "tier2_support", "billing_team", "engineering", "account_management"],
    )
    params = {
        k: v
        for k, v in {"status": status, "priority": priority, "assigned_team": team}.items()
        if v != "all"
    }

    try:
        tickets = api_request("GET", "/tickets", params=params)
        st.dataframe(tickets, use_container_width=True)
    except RuntimeError as error:
        st.error(str(error))


def ticket_details_page() -> None:
    st.header("Ticket Details")
    ticket_id = st.text_input("Ticket ID for details")
    if not ticket_id:
        return

    try:
        ticket = api_request("GET", f"/tickets/{ticket_id}")
        st.json(ticket)
    except RuntimeError as error:
        st.error(str(error))
        return

    status = st.selectbox("Update status", ["open", "in_progress", "resolved", "escalated"])
    if st.button("Update Status"):
        try:
            api_request("PATCH", f"/tickets/{ticket_id}", json={"status": status})
            st.success("Status updated.")
        except RuntimeError as error:
            st.error(str(error))

    st.subheader("Manual Escalation")
    team = st.selectbox("Escalation team", ["engineering", "billing_team", "tier1_support", "tier2_support", "account_management"])
    reason = st.text_area("Escalation reason")
    if st.button("Escalate"):
        try:
            api_request("POST", f"/tickets/{ticket_id}/escalate", json={"team": team, "reason": reason})
            st.success("Ticket escalated.")
        except RuntimeError as error:
            st.error(str(error))

    st.subheader("History")
    try:
        history = api_request("GET", f"/tickets/{ticket_id}/history")
        st.dataframe(history, use_container_width=True)
    except RuntimeError as error:
        st.error(str(error))


def main() -> None:
    st.set_page_config(page_title="EasyTicket", layout="wide")
    st.sidebar.caption(f"Backend: {BACKEND_BASE_URL}")
    page = st.sidebar.radio("Page", ["Create Ticket", "Tickets", "Ticket Details"])
    if page == "Create Ticket":
        create_ticket_page()
    elif page == "Tickets":
        ticket_list_page()
    else:
        ticket_details_page()


if __name__ == "__main__":
    main()
