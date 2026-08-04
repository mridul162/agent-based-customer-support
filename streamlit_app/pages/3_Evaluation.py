import streamlit as st
from components.metrics import render_metric_row
from components.sidebar import render_header_navigation, render_sidebar
from components.styles import apply_styles, render_page_header, status_chip
from services.api_client import ApiClientError, get_api_client

st.set_page_config(page_title="Evaluation", page_icon="EV", layout="wide")
apply_styles()
render_sidebar()
render_header_navigation()

client = get_api_client()

render_page_header(
    "Evaluation Dashboard",
    "Track the latest evaluation summary and quality metrics in a more readable format.",
    badge="Insights",
)

try:
    summary = client.get_evaluation_summary()
    accuracy = float(summary.get("accuracy", 0))
    passed = int(summary.get("passed_cases", 0))
    total = int(summary.get("total_cases", 0))
    failed = int(summary.get("failed_cases", 0))

    render_metric_row(
        [
            ("Accuracy", f"{accuracy:.0f}%", "Share of evaluation cases that passed."),
            ("Pass rate", f"{passed} / {total}", "Passed cases over total cases."),
            ("Failures", str(failed), "Evaluation cases that failed."),
        ]
    )

    if accuracy >= 90:
        tone, label = "ok", "On target"
    elif accuracy >= 75:
        tone, label = "warn", "Needs attention"
    else:
        tone, label = "danger", "Below threshold"

    st.markdown(
        '<div class="nav-eyebrow" style="margin-top:0.4rem;">Performance overview</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        header_col, chip_col = st.columns([4, 1])
        header_col.write("Latest quality signal from the evaluation pipeline.")
        chip_col.markdown(status_chip(label, tone), unsafe_allow_html=True)
        st.progress(min(max(accuracy / 100, 0), 1))
        st.caption(f"Source: {summary.get('source', 'unknown')}")
except ApiClientError as exc:
    st.error(str(exc))
