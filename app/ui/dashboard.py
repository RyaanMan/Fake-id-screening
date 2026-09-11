import streamlit as st

from app.risk.engine import calculate_risk
from app.face.engine import analyze_face
from app.forensics.engine import analyze_forensics
from app.mrz.engine import analyze_mrz
from app.ocr.engine import extract_data
from app.ui.styles import load_css


def dashboard_page():
    load_css()

    officer_id = st.session_state.get(
        "officer_id",
        "UNKNOWN",
    )

    # =========================================================
    # HEADER
    # =========================================================

    st.markdown(
        """
<div class="dashboard-header">
    <div class="dashboard-brand">NULL FORGERY</div>
    <div class="dashboard-subtitle">
        NATIONAL IDENTITY &amp; DOCUMENT SCREENING SYSTEM
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        st.caption(
            f"AUTHORIZED OFFICER  •  {officer_id}"
        )

    with col2:
        if st.button(
            "LOG OUT",
            use_container_width=True,
        ):
            st.session_state.authenticated = False
            st.session_state.pop(
                "officer_id",
                None,
            )
            st.rerun()

    st.divider()

    # =========================================================
    # SYSTEM STATUS
    # =========================================================

    st.subheader("SYSTEM STATUS")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("SYSTEM", "ONLINE")

    with c2:
        st.metric("OCR ENGINE", "READY")

    with c3:
        st.metric("MRZ ENGINE", "READY")

    with c4:
        st.metric("FORENSICS", "READY")

    st.divider()

    # =========================================================
    # DOCUMENT INPUT
    # =========================================================

    st.subheader("DOCUMENT SCREENING")

    uploaded_file = st.file_uploader(
        "Upload document image",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
    )

    if uploaded_file is None:
        st.info(
            "Waiting for document upload."
        )
        return

    image_bytes = uploaded_file.getvalue()

    st.success(
        f"Document loaded: {uploaded_file.name}"
    )

    preview, information = st.columns(2)

    with preview:
        st.image(
            image_bytes,
            caption="Document preview",
            use_container_width=True,
        )

    with information:
        st.markdown("### FILE INFORMATION")

        st.write(
            f"**Filename:** {uploaded_file.name}"
        )

        st.write(
            f"**Type:** {uploaded_file.type}"
        )

        st.write(
            f"**Size:** {uploaded_file.size:,} bytes"
        )

    # =========================================================
    # OCR
    # =========================================================

    st.divider()

    st.subheader("OCR EXTRACTION")

    if st.button(
        "RUN OCR ANALYSIS",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Extracting document text..."
            ):
                st.session_state.ocr_result = (
                    extract_data(image_bytes)
                )
        except Exception as exc:
            st.error(
                f"OCR analysis failed: {exc}"
            )

    if "ocr_result" not in st.session_state:
        st.info(
            "Run OCR to continue."
        )
        return

    ocr = st.session_state.ocr_result

    if ocr["text_detected"]:
        st.success(
            "OCR extraction completed."
        )

        st.text_area(
            "Extracted text",
            ocr["raw_text"],
            height=200,
        )
    else:
        st.warning(
            "No readable text detected."
        )

    # =========================================================
    # MRZ
    # =========================================================

    st.divider()

    st.subheader("MRZ VALIDATION")

    if st.button(
        "RUN MRZ ANALYSIS",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Detecting MRZ..."
            ):
                st.session_state.mrz_result = (
                    analyze_mrz(
                        ocr["lines"]
                    )
                )
        except Exception as exc:
            st.error(
                f"MRZ analysis failed: {exc}"
            )

    if "mrz_result" in st.session_state:
        mrz = st.session_state.mrz_result

        if not mrz["detected"]:
            st.warning(
                "No probable MRZ detected."
            )
        elif mrz["valid"]:
            st.success(
                "MRZ validation passed."
            )
        else:
            st.warning(
                "MRZ detected but validation requires review."
            )

    # =========================================================
    # FACE ANALYSIS
    # =========================================================

    st.divider()

    st.subheader("FACE ANALYSIS")

    if st.button(
        "RUN FACE ANALYSIS",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Analyzing portrait region..."
            ):
                st.session_state.face_result = (
                    analyze_face(
                        image_bytes
                    )
                )
        except Exception as exc:
            st.error(
                f"Face analysis failed: {exc}"
            )

    if "face_result" not in st.session_state:
        st.info(
            "Face analysis has not been performed."
        )
    else:
        face = st.session_state.face_result

        if face["face_detected"]:
            st.success(
                "Probable portrait region detected."
            )
        else:
            st.warning(
                "No probable portrait region detected."
            )

        f1, f2 = st.columns(2)

        with f1:
            st.metric(
                "PORTRAIT REGIONS",
                face["face_count"],
            )

        with f2:
            if face["quality"]:
                st.metric(
                    "IMAGE QUALITY",
                    face["quality"]["quality"],
                )
            else:
                st.metric(
                    "IMAGE QUALITY",
                    "N/A",
                )

        if face["quality"]:
            q1, q2 = st.columns(2)

            with q1:
                st.metric(
                    "SHARPNESS",
                    f'{face["quality"]["sharpness"]:.2f}',
                )

            with q2:
                st.metric(
                    "BRIGHTNESS",
                    f'{face["quality"]["brightness"]:.2f}',
                )

        st.markdown("### FACE INDICATORS")

        for indicator in face["indicators"]:
            st.write(
                f"• {indicator}"
            )

    # =========================================================
    # FORENSICS
    # =========================================================

    st.divider()

    st.subheader("DOCUMENT FORENSICS")

    if st.button(
        "RUN FORENSIC ANALYSIS",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Inspecting image integrity..."
            ):
                st.session_state.forensic_result = (
                    analyze_forensics(
                        image_bytes
                    )
                )
        except Exception as exc:
            st.error(
                f"Forensic analysis failed: {exc}"
            )

    if "forensic_result" not in st.session_state:
        st.info(
            "Forensic analysis has not been performed."
        )
        return

    forensic = st.session_state.forensic_result

    # ---------------------------------------------------------
    # IMAGE PROPERTIES
    # ---------------------------------------------------------

    st.markdown("### IMAGE PROPERTIES")

    properties = forensic["properties"]

    p1, p2, p3 = st.columns(3)

    with p1:
        st.metric(
            "WIDTH",
            f'{properties["width"]} px',
        )

    with p2:
        st.metric(
            "HEIGHT",
            f'{properties["height"]} px',
        )

    with p3:
        st.metric(
            "CHANNELS",
            properties["channels"],
        )

    # ---------------------------------------------------------
    # ELA
    # ---------------------------------------------------------

    st.markdown("### ERROR LEVEL ANALYSIS")

    st.image(
        forensic["ela_image"],
        caption=(
            "ELA visualization — "
            "interpret as a forensic indicator, "
            "not standalone proof of manipulation."
        ),
        use_container_width=True,
    )

    stats = forensic["ela_statistics"]

    e1, e2, e3 = st.columns(3)

    with e1:
        st.metric(
            "ELA MEAN",
            f'{stats["mean"]:.2f}',
        )

    with e2:
        st.metric(
            "ELA MAX",
            stats["maximum"],
        )

    with e3:
        st.metric(
            "ELA STD DEV",
            f'{stats["std"]:.2f}',
        )

    # ---------------------------------------------------------
    # METADATA
    # ---------------------------------------------------------

    st.markdown("### METADATA")

    metadata = forensic["metadata"]

    if metadata:
        st.json(metadata)
    else:
        st.info(
            "No EXIF metadata found."
        )

    # ---------------------------------------------------------
    # INDICATORS
    # ---------------------------------------------------------

    st.markdown("### FORENSIC INDICATORS")

    for indicator in forensic["indicators"]:
        st.write(
            f"• {indicator}"
        )
    # =========================================================
    # RISK ASSESSMENT
    # =========================================================

    st.divider()

    st.subheader("RISK ASSESSMENT")

    if st.button(
        "RUN RISK ASSESSMENT",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Calculating screening risk..."
            ):
                st.session_state.risk_result = (
                    calculate_risk(
                        mrz_result=st.session_state.get(
                            "mrz_result"
                        ),
                        face_result=st.session_state.get(
                            "face_result"
                        ),
                        forensic_result=st.session_state.get(
                            "forensic_result"
                        ),
                    )
                )
        except Exception as exc:
            st.error(
                f"Risk assessment failed: {exc}"
            )

    if "risk_result" in st.session_state:
        risk = st.session_state.risk_result

        score = risk["score"]
        level = risk["level"]

        r1, r2 = st.columns(2)

        with r1:
            st.metric(
                "RISK SCORE",
                f"{score}/100",
            )

        with r2:
            if level == "LOW":
                st.success(
                    f"RISK LEVEL: {level}"
                )
            elif level == "MEDIUM":
                st.warning(
                    f"RISK LEVEL: {level}"
                )
            else:
                st.error(
                    f"RISK LEVEL: {level}"
                )

        st.markdown("### SCREENING REASONS")

        if risk["reasons"]:
            for reason in risk["reasons"]:
                st.write(
                    f"• {reason}"
                )
        else:
            st.write(
                "No elevated-risk indicators detected."
            )

        st.caption(
            "Risk score is an automated screening indicator "
            "and must not be treated as definitive proof of "
            "document fraud or authenticity."
        )

    # =========================================================
    # PIPELINE
    # =========================================================

    st.subheader("SCREENING PIPELINE")

    mrz_status = "PENDING"

    if "mrz_result" in st.session_state:
            mrz_status = (
                "PASS"
                if st.session_state.mrz_result["valid"]
                else "REVIEW"
            )

    face_status = "PENDING"

    if "face_result" in st.session_state:
            face_status = (
                "PASS"
                if st.session_state.face_result["face_detected"]
                else "REVIEW"
            )

    risk_status = "PENDING"

    if "risk_result" in st.session_state:
            risk_status = st.session_state.risk_result["level"]

    pipeline = [
            ("01", "DOCUMENT INPUT", "COMPLETE"),
            ("02", "OCR EXTRACTION", "COMPLETE"),
            ("03", "MRZ VALIDATION", mrz_status),
            ("04", "FACE ANALYSIS", face_status),
            ("05", "FORENSIC ANALYSIS", "COMPLETE"),
            ("06", "RISK ASSESSMENT", risk_status),
    ]

    for number, module, status in pipeline:
        a, b, c = st.columns(
            [1, 5, 2]
        )

        with a:
            st.write(f"**{number}**")

        with b:
            st.write(module)

        with c:
            st.write(status)

    st.divider()

    st.caption(
        "NULL FORGERY // GOVERNMENT ACCESS NODE // LOCAL PROTOTYPE"
    )
