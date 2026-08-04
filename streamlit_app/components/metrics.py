from typing import Any

import streamlit as st

from .styles import status_chip


def render_metric_row(metrics: list[tuple[str, str, str | None]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(columns, metrics):
        with column:
            st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
            st.metric(label, value, help=help_text)
            st.markdown("</div>", unsafe_allow_html=True)


def render_health_check(label: str, check: dict[str, Any] | None) -> None:
    status = (check or {}).get("status", "error")
    detail = (check or {}).get("detail", "No detail available")
    is_ok = status == "ok"
    tone = "ok" if is_ok else "danger"
    chip = status_chip("Healthy" if is_ok else "Attention", tone)
    border_color = "var(--ok)" if is_ok else "var(--danger)"

    st.markdown(
        f"""
        <div class="panel-card" style="border-left: 3px solid {border_color};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <strong>{label}</strong>
                {chip}
            </div>
            <div style="color: var(--text-muted); font-size: 0.86rem;">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
