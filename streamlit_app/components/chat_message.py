from typing import Any

import streamlit as st

from .styles import status_chip


def render_chat_message(role: str, content: str) -> None:
    is_user = role == "user"
    avatar = "🧑" if is_user else "🤖"
    label = "Customer" if is_user else "Assistant"
    bubble_class = "user" if is_user else "assistant"

    with st.chat_message(avatar):
        st.markdown(
            f'<div class="chat-role-label">{label}</div>', unsafe_allow_html=True
        )
        if isinstance(content, dict):
            st.markdown(
                f'<div class="chat-bubble {bubble_class}">', unsafe_allow_html=True
            )
            st.json(content)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            safe_content = str(content).replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                f'<div class="chat-bubble {bubble_class}">{safe_content}</div>',
                unsafe_allow_html=True,
            )


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

    execution = (
        response.get("execution")
        if isinstance(response.get("execution"), dict)
        else None
    )
    if execution is None:
        execution = (
            response.get("metadata")
            if isinstance(response.get("metadata"), dict)
            else None
        )
    if execution is None:
        execution = (
            response.get("result") if isinstance(response.get("result"), dict) else None
        )
    if execution is None:
        execution = (
            response.get("execution_trace")
            if isinstance(response.get("execution_trace"), dict)
            else None
        )

    agent_name = (
        response.get("agent_name")
        or (execution.get("agent_name") if execution else None)
        or (execution.get("agent") if execution else None)
    )
    tool_used = (
        response.get("tool_used")
        or (execution.get("tool_used") if execution else None)
        or (execution.get("tool") if execution else None)
    )
    latency_ms = (
        response.get("latency_ms")
        or (execution.get("latency_ms") if execution else None)
        or (execution.get("latency") if execution else None)
        or (execution.get("total_duration_ms") if execution else None)
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

    st.markdown(
        '<div class="nav-eyebrow">Execution details</div>', unsafe_allow_html=True
    )

    latency = details.get("latency_ms")
    latency_value = f"{latency:.0f} ms" if isinstance(latency, (int, float)) else "n/a"

    rows = [
        ("Agent selected", details.get("agent_name") or "n/a"),
        ("Tool used", details.get("tool_used") or "none"),
        ("Latency", latency_value),
    ]
    ticket_id = details.get("ticket_id")
    if ticket_id:
        rows.append(("Ticket", str(ticket_id)))

    rows_html = "".join(
        f'<div class="kv-row"><span class="kv-label">{k}</span>'
        f'<span class="kv-value">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(f'<div class="panel-card">{rows_html}</div>', unsafe_allow_html=True)

    needs_human = details.get("needs_human")
    needs_clarification = details.get("needs_clarification")
    if needs_human or needs_clarification:
        chips = ""
        if needs_human:
            chips += status_chip("Needs human support", "warn")
        if needs_clarification:
            chips += " " + status_chip("Needs clarification", "neutral")
        st.markdown(
            f"<div style='margin-top: 0.4rem;'>{chips}</div>", unsafe_allow_html=True
        )
