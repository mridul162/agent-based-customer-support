import streamlit as st
from components.chat_page import render_chat_page
from components.sidebar import render_header_navigation, render_sidebar
from components.styles import apply_styles

st.set_page_config(
    page_title="Customer Support AI",
    page_icon="CS",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()
render_sidebar()
render_header_navigation()
render_chat_page()
