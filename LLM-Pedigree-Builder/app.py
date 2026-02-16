"""Unified local Streamlit entrypoint for patient and clinician workflows."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="LLM Pedigree Builder", layout="wide")
st.title("LLM Pedigree Builder")
st.caption("Private-by-default local pedigree builder and analysis prototype")

st.markdown(
    """
## Launch apps
- **Patient app:** `streamlit run apps/patient_app.py`
- **Clinician app:** `streamlit run apps/clinician_app.py`

This landing page exists to provide a single root entrypoint for packaging.
"""
)
