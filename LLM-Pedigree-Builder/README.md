# LLM-Pedigree-Builder (V1 Prototype)

Open-source local-first prototype for conversational pedigree creation and clinician-side genetic risk triage.

## Features
- **Patient workflow (Streamlit):** natural language chat for family history capture, structured pedigree JSON output, GEDCOM export, pedigree visualization, QR generation, and PDF report export.
- **Clinician workflow (Streamlit):** upload JSON/QR/photo, extract pedigree data, edit JSON, run rule-based inheritance and risk analysis, and generate clinician PDF report.
- **Privacy and ethics:** local execution only, no external API calls required, explicit warnings and consent gates.

## Architecture
```
LLM-Pedigree-Builder/
├── app.py
├── apps/
│   ├── patient_app.py
│   └── clinician_app.py
├── src/
│   ├── llm_chat.py
│   ├── pedigree_builder.py
│   ├── analysis_engine.py
│   ├── output_generator.py
│   └── data_extractor.py
├── tests/
├── docs/
└── examples/
```

## Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Optional local LLM setup (Ollama)
```bash
ollama pull qwen2.5:7b-instruct
# fallback
ollama pull llama3
```
Set model if needed:
```bash
export OLLAMA_MODEL=qwen2.5:7b-instruct
```

## Run
```bash
streamlit run apps/patient_app.py
streamlit run apps/clinician_app.py
# or landing page
streamlit run app.py
```

## Testing
```bash
pytest
```

## Engineering quality and OSS maturity
To make this project best-in-class open source, prioritize:
1. **Trust:** strict local-first privacy defaults and explicit medical disclaimers.
2. **Reliability:** deterministic regression tests for end-to-end patient/clinician workflows.
3. **Transparency:** explainable risk flags with provenance for each recommendation.
4. **Community:** contribution templates, clear governance, and responsive issue triage.

See:
- [ROADMAP.md](ROADMAP.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [docs/ethical_guidelines.md](docs/ethical_guidelines.md)

## Notes and assumptions
- If Ollama/LangChain runtime is unavailable, a deterministic local parser fallback is used for development.
- Risk scoring is heuristic and intended for MVP triage, not diagnosis.
- OCR requires local tesseract binary installed on the system path.

## Contributing
- Add tests for new core logic.
- Keep APIs typed and modular.
- Preserve local-only privacy defaults.
