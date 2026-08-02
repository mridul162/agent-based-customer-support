from typing import Any

import streamlit as st


def render_metric_row(metrics: list[tuple[str, str, str | None]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(columns, metrics):
        column.metric(label, value, help=help_text)


def render_health_check(label: str, check: dict[str, Any] | None) -> None:
    status = (check or {}).get("status", "error")
    detail = (check or {}).get("detail", "No detail available")
    icon = "OK" if status == "ok" else "Attention"
    st.markdown(f"**{label}**")
    st.success(f"{icon}: Healthy") if status == "ok" else st.error(f"{icon}: {detail}")
