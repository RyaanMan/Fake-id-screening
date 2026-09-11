from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from app.database.db import init_db, recent_audit, seed_demo_data
from app.pipeline import analyze_document

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="MHA Immigration Screening Prototype",
    page_icon="🛂",
    layout="wide",
)

init_db()
seed_demo_data()

ROLE_LABELS = {
    "IMMIGRATION_OFFICER": "Immigration / Check Post Officer",
    "SUPERVISOR": "Senior / Supervisory Officer",
    "AUDITOR": "Audit / Compliance Officer",
    "ADMIN": "System Administrator",
}

st.sidebar.title("Government Screening Prototype")
st.sidebar.caption("Conceptual hackathon UI — simulated government/reference data")
role = st.sidebar.selectbox("Role", list(ROLE_LABELS), format_func=lambda x: ROLE_LABELS[x])
username = st.sidebar.text_input("Operator ID", "demo.officer")

st.title("🛂 AI-Based Fake Identity & Document Screening")
st.caption("AI + Image Forensics + Reference Database + Blockchain")

if role == "IMMIGRATION_OFFICER":
    st.subheader("Officer Screening Desk")
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded = st.file_uploader("Upload document image", type=["jpg", "jpeg", "png", "webp"])
        document_number = st.text_input("Document number", placeholder="e.g. DEMO123456")
    with col2:
        st.markdown("### Officer can see")
        st.write("OCR/MRZ fields, face-match score, ELA, copy-move, metadata, database result, blockchain status, risk and reasons.")
        st.info("Actual OCR/face modules are plugged into the same pipeline later; current prototype uses neutral placeholders for those signals.")

    if uploaded and st.button("Run screening", type="primary"):
        target = BASE_DIR / "data" / "uploads" / uploaded.name
        target.write_bytes(uploaded.getbuffer())
        with st.spinner("Running document screening..."):
            result = analyze_document(
                target,
                username=username,
                role=role,
                document_number=document_number,
            )

        st.image(uploaded, caption="Uploaded document", width=500)

        risk = result["risk"]
        st.metric("Risk Score", f"{risk['score']}/100")
        if risk["level"] == "HIGH":
            st.error(f"HIGH RISK — {risk['action']}")
        elif risk["level"] == "MEDIUM":
            st.warning(f"MEDIUM RISK — {risk['action']}")
        else:
            st.success(f"LOW RISK — {risk['action']}")

        a, b, c, d = st.columns(4)
        a.metric("ELA", result["ela"]["score"])
        b.metric("Copy-Move", result["copy_move"]["score"])
        c.metric("Metadata", result["metadata"]["score"])
        d.metric("Blockchain", "MATCH" if result["blockchain"].get("match") else "MISMATCH / UNREGISTERED")

        st.markdown("### Explainable flags")
        for reason in risk["reasons"]:
            st.write(f"• {reason}")

        st.markdown("### Cryptographic fingerprint")
        st.code(result["file_hash"])

        st.markdown("### Blockchain record")
        st.json(result["blockchain"])

        st.markdown("### Reference database")
        st.json(result["database"] or {"result": "NO MATCH"})

elif role == "SUPERVISOR":
    st.subheader("Supervisor — Flagged Case Review")
    logs = recent_audit(100)
    flagged = [x for x in logs if x["risk_level"] in {"HIGH", "MEDIUM"}]
    st.write(f"Cases requiring attention: {len(flagged)}")
    st.dataframe(flagged, use_container_width=True)

elif role == "AUDITOR":
    st.subheader("Audit / Compliance View")
    st.caption("Read-only prototype audit trail")
    st.dataframe(recent_audit(200), use_container_width=True)

else:
    st.subheader("System Administrator")
    st.write("Prototype administration view")
    st.write({
        "python": os.sys.version,
        "project": str(BASE_DIR),
        "roles": list(ROLE_LABELS.values()),
        "pii_policy": "Keep PII/document content off-chain",
    })
    st.info("Production authorization should use real institutional IAM/SSO. The role selector here is a demo switch, not security.")
