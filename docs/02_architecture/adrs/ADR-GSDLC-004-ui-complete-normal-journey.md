---
doc_id: "ADR-GSDLC-004"
title: "ADR-GSDLC-004 — UI-complete normal journey and project-centric shell"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
approval: "pending_owner_00_c_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-00-C"
runtime_implemented: false
---
# ADR-GSDLC-004 — UI-complete normal journey and project-centric shell

## Contexto

UOC convirtió la Web UI en una consola operacional gobernada, pero sus nueve rutas actuales están organizadas principalmente por capacidades transversales. El objetivo GSDLC exige que el usuario avance por el **proyecto**, no por una colección de herramientas ni por operadores PowerShell externos.

## Decisión

La navegación primaria futura se organiza en `ProjectShell`:

```text
Home
→ Project Status
→ Engineering
→ Planning
→ Stories
→ Release
```

Reports, Traces, Approvals, Jobs, Quality, AI/Agent tools y Settings se mantienen como vistas transversales.

La UI normal consume exclusivamente API local/ApplicationService y operaciones tipadas. Quedan prohibidos:

- React→filesystem;
- React→Git directo;
- React→core;
- terminal web/arbitrary shell;
- parámetros libres que eviten schema/allowlist.

## Project Status

Debe estar accesible durante todo el journey y mostrar como mínimo fase, paso, progreso, blockers, approvals pendientes, quality signal, Git state, presupuesto de modelo/tokens, next action y execution modes disponibles.

## StepActionAdvisor

Servicio determinístico con entradas:

`state + step + role + policy + capability registry + provider availability + budget + risk`.

Produce:

- `MANUAL`;
- `PASTE`;
- `UPLOAD_IMPORT`;
- `EXTERNAL_EDITOR`;
- `AGENT`;
- `RAG`;
- `TYPED_OPERATION`;

cada uno con `available`, disabled reason, approvals, dry-run, side effects, costo/tokens estimados y evidencia esperada.

El LLM no decide qué modo está permitido.

## Criterio UI-complete

Para cada milestone cerrado:

```text
PowerShell required by normal user = 0
External operator project writes = 0
Required unclassified CLI bridge = 0
```

CLI/API continúan como expert automation, CI o diagnóstico.

## Estado

`planned-GSDLC`. Las nueve rutas UOC actuales siguen siendo válidas como baseline histórico/current; este ADR no agrega rutas.
