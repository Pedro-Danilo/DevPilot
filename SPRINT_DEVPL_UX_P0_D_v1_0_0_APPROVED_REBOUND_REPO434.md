---
doc_id: "SPRINT-DEVPL-UX-P0-D"
title: "DEVPL-UX-P0-D — Cross-surface operational patterns and progressive evidence"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "approved_by_owner"
precondition: "UX-P0-C CLOSED/PASS/WINDOWS-VALIDATED on repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip"
successor_expected: "repo435"
---

# DEVPL-UX-P0-D — Cross-surface operational patterns and progressive evidence

> Rebound baseline: `repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip` / `75dbead73c6c6aaf1f792e02f3659ee2b6c0b927` / `e1117ba5e9c3bace2de482940d6b447b0150acb2e26ba1647f9677939f5faf39`. Repo430 permanece histórico e inmutable. UX-P0-E pasa a repo436.

## Objetivo / alcance

Shared states/actions/gates/approvals/diffs/long-op/evidence patterns across Story, Jobs, Quality, Release, Recovery, AI.

## Validación mínima

impacted smokes + browser focal + a11y + Test Impact.

## Definition of Done

semantic consistency; blockers/evidence correct; Full=0.

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
