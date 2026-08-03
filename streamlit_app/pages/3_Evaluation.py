import streamlit as st
from components.metrics import render_metric_row
from components.sidebar import render_sidebar
from components.styles import apply_styles
from services.api_client import ApiClientError, get_api_client

st.set_page_config(page_title="Evaluation", page_icon="EV", layout="wide")
apply_styles()
render_sidebar()

client = get_api_client()

st.title("Evaluation Dashboard")
st.caption("Latest evaluation summary served by FastAPI.")

try:
    summary = client.get_evaluation_summary()
    accuracy = float(summary.get("accuracy", 0))
    passed = int(summary.get("passed_cases", 0))
    total = int(summary.get("total_cases", 0))
    failed = int(summary.get("failed_cases", 0))

    render_metric_row(
        [
            ("Accuracy", f"{accuracy:.0f}%", "Share of evaluation cases that passed."),
            ("Pass Rate", f"{passed} / {total}", "Passed cases over total cases."),
            ("Failures", str(failed), "Evaluation cases that failed."),
        ]
    )

    st.progress(min(max(accuracy / 100, 0), 1))
    st.caption(f"Source: {summary.get('source', 'unknown')}")
except ApiClientError as exc:
    st.error(str(exc))
