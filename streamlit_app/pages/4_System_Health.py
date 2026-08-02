import streamlit as st

from components.metrics import render_health_check
from components.sidebar import render_sidebar
from components.styles import apply_styles
from services.api_client import ApiClientError, get_api_client


st.set_page_config(page_title="System Health", page_icon="HT", layout="wide")
apply_styles()
render_sidebar()

client = get_api_client()

st.title("Health Dashboard")
st.caption("Deployment dependency status from `GET /health`.")

try:
    health = client.get_health()
    checks = health.get("checks", {})

    status = health.get("status", "unknown")
    st.metric("API Status", status.upper())

    columns = st.columns(3)
    with columns[0]:
        render_health_check("Database", checks.get("database"))
    with columns[1]:
        render_health_check("OpenAI", checks.get("openai"))
    with columns[2]:
        render_health_check("Vector Index", checks.get("vector_index"))
except ApiClientError as exc:
    st.error(str(exc))
