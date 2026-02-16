"""Streamlit clinician-facing app for pedigree upload and risk analysis."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from src.analysis_engine import analyze_pedigree
from src.data_extractor import extract_pedigree_from_upload, pseudonymize_pedigree
from src.output_generator import build_pedigree_figure, generate_pedigree_pdf

st.set_page_config(page_title="Analyze Pedigree", layout="wide")
st.title("Analyze Pedigree")
st.warning("Not medical advice. Local decision support only; validate clinically.")

uploaded_file = st.file_uploader("Upload pedigree file (JSON, QR image, photo)", type=["json", "txt", "png", "jpg", "jpeg", "bmp"])
pseudonymize = st.checkbox("Pseudonymize names in report")

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / uploaded_file.name
        path.write_bytes(uploaded_file.read())

        try:
            pedigree = extract_pedigree_from_upload(str(path))
            if pseudonymize:
                pedigree = pseudonymize_pedigree(pedigree)

            st.subheader("Extracted Pedigree")
            editable_json = st.text_area("Edit JSON before analysis", json.dumps(pedigree, indent=2), height=300)
            pedigree = json.loads(editable_json)

            result = analyze_pedigree(pedigree)
            st.subheader("Risk Analysis")
            st.metric("Inbreeding coefficient", result.inbreeding_coefficient)
            st.metric("Risk level", result.risk_level)
            st.write("Inheritance flags")
            for flag in result.inheritance_flags:
                st.write(f"- {flag}")
            st.write("Recommendations")
            for recommendation in result.recommendations:
                st.write(f"- {recommendation}")

            fig = build_pedigree_figure(pedigree)
            st.image(fig, caption="Pedigree visualization")

            notes = st.text_area("Clinical notes for report", "")
            if st.button("Generate clinician PDF"):
                pdf_out = Path(temp_dir) / "clinician_report.pdf"
                fig_for_pdf = build_pedigree_figure(pedigree)
                generate_pedigree_pdf(pedigree, str(pdf_out), fig_for_pdf, analysis=result, notes=notes)
                st.download_button("Download Clinician PDF", pdf_out.read_bytes(), file_name="clinician_report.pdf")

        except Exception as exc:
            st.error(f"Failed to process upload: {exc}")
else:
    st.info("Upload a file to begin analysis.")
