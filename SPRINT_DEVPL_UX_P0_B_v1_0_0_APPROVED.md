---
doc_id: "SPRINT-DEVPL-UX-P0-B"
title: "DEVPL-UX-P0-B — Product App Shell, grouped navigation and persistent project context"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "UX-P0-A CLOSED/PASS/WINDOWS-VALIDATED"
source_repo: "repo_DevPilot_Local_431_DEVPL_UX_P0_A_AUTHORITY_DESIGN_SYSTEM_FOUNDATION_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "013cc84f0df9eff1fb750b542644bfd0c7dc8717"
source_repo_sha256: "be80b6490cbbbfc7b5827fa896cbe5528a2b2d3676fb6c2ceef672820ee2f097"
successor_expected: "repo432"
---

# Owner approval — 2026-09-15

El owner autoriza la implementación de DEVPL-UX-P0-B sobre el successor Windows-validado de UX-P0-A.

# DEVPL-UX-P0-B — Product App Shell, grouped navigation and persistent project context

## Objetivo / alcance

Grouped navigation; breadcrumbs; persistent Project Context; authoritative Next Action; Guided/Expert shell.

## Validación mínima

auth/route guards, handoff/recovery, keyboard, responsive browser, Test Impact.

## Definition of Done

Project/stage/state/blocker/next-action visible; Full=0.

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
