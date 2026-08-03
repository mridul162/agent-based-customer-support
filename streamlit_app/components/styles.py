import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            max-width: 1180px;
        }
        
        /* 1. Metric Container Card */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            padding: 0.85rem 1.1rem !important;
            border-radius: 8px !important;
            border: 1px solid #e6e8eb !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* 2. Metric Label Styling (Ensures high contrast & visibility) */
        div[data-testid="stMetricLabel"], 
        div[data-testid="stMetricLabel"] p {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            color: #4b5563 !important; /* Visible dark gray on light background */
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            white-space: normal !important;
        }

        /* 3. Metric Value Styling */
        div[data-testid="stMetricValue"], 
        div[data-testid="stMetricValue"] > div {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #111827 !important; /* Solid dark text for values */
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid #e6e8eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
