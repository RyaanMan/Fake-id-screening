from __future__ import annotations

import streamlit as st

from app.ui.api_client import ApiError, analyze_document, audit_log, list_screenings
from app.ui.styles import load_css

ROLE_LABELS = {
    "IMMIGRATION_OFFICER": "Immigration / Check Post Officer",
    "SUPERVISOR": "Senior / Supervisory Officer",
    "AUDITOR": "Audit / Compliance Officer",
    "ADMIN": "System Administrator",
}


def _header() -> None:
    st.markdown(
        """
<div class="dashboard-header">
    <div class="dashboard-brand">NULL FORGERY</div>
    <div class="dashboard-subtitle">NATIONAL IDENTITY &amp; DOCUMENT SCREENING SYSTEM</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        role_label = ROLE_LABELS.get(st.session_state.role, st.session_state.role)
        st.caption(f"AUTHORIZED USER • {st.session_state.username} • {role_label}")
    with col2:
        if st.button("LOG OUT", use_container_width=True):
            for key in ("authenticated", "token", "username", "role"):
                st.session_state.pop(key, None)
            st.rerun()

    st.divider()


def _risk_banner(risk: dict) -> None:
    score = risk["score"]
    level = risk["level"]

    r1, r2 = st.columns(2)
    with r1:
        st.metric("RISK SCORE", f"{score}/100")
    with r2:
        if level == "LOW":
            st.success(f"RISK LEVEL: {level} — {risk['action']}")
        elif level == "MEDIUM":
            st.warning(f"RISK LEVEL: {level} — {risk['action']}")
        else:
            st.error(f"RISK LEVEL: {level} — {risk['action']}")

    st.markdown("### SCREENING REASONS")
    for reason in risk["reasons"]:
        st.write(f"• {reason}")

    st.caption(
        "Risk score is an automated screening indicator and must not be treated as "
        "definitive proof of document fraud or authenticity."
    )


def _screening_desk() -> None:
    st.subheader("OFFICER SCREENING DESK")

    uploaded_file = st.file_uploader("Upload document image", type=["jpg", "jpeg", "png", "webp"])
    document_number = st.text_input("Document number (optional)", placeholder="e.g. DEMO123456")

    if uploaded_file is None:
        st.info("Waiting for document upload.")
        return

    image_bytes = uploaded_file.getvalue()

    preview, information = st.columns(2)
    with preview:
        st.image(image_bytes, caption="Document preview", use_container_width=True)
    with information:
        st.markdown("### FILE INFORMATION")
        st.write(f"**Filename:** {uploaded_file.name}")
        st.write(f"**Type:** {uploaded_file.type}")
        st.write(f"**Size:** {uploaded_file.size:,} bytes")

    if not st.button("RUN SCREENING", type="primary", use_container_width=True):
        return

    try:
        with st.spinner("Running full document screening pipeline..."):
            result = analyze_document(
                st.session_state.token,
                uploaded_file.name,
                image_bytes,
                document_number=document_number,
            )
    except ApiError as exc:
        st.error(f"Screening failed: {exc.detail}")
        return
    except Exception as exc:
        st.error(f"Could not reach the screening API: {exc}")
        return

    st.divider()
    st.subheader("RISK ASSESSMENT")
    _risk_banner(result["risk"])

    st.divider()
    st.subheader("SIGNAL BREAKDOWN")
    a, b, c, d = st.columns(4)
    a.metric("ELA", result["ela"]["score"])
    b.metric("Copy-Move", result["copy_move"]["score"])
    c.metric("Metadata", result["metadata"]["score"])
    d.metric(
        "Blockchain",
        "MATCH" if result["blockchain"].get("match") else "MISMATCH / UNREGISTERED",
    )

    st.markdown("### OCR")
    if result["ocr"].get("text_detected"):
        st.text_area("Extracted text", result["ocr"]["raw_text"], height=150)
    else:
        st.warning("No readable text detected.")

    st.markdown("### MRZ")
    mrz = result["mrz"]
    if not mrz.get("detected"):
        st.info("No probable MRZ detected (expected for non-passport documents).")
    elif mrz.get("valid"):
        st.success("MRZ checksum validation passed.")
    else:
        st.warning("MRZ detected but checksum validation failed — requires review.")

    st.markdown("### FACE")
    face = result["face"]
    if face.get("face_detected"):
        st.success(f"Face detected ({face['faces'][0]['confidence'] * 100:.1f}% confidence).")
        if face.get("quality"):
            st.write(f"Quality: **{face['quality']['quality']}**")
    else:
        st.warning("No face detected.")
    for indicator in face.get("indicators", []):
        st.write(f"• {indicator}")

    st.markdown("### CRYPTOGRAPHIC FINGERPRINT")
    st.code(result["file_hash"])

    st.markdown("### BLOCKCHAIN RECORD")
    st.json(result["blockchain"])

    st.markdown("### REFERENCE DATABASE")
    st.json(result["database"] or {"result": "NO MATCH"})


def _supervisor_view() -> None:
    st.subheader("SUPERVISOR — FLAGGED CASE REVIEW")
    try:
        screenings = list_screenings(st.session_state.token, limit=200)
    except ApiError as exc:
        st.error(f"Could not load screenings: {exc.detail}")
        return

    flagged = [s for s in screenings if s["risk_level"] in {"HIGH", "MEDIUM"}]
    st.write(f"Cases requiring attention: {len(flagged)}")
    st.dataframe(flagged, use_container_width=True)


def _auditor_view() -> None:
    st.subheader("AUDIT / COMPLIANCE VIEW")
    st.caption("Read-only audit trail")
    try:
        logs = audit_log(st.session_state.token, limit=200)
    except ApiError as exc:
        st.error(f"Could not load audit log: {exc.detail}")
        return
    st.dataframe(logs, use_container_width=True)


def _admin_view() -> None:
    st.subheader("SYSTEM ADMINISTRATOR")
    st.write(
        {
            "roles": list(ROLE_LABELS.values()),
            "pii_policy": "Keep PII/document content off-chain",
        }
    )
    st.info(
        "Production authorization should use real institutional IAM/SSO. "
        "New officer accounts can be created via POST /auth/register."
    )
    try:
        logs = audit_log(st.session_state.token, limit=50)
        st.markdown("### Recent audit activity")
        st.dataframe(logs, use_container_width=True)
    except ApiError as exc:
        st.error(f"Could not load audit log: {exc.detail}")


def dashboard_page() -> None:
    load_css()
    _header()

    role = st.session_state.role
    if role == "IMMIGRATION_OFFICER":
        _screening_desk()
    elif role == "SUPERVISOR":
        _supervisor_view()
    elif role == "AUDITOR":
        _auditor_view()
    elif role == "ADMIN":
        _admin_view()
    else:
        st.error(f"Unknown role: {role}")

    st.divider()
    st.caption("NULL FORGERY // GOVERNMENT ACCESS NODE // PROTOTYPE")
