import streamlit as st


def load_css():
    st.markdown(
        """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 50% 0%,
            #18202d 0%,
            #0d1016 45%,
            #090b10 100%
        );
}

.block-container {
    padding-top: 2.5rem;
    max-width: 1200px;
}

/* Login */

.login-card {
    margin: 45px auto 25px auto;
    padding: 38px 42px 30px 42px;
    background: rgba(18, 23, 32, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.brand {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #f5f7fa;
}

.subtitle {
    text-align: center;
    color: #8f9aaa;
    font-size: 12px;
    letter-spacing: 1.3px;
    margin-top: 7px;
}

div[data-baseweb="input"] {
    background-color: #111722;
}

div[data-baseweb="input"] input {
    color: #f5f7fa;
}

.stButton > button {
    min-height: 44px;
    border-radius: 8px;
    font-weight: 700;
    letter-spacing: 0.4px;
}

.system-status {
    text-align: center;
    margin-top: 25px;
    color: #687486;
    font-size: 11px;
    letter-spacing: 1px;
}

.audit {
    text-align: center;
    margin-top: 32px;
    color: #4f5968;
    font-size: 10px;
    letter-spacing: 1px;
}

/* Dashboard */

.dashboard-header {
    padding: 10px 0 20px 0;
}

.dashboard-brand {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 2.5px;
    color: #f5f7fa;
}

.dashboard-subtitle {
    margin-top: 5px;
    color: #7f8a9b;
    font-size: 11px;
    letter-spacing: 1.2px;
}

/* File uploader */

[data-testid="stFileUploader"] {
    border-radius: 10px;
}

/* Metrics */

[data-testid="stMetric"] {
    background: rgba(18, 23, 32, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px;
    padding: 12px;
}

/* Footer */

.dashboard-footer {
    text-align: center;
    color: #4f5968;
    font-size: 10px;
    letter-spacing: 1px;
}

</style>
        """,
        unsafe_allow_html=True,
    )
