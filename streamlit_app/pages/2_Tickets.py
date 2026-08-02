import streamlit as st

from components.sidebar import render_sidebar
from components.styles import apply_styles
from services.api_client import ApiClientError, get_api_client


st.set_page_config(page_title="Tickets", page_icon="TK", layout="wide")
apply_styles()
render_sidebar()

client = get_api_client()

st.title("Ticket Viewer")
st.caption("Search a ticket by ID or inspect recent tickets from the API.")

search_col, action_col = st.columns([4, 1])
ticket_id = search_col.text_input("Ticket ID", placeholder="TICKET-ABC12345")
search_clicked = action_col.button("Search", type="primary", use_container_width=True)

if search_clicked and ticket_id.strip():
    try:
        ticket = client.get_ticket(ticket_id.strip())
        st.subheader(ticket["ticket_id"])
        st.write(ticket["issue"])
        st.metric("Status", ticket["status"])
        st.caption(f"Customer: {ticket['customer_id']}")
    except ApiClientError as exc:
        st.error(str(exc))

st.divider()
st.subheader("Recent Tickets")

try:
    tickets = client.list_tickets(limit=20)
    if tickets:
        for ticket in tickets:
            with st.container(border=True):
                cols = st.columns([2, 2, 1])
                cols[0].markdown(f"**{ticket['ticket_id']}**")
                cols[0].caption(ticket["customer_id"])
                cols[1].write(ticket["issue"])
                cols[2].metric("Status", ticket["status"])
    else:
        st.info("No tickets found yet.")
except ApiClientError as exc:
    st.error(str(exc))
