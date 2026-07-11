---
doc_id: POST-H-031-E-REDACTED-EVIDENCE-EXPORT-UX-REPORT
title: "POST-H-031-E — Redacted evidence export UX report"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-031-E — Redacted evidence export UX report

## Decision

PASS as `implemented-initial/local-first/redacted-operator-export`.

POST-H-031-E adds a redacted operator evidence export UX that packages curated summaries from EvidenceGraph, OperatorHealthSummary, GapActionMap, ClaimsNoGoDashboard, ObservabilityRedactedExport, RuntimeStateInventory and ProductionReadyFinalDeclaration.

## Scope

The implementation is intentionally a redacted operator/auditor package. It is not a general repository export and it is not an external certification artifact.

## Safety invariants

- `--redacted` is mandatory.
- Dry-run writes no files.
- Write mode is explicit through `--write-report`.
- All writes are constrained to `outputs/reports` and `outputs/audit_exports/operator_evidence_export`.
- `.env`, `.devpilot/devpilot.db`, raw prompts, raw outputs and arbitrary outputs are not exported.
- The export includes manifest, checksums, redaction manifest and interpretation instructions.
- The package does not mutate claims, no-go gates, project state, source files, runtime DBs or readiness declarations.

## Implemented artifacts

- `docs/schemas/operator_evidence_export.schema.json`.
- `src/devpilot_core/evidence_graph/export.py`.
- `python -m devpilot_core operator evidence-export --redacted --dry-run --json`.
- `python -m devpilot_core operator evidence-export --redacted --write-report --json`.
- `ApplicationService.operator_evidence_export`.
- Protected local API route `GET /api/v1/operator/evidence-export`.
- Documentation and registry synchronization.

## Validation commands

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_redacted_evidence_export_ux.py -q
python -m devpilot_core operator evidence-export --redacted --dry-run --json
python -m devpilot_core operator evidence-export --redacted --write-report --json
python -m devpilot_core schema validate --schema-id OperatorEvidenceExport --instance outputs/reports/operator_evidence_export.json --json
```

## Limitations

This is an implemented-initial UX package. It is sufficient for local operator/auditor evidence sharing, but future iterations may add UI affordances, package signing, richer section-level freshness indicators and optional encrypted delivery. Those future capabilities require separate backlog items and must preserve redaction and local-first constraints.
