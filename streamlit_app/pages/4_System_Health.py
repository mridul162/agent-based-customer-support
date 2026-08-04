import streamlit as st
from components.metrics import render_health_check
from components.sidebar import render_header_navigation, render_sidebar
from components.styles import apply_styles, render_page_header, status_chip
from services.api_client import ApiClientError, get_api_client

st.set_page_config(page_title="System Health", page_icon="HT", layout="wide")
apply_styles()
render_sidebar()
render_header_navigation()

client = get_api_client()

render_page_header(
    "Health Dashboard",
    "Monitor deployment health at a glance and review the current status of critical dependencies.",
    badge="Monitoring",
)

try:
    health = client.get_health()
    checks = health.get("checks", {})
    status = health.get("status", "unknown")
    tone = "ok" if status == "ok" else "danger"

    with st.container(border=True):
        col_status, col_chip = st.columns([4, 1])
        with col_status:
            st.markdown(
                '<div class="nav-eyebrow">API status</div>', unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="font-family: var(--font-display); font-size:1.3rem; font-weight:600;">{status.upper()}</div>',
                unsafe_allow_html=True,
            )
            st.caption("Current health report from the FastAPI service")
        with col_chip:
            st.markdown(status_chip(status.upper(), tone), unsafe_allow_html=True)

    st.markdown(
        '<div class="nav-eyebrow" style="margin-top:0.8rem;">Dependencies</div>',
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    with columns[0]:
        render_health_check("Database", checks.get("database"))
    with columns[1]:
        render_health_check("OpenAI", checks.get("openai"))
    with columns[2]:
        render_health_check("Vector Index", checks.get("vector_index"))
except ApiClientError as exc:
    st.error(str(exc))
