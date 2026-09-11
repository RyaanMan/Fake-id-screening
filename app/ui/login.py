import streamlit as st

from app.ui.styles import load_css


DEMO_OFFICER_ID = "GOV-DEMO-001"
DEMO_PASSWORD = "Null@2026"


def login_page():
    load_css()

    # Header
    st.markdown(
        '<div class="login-card">'
        '<div class="brand">NULL FORGERY</div>'
        '<div class="subtitle">'
        'NATIONAL IDENTITY &amp; DOCUMENT SCREENING SYSTEM'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Security notice — native Streamlit component.
    st.warning("RESTRICTED SYSTEM • AUTHORIZED PERSONNEL ONLY")

    # Credentials
    officer_id = st.text_input(
        "Government Officer ID",
        placeholder="Enter authorized officer ID",
    )

    password = st.text_input(
        "Access Credential",
        type="password",
        placeholder="Enter access credential",
    )

    authenticate = st.button(
        "AUTHENTICATE & ENTER COMMAND CENTER",
        use_container_width=True,
    )

    if authenticate:
        if (
            officer_id.strip() == DEMO_OFFICER_ID
            and password == DEMO_PASSWORD
        ):
            st.session_state.authenticated = True
            st.session_state.officer_id = officer_id.strip()
            st.rerun()
        else:
            st.error("Authentication failed. Access denied.")

    st.markdown(
        '<div class="system-status">'
        '● AUTHENTICATION NODE ONLINE'
        '</div>'
        '<div class="audit">'
        'NULL FORGERY // GOVERNMENT ACCESS NODE // LOCAL PROTOTYPE'
        '</div>',
        unsafe_allow_html=True,
    )
