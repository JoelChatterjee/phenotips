# Contributing to LLM-Pedigree-Builder

Thanks for helping improve a local-first, privacy-preserving genetics support tool.

## Development setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Quality checks
```bash
pytest
ruff check .
mypy src
```

## Pull request expectations
- Keep changes focused and modular.
- Add/extend tests for behavioral changes.
- Update docs for user-visible or API changes.
- Preserve privacy-by-default behavior (no cloud calls, no hidden telemetry).

## Clinical and ethical boundaries
- Do not frame output as diagnosis.
- Maintain/extend consent and warning UX.
- Prefer conservative risk language.

## Commit style
Use clear, imperative commit messages:
- `Add OCR fallback confidence threshold`
- `Refactor analysis flags into dedicated module`
- `Document threat model and data retention policy`
