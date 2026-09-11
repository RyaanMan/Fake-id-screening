from __future__ import annotations

import streamlit as st

from app.ui.dashboard import dashboard_page
from app.ui.login import login_page

st.set_page_config(
    page_title="NULL FORGERY — Document Screening",
    page_icon="🛂",
    layout="wide",
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    dashboard_page()
else:
    login_page()
