---
doc_id: "SPRINT-DEVPL-UX-P0-C"
title: "DEVPL-UX-P0-C — Greenfield critical-path surface productization"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "UX-P0-B CLOSED/PASS/WINDOWS-VALIDATED"
successor_expected: "repo434"
source_repo: "repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "dc63672f2d617968998f3c68374a03581b348578"
source_repo_sha256: "f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246"
source_backlog: "DEVPL_UX_P0_PRE_PILOT_PRODUCTIZATION_BACKLOG_v1_0_1_APPROVED_REBOUND_REPO433.md"
full_regression: "PROHIBITED"
---

# Owner approval / rebound — 2026-09-15

El owner autoriza UX-P0-C sobre el successor Windows-validado inmediato de UX-P0-B. Repo433 es baseline inmutable de entrada y repo434 es el successor esperado.

# DEVPL-UX-P0-C — Greenfield critical-path surface productization

## Objetivo / alcance

Home, Entry, Project Status, Pre-code, Documents entry, Planning; Guided copy/action hierarchy.

## Validación mínima

targeted browser critical path, role-negative, keyboard, API parity, Test Impact.

## Definition of Done

seven UX questions answerable; no terminal external normal path; Full=0.

## Seguridad y gobernanza

Preservar server authority, RBAC, approvals, route/API contracts, local-first/no-remote y evidencia. No acciones destructivas ni force Git. LF/CRLF no constituye autoridad.

## Operador Windows

Debe entregarse un único bundle reentrante/state-aware con una sola guía `.md`, pasos consecutivos y comandos PowerShell de una línea. Python preferido.

## Riesgos

- convertir productización UX en reescritura total;
- degradar route/API/policy contracts por cambios de presentación;
- esconder evidencia o blockers para simplificar la UI;
- introducir dependencia nueva sin necesidad;
- crear falsos BLOCK por representación física LF/CRLF.

## Comandos de verificación base

El operador del micro-sprint debe resolver desde el successor vigente y ejecutar como mínimo los equivalentes actuales de:

```text
cd ui/web && npm run build
cd ui/web && npm run test:route-enforcement
cd ui/web && npm run test:accessibility
cd ui/web && npm run test:state-matrix
python -m pytest <tests focales/impactados derivados por Test Impact> -q
```

Los comandos exactos deben validarse contra `package.json`, CLI registry y Test Impact del successor; no copiar comandos históricos si el contrato vigente cambió.
