import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.title("Customer Support AI")
        st.caption("Operations Dashboard")

        st.divider()
        st.markdown("**Navigation**")
        st.page_link("app.py", label="Chat")
        st.page_link("pages/2_Tickets.py", label="Tickets")
        st.page_link("pages/3_Evaluation.py", label="Evaluation")
        st.page_link("pages/4_System_Health.py", label="Health")

        st.divider()
        st.markdown("**Architecture**")
        st.code(
            "Browser\n"
            "  -> Streamlit\n"
            "  -> FastAPI\n"
            "  -> LangGraph\n"
            "  -> Tools\n"
            "  -> Database",
            language="text",
        )
