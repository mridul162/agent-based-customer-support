from typing import Any

import streamlit as st


def render_chat_message(role: str, content: str) -> None:
    avatar = "user" if role == "user" else "assistant"
    label = "Customer" if role == "user" else "Assistant"
    with st.chat_message(avatar):
        st.markdown(f"**{label}**")
        if isinstance(content, dict):
            st.json(content)
        else:
            st.write(content)


def extract_execution_details(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {
            "agent_name": None,
            "tool_used": None,
            "latency_ms": None,
            "ticket_id": None,
            "needs_human": None,
            "needs_clarification": None,
        }

    execution = response.get("execution") if isinstance(response.get("execution"), dict) else None
    if execution is None:
        execution = response.get("metadata") if isinstance(response.get("metadata"), dict) else None
    if execution is None:
        execution = response.get("result") if isinstance(response.get("result"), dict) else None
    if execution is None:
        execution = response.get("execution_trace") if isinstance(response.get("execution_trace"), dict) else None

    agent_name = response.get("agent_name") or (
        execution.get("agent_name") if execution else None
    ) or (
        execution.get("agent") if execution else None
    )
    tool_used = response.get("tool_used") or (
        execution.get("tool_used") if execution else None
    ) or (
        execution.get("tool") if execution else None
    )
    latency_ms = response.get("latency_ms") or (
        execution.get("latency_ms") if execution else None
    ) or (
        execution.get("latency") if execution else None
    ) or (
        execution.get("total_duration_ms") if execution else None
    )

    return {
        "agent_name": agent_name,
        "tool_used": tool_used,
        "latency_ms": latency_ms,
        "ticket_id": response.get("ticket_id"),
        "needs_human": response.get("needs_human"),
        "needs_clarification": response.get("needs_clarification"),
    }


def render_trace_panel(response: dict) -> None:
    details = extract_execution_details(response)
    
    st.subheader("Execution Details")

    latency = details.get("latency_ms")
    latency_value = f"{latency:.0f} ms" if isinstance(latency, (int, float)) else "n/a"

    # Stacked vertically to ensure full readability inside narrow side panels
    st.metric("Agent Selected", details.get("agent_name") or "n/a")
    st.metric("Tool Used", details.get("tool_used") or "none")
    st.metric("Latency", latency_value)

    ticket_id = details.get("ticket_id")
    if ticket_id:
        st.metric("Ticket", str(ticket_id))

    needs_human = details.get("needs_human")
    needs_clarification = details.get("needs_clarification")
    if needs_human or needs_clarification:
        status_parts = []
        if needs_human:
            status_parts.append("⚠️ Needs human support")
        if needs_clarification:
            status_parts.append("❓ Needs clarification")
        st.warning(" • ".join(status_parts))