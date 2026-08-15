---
doc_id: "DEVPL-GSDLC-R01-B-AUTH-POLICIES-TEMPLATES"
title: "DEVPL-GSDLC-R01-B — Auth policies and engineering/procurement templates"
status: "implemented-controlled/pending-windows-validation"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-B"
source_repo: "repo_DevPilot_Local_343_DEVPL_GSDLC_R01_A_LANDSCAPE.zip"
source_git_commit: "316f616263a74916e9a35ce1596f70e86952ebaa"
research_basis: "deep-research-report_GSDLC-R01-B.md"
---

# Auth policies and engineering/procurement templates

These are engineering/procurement **templates**, not signature-ready legal clauses and not legal advice.

## Authentication policy

- Prefer workload identities/short-lived credentials where the provider officially supports them.
- Never commit real API keys, OAuth tokens, cookies, session tokens or cloud credentials.
- Consumer web login/session is not a programmatic integration mechanism.
- A route is identified by provider + access mechanism + contractual/billing context + region/data path, not by protocol compatibility alone.
- External routes remain disabled until a later explicit enablement ADR/backlog.

## Clause/checklist templates

### DATA-01 — Data residency / international transfer
Record processing regions, storage regions, transfer/transmission mechanism, subprocessors and workload data classes. Unknown values block sensitive-data use.

### LOG-01 — Logging
Record whether prompts/outputs/metadata are logged, log destinations, default state, retention and operator controls. Default benchmark posture is minimum content logging.

### TEL-01 — Telemetry
Record service telemetry separately from content logging and document opt-out/configuration where officially supported.

### PII-01 — Personal-data handling
Require classification, lawful basis/authorization, controller/processor roles, DPA, transfer mechanism, retention/deletion, security controls and Privacy/Legal approval before external PII processing.

### TRAIN-01 — Provider training / product improvement
Freeze whether prompts/outputs may be used for model/product improvement for the exact paid/free/enterprise route. If not documented, record unknown.

### FT-01 — Fine-tuning
Freeze ownership, training-data handling, retention, derived artifact rights and deletion for any future fine-tuning route. Not authorized by R01-B.

### RET-01 — Retention and deletion
Freeze default/optional retention and deletion behavior; do not infer zero retention from marketing language.

### SUB-01 — Subprocessors
Record relevant subprocessors and change-notification mechanism where officially documented.

### SLA-01 — Incident / continuity / SLA
Freeze service commitment, incident notification and continuity requirements appropriate to the future workload.

### AUTH-01 — Credentials and workload identity
Define secret injection, rotation, least privilege, service identity, expiration, revocation and audit requirements. Repository-stored real secrets remain prohibited.
