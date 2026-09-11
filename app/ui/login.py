from __future__ import annotations

import streamlit as st

from app.ui.api_client import ApiError, login
from app.ui.styles import load_css


def login_page() -> None:
    load_css()

    st.markdown(
        '<div class="login-card">'
        '<div class="brand">NULL FORGERY</div>'
        '<div class="subtitle">'
        "NATIONAL IDENTITY &amp; DOCUMENT SCREENING SYSTEM"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.warning("RESTRICTED SYSTEM • AUTHORIZED PERSONNEL ONLY")

    username = st.text_input("Officer Username", placeholder="Enter authorized username")
    password = st.text_input("Access Credential", type="password", placeholder="Enter access credential")

    authenticate = st.button("AUTHENTICATE & ENTER COMMAND CENTER", use_container_width=True)

    if authenticate:
        try:
            with st.spinner("Authenticating..."):
                result = login(username.strip(), password)
        except ApiError as exc:
            st.error(f"Authentication failed: {exc.detail}")
        except Exception as exc:
            st.error(f"Could not reach the screening API: {exc}")
        else:
            st.session_state.authenticated = True
            st.session_state.token = result["access_token"]
            st.session_state.username = result["username"]
            st.session_state.role = result["role"]
            st.rerun()

    st.markdown(
        '<div class="system-status">● AUTHENTICATION NODE ONLINE</div>'
        '<div class="audit">NULL FORGERY // GOVERNMENT ACCESS NODE // PROTOTYPE</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Demo accounts (seeded on first backend startup)"):
        st.code(
            "admin / Admin@2026\n"
            "demo.officer / Officer@2026\n"
            "demo.supervisor / Supervisor@2026\n"
            "demo.auditor / Auditor@2026",
        )
