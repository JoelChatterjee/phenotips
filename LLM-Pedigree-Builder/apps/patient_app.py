"""Streamlit patient-facing app for conversational pedigree building."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from src.llm_chat import PedigreeChatEngine
from src.output_generator import build_pedigree_figure, generate_pedigree_pdf, generate_qr_code
from src.pedigree_builder import default_pedigree, to_gedcom

st.set_page_config(page_title="Build Your Family Tree", layout="wide")
st.title("Build Your Family Tree")
st.warning("This tool runs locally and is not medical advice. Please consult a licensed professional.")

consent = st.checkbox("I understand data stays local and is sensitive—proceed?")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pedigree" not in st.session_state:
    st.session_state.pedigree = default_pedigree()

engine = PedigreeChatEngine()

if consent:
    st.subheader("Family history chat")
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input("Tell me about your family. Example: My mother has diabetes.")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        try:
            response = engine.process_user_message(st.session_state.chat_history, user_input)
            st.session_state.pedigree = response.pedigree
            with st.chat_message("assistant"):
                st.json(response.pedigree)
                if response.follow_up_question:
                    st.info(response.follow_up_question)
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": json.dumps(response.pedigree)
                    + (f"\n{response.follow_up_question}" if response.follow_up_question else ""),
                }
            )
        except Exception as exc:
            st.error(f"Could not process message: {exc}")

    st.divider()
    st.subheader("Generated pedigree preview")
    fig = build_pedigree_figure(st.session_state.pedigree)
    st.image(fig, caption="Pedigree Visualization", use_container_width=False)

    notes = st.text_area("Optional notes for PDF", "")
    if st.button("Generate Outputs"):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            qr_path = temp_path / "pedigree_qr.png"
            pdf_path = temp_path / "pedigree_report.pdf"
            json_path = temp_path / "pedigree.json"
            gedcom_path = temp_path / "pedigree.ged"

            generate_qr_code(st.session_state.pedigree, str(qr_path))
            fig_for_pdf = build_pedigree_figure(st.session_state.pedigree)
            generate_pedigree_pdf(st.session_state.pedigree, str(pdf_path), fig_for_pdf, notes=notes)
            json_path.write_text(json.dumps(st.session_state.pedigree, indent=2), encoding="utf-8")
            gedcom_path.write_text(to_gedcom(st.session_state.pedigree), encoding="utf-8")

            st.success("Artifacts generated locally.")
            st.image(str(qr_path), caption="Shareable QR")
            st.download_button("Download JSON", json_path.read_bytes(), file_name="pedigree.json")
            st.download_button("Download GEDCOM", gedcom_path.read_bytes(), file_name="pedigree.ged")
            st.download_button("Download QR", qr_path.read_bytes(), file_name="pedigree_qr.png")
            st.download_button("Download PDF", pdf_path.read_bytes(), file_name="pedigree_report.pdf")
else:
    st.info("Please confirm consent to continue.")
