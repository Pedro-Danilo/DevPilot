---
doc_id: "DEVPL-GSDLC-13-BACKLOG"
title: "DEVPL-GSDLC-13 — Real product acceptance backlog"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_BACKLOG_v1_0_0_APPROVED.md"
execution_model: "owner-driven/devpilot-executed/chatgpt-adjudicated after 13-A"
---

# DEVPL-GSDLC-13 — Backlog

## Invariantes

- repo436 immutable;
- Git remote sync PASS;
- greenfield nuevo; no historical artifacts;
- operator project writes=0;
- mandatory UI journey; normal-user terminal escapes=0;
- Owner decisions through product; ChatGPT external is not project oracle;
- dry-run/approval before relevant mutations;
- authority/RBAC/evidence/provenance preserved;
- no destructive Git / no force push;
- LF/CRLF never change authority;
- mock/no API baseline; local/API external opt-in/provenanced;
- PASS checkpoint normal => adjudication + next Run Card, no bundle.

## 13-A

Rebind authorities; materialize package docs; register roots/instrumentation; no greenfield content.

## 13-B — Checkpoints B-01..B-03

Pasos 1–8: launch/login/Home; Create Project; idea/constraints; plan/dry-run/approval; bootstrap workspace/Git/environment; Project Status; restart/recover.

## 13-C — Checkpoints C-01..C-04

Pasos 9–17: Vision/Scope/Requirements; Architecture/Security/Test Strategy/ADRs/traceability; readiness; Roadmap/Backlog/Sprint/Stories.

## 13-D — Checkpoints D-01..D-08

Pasos 18–32 y 34–38: story loop; quality; Git; repeat to MVP; recovery scenarios; release. Paso 33 UX-P1 transversal.

## 13-E — E-01

Paso 39: independent audit, conditional Full policy, closure y legacy handoff.

## Corrective backlog rule

Un BLOCK no autoriza a ChatGPT/Owner a completar externamente el proyecto. Si la causa es DevPilot, crear UX-P1/product corrective bounded, Windows-validate, sync y retest exact checkpoint. Si es decisión legítima del Owner, resolver dentro de la UI. Si es ambiente, corregir solo el ambiente sin project writes.
