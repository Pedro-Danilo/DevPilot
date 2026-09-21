---
doc_id: "DEVPL-GSDLC-13-ACCEPTANCE-EVIDENCE-PLAN"
title: "DEVPL-GSDLC-13 — Acceptance evidence plan"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "DEVPL_GSDLC_13_ACCEPTANCE_EVIDENCE_PLAN_v1_0_0_APPROVED.md"
---

# Acceptance evidence plan

## Roots

- evaluation: `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13`;
- workspace: `D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield`;
- optional export: `D:\Projects\DevPilot_Artifacts\GSDLC-13-GREENFIELD`.

## Authority Pack estable

Se adjunta/recarga solo al cambiar autoridad: DevPilot baseline/successor, active sprint, Operating Model, Runbook y UX-P1 policy.

## Run Packet incremental

Cada checkpoint adjunta solo evidencia nueva:

- checkpoint/timestamps;
- receipts/logs/export;
- screenshots decisivos;
- first-attempt;
- time-to-next-valid-action;
- confusion/block moments;
- normal-user terminal escapes;
- audit/operator terminal uses;
- operator project writes;
- approvals/provenance;
- Git before/after;
- tests/gates;
- UX findings/disposition;
- confidence 1–5.

## Evidence integrity

- no evidence se usa para editar el proyecto externamente;
- no full acceptance rerun para ocultar FAIL;
- first-attempt se preserva aunque exista corrective;
- corrective retest se etiqueta como tal y referencia el finding/checkpoint original;
- project evidence y DevPilot corrective evidence se mantienen diferenciados.
