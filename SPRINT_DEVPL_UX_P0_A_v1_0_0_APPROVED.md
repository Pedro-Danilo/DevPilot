---
doc_id: "SPRINT-DEVPL-UX-P0-A"
title: "DEVPL-UX-P0-A — Authority rebind, frontend identity and design-system foundation"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "repo430 + Git sync PASS"
successor_expected: "repo431"
source_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "a415504bbf021566243ef4000b1a27d4c8846fee"
source_repo_sha256: "969f7d6b8cbdd8eb3bc32491718e94ee41295647e82234779aee180cea2a388a"
remote_sync_precondition: "DEVPL-POST-GSDLC-GIT-REMOTE-SYNC/CLOSED-PASS-WINDOWS-VALIDATED"
---

# Owner approval — 2026-09-15

El owner aprueba este artefacto como autoridad operativa para DEVPL-UX-P0. Repo430 permanece inmutable; toda mutación inicia en su successor.

# DEVPL-UX-P0-A — Authority rebind, frontend identity and design-system foundation

## Objetivo / alcance

Rebind/document S3 cleanup; approved docs; frontend metadata; design tokens; IA baseline.

## Validación mínima

UI build, route enforcement, a11y/state matrix, docs/TCR, Test Impact.

## Definition of Done

Full=0; authority coherent; tokens/IA ready; no guard drift.

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
