---
doc_id: "POST-H-025-A-CRITERIA-REPORT"
title: "POST-H-025-A — Criteria schema y evidence map"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-03"
approval: "approved_by_owner"
created_by: "POST-H-025-A"
phase: "POST-FASE-H"
local_first: true
dry_run: true
read_only: true
---

# POST-H-025-A — Criteria schema y evidence map

## Resultado

POST-H-025-A queda implementado como `implemented-initial / criteria-schema-evidence-map-only`.

## Implementación

Se agregan los contratos `ProductionReadyLocalCriteria` y `ProductionReadyLocalReport`, junto con el archivo versionado `.devpilot/production/production_ready_local_criteria.json`.

El criteria JSON define:

```text
- alcance production-ready-local solamente;
- hito requeridos POST-H-002..POST-H-017 y POST-H-024;
- hitos opcionales de diseño POST-H-018..POST-H-023;
- evidence map por hito;
- clasificación de evidencia: required, optional, blocker y advisory;
- minimum_score=90;
- blocking_gaps_allowed=0;
- no-go gates explícitos para remote execution, connector write, plugin execution, external APIs, enterprise/compliance/remote/SaaS claims.
```

## Criterio industrial aplicado

Este micro-sprint no ejecuta agregación ni declara `production-ready-local`. Solo establece el contrato auditable que los micro-sprints POST-H-025-B/C/D/E deberán consumir. El comportamiento esperado del gate futuro es BLOCK por defecto si falta evidencia obligatoria.

## Seguridad

La definición es local-first, read-only y dry-run. No habilita red, APIs externas, remote execution, connector write ni plugin execution. También impide claims enterprise-ready, compliance-certified, remote-ready y SaaS-ready.

## Limitaciones

La agregación de evidencias queda para POST-H-025-B. El CLI/API del gate queda para POST-H-025-C. La validación de claims en documentos queda para POST-H-025-D. La declaración final PASS/BLOCK queda para POST-H-025-E.
