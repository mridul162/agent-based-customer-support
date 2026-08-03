import streamlit as st

from components.chat_message import render_chat_message, render_trace_panel
from services.api_client import ApiClientError, get_api_client


def render_chat_page() -> None:
    client = get_api_client()

    st.title("Customer Chat")
    st.caption("Live support workflow powered by the FastAPI service.")

    if "chat_customer_id" not in st.session_state:
        st.session_state.chat_customer_id = "CUST-001"
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

    with st.form("message_form", clear_on_submit=True):
        customer_id = st.text_input("Customer ID", value=st.session_state.chat_customer_id)
        message = st.text_area(
            "Message",
            height=120,
        )
        col_send, col_history = st.columns([1, 5])
        send_clicked = col_send.form_submit_button("Send", type="primary")
        history_clicked = col_history.form_submit_button("Load History")

    if customer_id != st.session_state.chat_customer_id:
        st.session_state.chat_customer_id = customer_id
        load_history(customer_id)

    if history_clicked:
        load_history(customer_id)

    if send_clicked and message.strip():
        try:
            response = client.send_message(customer_id=customer_id.strip(), message=message.strip())
            response_payload = response if isinstance(response, dict) else {"response": str(response)}
            st.session_state.last_response = response_payload
            st.session_state.chat_messages.append({"role": "user", "content": message.strip()})
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": response_payload.get("response", "")}
            )
        except ApiClientError as exc:
            st.error(str(exc))

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("Conversation")
        if not st.session_state.chat_messages:
            st.info("No conversation loaded yet.")
        for chat_message in st.session_state.chat_messages:
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
            st.subheader("Execution Details")
            st.write("Send a message to inspect routing, tool use, and latency.")
