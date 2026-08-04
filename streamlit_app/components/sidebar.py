import streamlit as st

NAV_ITEMS = [
    ("Chat", "app.py"),
    ("Tickets", "pages/2_Tickets.py"),
    ("Evaluation", "pages/3_Evaluation.py"),
    ("Health", "pages/4_System_Health.py"),
]

TRACE_STEPS = [
    "Browser",
    "Streamlit UI",
    "FastAPI",
    "Router Graph",
    "Specialist Agent",
    "Tools & Escalation",
    "Database",
]


def render_navigation_links() -> None:
    for label, target in NAV_ITEMS:
        st.page_link(target, label=label)


def render_header_navigation() -> None:
    st.markdown('<div class="top-nav-bar">', unsafe_allow_html=True)
    cols = st.columns(len(NAV_ITEMS))
    for col, (label, target) in zip(cols, NAV_ITEMS):
        with col:
            st.page_link(target, label=label, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-block">
                <div class="brand-mark"><span class="brand-dot"></span>Live operations</div>
                <div class="brand-title">Customer Support Platform</div>
                <div class="brand-subtitle">Multi-Agent Support Console</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nav-eyebrow">Navigate</div>', unsafe_allow_html=True)
        render_navigation_links()

        st.markdown(
            '<div class="nav-eyebrow" style="margin-top:1.4rem;">Request pipeline</div>',
            unsafe_allow_html=True,
        )
        nodes = "".join(
            f'<div class="trace-node"><span>{step}</span></div>' for step in TRACE_STEPS
        )
        st.markdown(f'<div class="trace-rail">{nodes}</div>', unsafe_allow_html=True)
