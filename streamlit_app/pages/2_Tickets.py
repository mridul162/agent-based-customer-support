import streamlit as st
from components.sidebar import render_header_navigation, render_sidebar
from components.styles import apply_styles, render_page_header, status_chip
from services.api_client import ApiClientError, get_api_client

st.set_page_config(page_title="Tickets", page_icon="TK", layout="wide")
apply_styles()
render_sidebar()
render_header_navigation()

client = get_api_client()

render_page_header(
    "Ticket Viewer",
    "Search by ticket ID and inspect the latest support tickets in a clearer operational layout.",
    badge="Operations",
)


def _status_tone(status: str) -> str:
    normalized = (status or "").lower()
    if normalized in {"open", "pending", "in_progress"}:
        return "warn"
    if normalized in {"resolved", "closed", "done"}:
        return "ok"
    if normalized in {"escalated", "failed"}:
        return "danger"
    return "neutral"


search_col, action_col = st.columns([4, 1])
ticket_id = search_col.text_input(
    "Ticket ID", placeholder="TICKET-ABC12345", label_visibility="collapsed"
)
action_col_ph = action_col.container()
search_clicked = action_col_ph.button(
    "Search", type="primary", use_container_width=True
)

if search_clicked and ticket_id.strip():
    try:
        ticket = client.get_ticket(ticket_id.strip())
        chip = status_chip(ticket["status"], _status_tone(ticket["status"]))
        st.markdown(
            f"""
            <div class="panel-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                    <span class="mono" style="font-weight:600; font-size:1.05rem;">{ticket["ticket_id"]}</span>
                    {chip}
                </div>
                <div style="color: var(--text); margin-bottom:0.6rem;">{ticket["issue"]}</div>
                <div style="color: var(--text-muted); font-size:0.82rem;">Customer: <span class="mono">{ticket["customer_id"]}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except ApiClientError as exc:
        st.error(str(exc))

st.markdown(
    '<div class="nav-eyebrow" style="margin-top:0.8rem;">Recent tickets</div>',
    unsafe_allow_html=True,
)

try:
    tickets = client.list_tickets(limit=20)
    if tickets:
        for ticket in tickets:
            chip = status_chip(ticket["status"], _status_tone(ticket["status"]))
            st.markdown(
                f"""
                <div class="panel-card" style="margin-bottom:0.6rem;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;">
                        <div>
                            <div class="mono" style="font-weight:600;">{ticket["ticket_id"]}</div>
                            <div style="color: var(--text-muted); font-size:0.8rem; margin-top:0.15rem;">{ticket["customer_id"]}</div>
                        </div>
                        {chip}
                    </div>
                    <div style="color: var(--text); margin-top:0.6rem; font-size:0.9rem;">{ticket["issue"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="panel-card" style="text-align:center; padding: 2rem 1rem; color: var(--text-muted);">
                No tickets found yet.
            </div>
            """,
            unsafe_allow_html=True,
        )
except ApiClientError as exc:
    st.error(str(exc))
