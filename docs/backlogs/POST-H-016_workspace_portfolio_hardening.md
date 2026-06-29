---
doc_id: "POST-H-016-BACKLOG"
id: "POST-H-016"
title: "POST-H-016 — Workspace portfolio hardening"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-29"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "in_progress"
current_micro_sprint: "POST-H-016-C"
next_micro_sprint: "POST-H-016-D"
---

# POST-H-016 — Workspace portfolio hardening

## Estado

POST-H-016 queda aprobado para implementación incremental. El hito endurece el manejo de múltiples workspaces locales y del portfolio local de DevPilot sin convertir la plataforma en SaaS, multiusuario enterprise o runtime remoto.

La implementación es `implemented-initial` por micro-sprint: cada entrega debe mantener compatibilidad histórica, no-go gates explícitos y evidencia local verificable. La declaración `production-ready-local` sigue reservada para hitos posteriores.

## Objetivo

Endurecer la gestión de múltiples workspaces locales, garantizando:

```text
- registry explícito y deny-by-default;
- workspace activo no ambiguo;
- migración compatible v1 -> v2;
- aislamiento de estado, outputs, traces, reports y secretos;
- portfolio status read-only;
- validación local sin red, APIs externas ni mutaciones por defecto.
```

## Micro-sprints

```text
POST-H-016-A — Registry v2 y migración compatible
POST-H-016-B — Workspace isolation validator
POST-H-016-C — Portfolio status hardening
POST-H-016-D — CLI/API integration segura
POST-H-016-E — Quality gate y runbook
```

## POST-H-016-A

Alcance del micro-sprint actual:

```text
1. Crear Multiworkspace Registry v2 schema.
2. Implementar migración read-only v1 -> v2.
3. Mantener compatibilidad con el registry v1 vigente.
4. Agregar registry-validate v2 al CLI.
5. Crear pruebas focales de contrato, CLI y no-go defaults.
```

Comando operacional:

```powershell
python -m devpilot_core workspace registry-validate --registry-version v2 --json
```

## Límites

POST-H-016-A no implementa todavía:

```text
- isolation report;
- hardening completo de portfolio status;
- API endpoint dedicado de portfolio hardening;
- quality gate workspace-portfolio-hardening;
- reparación automática de workspaces;
- escrituras cross-workspace;
- remote execution;
- connector write;
- plugin execution;
- APIs externas.
```

Estas capacidades quedan para POST-H-016-B/C/D/E.

## POST-H-016-B

Alcance del micro-sprint actual:

```text
1. Implementar WorkspaceIsolationValidator.
2. Validar que root/state/outputs/traces permanecen dentro del workspace.
3. Detectar referencias cruzadas a otros roots registrados.
4. Integrar PathGuard.
5. Generar workspace_isolation_report.json bajo outputs/reports solo cuando se solicita.
```

Comando operacional:

```powershell
python -m devpilot_core workspace isolation-check --json --write-report
```

Límites: `implemented-initial`; no endurece todavía `portfolio status`, no expone API dedicada y no integra el subgate final `workspace-portfolio-hardening`. POST-H-016-C/D/E completan esas capas.

## POST-H-016-C

Alcance del micro-sprint actual:

```text
1. Endurecer PortfolioStatusBuilder sobre Workspace Registry v2.
2. Validar portfolio status contra WorkspaceIsolationValidator antes de consolidar señales.
3. Mostrar únicamente workspaces registrados.
4. Reportar un summary por workspace: readiness, state, reports, traces y risks.
5. Reportar como unknown las fuentes operacionales ausentes.
6. Mantener no-go gates: read-only, sin secrets read, sin state DB read y sin cross-workspace writes.
```

Comando operacional:

```powershell
python -m devpilot_core portfolio status --json
```

Criterios PASS:

```text
- registered_workspaces_only=true;
- unregistered_workspace_policy=denied;
- portfolio_status_read_only=true;
- state_files_read=false;
- secrets_read=false;
- source_mutations_performed=false;
- cross_workspace_writes=false;
- cada workspace reportado tiene is_registered=true.
```

Criterios BLOCK:

```text
- Registry v2 inválido;
- WorkspaceIsolationValidator detecta rutas fuera del workspace;
- referencias cruzadas entre workspaces;
- colisiones de state/reports/traces;
- intento de leer secretos o state DB.
```

Límites: `implemented-initial`; POST-H-016-C no expone API dedicada, no implementa UI específica ni integra todavía el subgate final `workspace-portfolio-hardening`. POST-H-016-D/E completan esas capas.
