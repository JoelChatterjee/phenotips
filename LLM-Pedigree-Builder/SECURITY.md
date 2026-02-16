# Security Policy

## Supported versions
This project is currently pre-1.0 and accepts security reports for `main`.

## Reporting a vulnerability
Please report vulnerabilities privately to project maintainers before public disclosure.
Include:
- affected component(s)
- proof of concept / reproduction steps
- potential impact and threat model assumptions

## Security principles
- Local-first execution and storage by default
- No hidden network exfiltration
- Minimal retention of sensitive family history
- Clear user consent and warning surfaces

## High-priority threat areas
- Prompt injection via uploaded documents
- Malicious payloads in JSON/QR uploads
- Insecure temporary-file handling
- Unintended persistence of PHI/PII in logs
