import streamlit as st
from services.api_client import ApiClientError, get_api_client

from .chat_message import (
    render_chat_message,
    render_trace_panel,
)
from .styles import render_page_header


def render_chat_page() -> None:
    client = get_api_client()

    render_page_header(
        "Customer Chat",
        "Review the live support workflow and inspect the execution path behind every reply.",
        badge="Live support",
    )

    if "chat_customer_id" not in st.session_state:
        st.session_state.chat_customer_id = "CUST-XXX"
    else:
        st.session_state.chat_customer_id = st.session_state.chat_customer_id
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    def load_history(customer_id: str) -> None:
        try:
            history = client.get_conversation(customer_id)
            st.session_state.chat_messages = history.get("messages", [])
        except ApiClientError as exc:
            st.warning(str(exc))

    summary_cols = st.columns(3)
    summary_cols[0].metric("Customer", st.session_state.chat_customer_id)
    summary_cols[1].metric("Messages", len(st.session_state.chat_messages))
    summary_cols[2].metric(
        "Latest agent",
        st.session_state.last_response.get("agent_name", "—")
        if st.session_state.last_response
        else "—",
    )

    with (
        st.container(border=True),
        st.form("message_form", clear_on_submit=True),
    ):
        customer_id = st.text_input(
            "Customer ID", value=st.session_state.chat_customer_id
        )
        message = st.text_area(
            "Message", height=120, placeholder="Type the customer's message…"
        )
        col_send, col_history = st.columns([1, 5])
        send_clicked = col_send.form_submit_button(
            "Send", type="primary", use_container_width=True
        )
        history_clicked = col_history.form_submit_button("Load history")

    if customer_id != st.session_state.chat_customer_id:
        st.session_state.chat_customer_id = customer_id
        load_history(customer_id)

    if history_clicked:
        load_history(customer_id)

    if send_clicked and message.strip():
        with st.spinner("Routing message through the agent graph…"):
            try:
                response = client.send_message(
                    customer_id=customer_id.strip(), message=message.strip()
                )
                response_payload = (
                    response
                    if isinstance(response, dict)
                    else {"response": str(response)}
                )
                st.session_state.last_response = response_payload
                st.session_state.chat_messages.append(
                    {"role": "user", "content": message.strip()}
                )
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": response_payload.get("response", ""),
                    }
                )
            except ApiClientError as exc:
                st.error(str(exc))

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.markdown(
            '<div class="nav-eyebrow">Conversation</div>', unsafe_allow_html=True
        )
        if not st.session_state.chat_messages:
            st.markdown(
                """
                <div class="panel-card" style="text-align:center; padding: 2.2rem 1rem;">
                    <div style="font-size:1.6rem;">💬</div>
                    <div style="margin-top:0.5rem; font-weight:600;">No conversation loaded yet</div>
                    <div style="color: var(--text-muted); font-size:0.86rem; margin-top:0.25rem;">
                        Send a message above or load history for this customer to populate the thread.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        for chat_message in st.session_state.chat_messages:
            with st.container(border=True):
                render_chat_message(
                    role=chat_message.get("role", "assistant"),
                    content=chat_message.get("content", ""),
                )

    with right:
        if st.session_state.last_response:
            render_trace_panel(st.session_state.last_response)
            ticket_id = st.session_state.last_response.get("ticket_id")
            if ticket_id:
                st.info(f"Ticket created or referenced: {ticket_id}")
        else:
            st.markdown(
                """
                <div class="panel-card">
                    <div class="nav-eyebrow" style="margin-bottom:0.6rem;">Execution details</div>
                    <div style="color: var(--text-muted); font-size:0.88rem;">
                        Send a message to inspect routing, tool use, and latency.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
