---
doc_id: POST-H-030-B-INDUSTRIAL-READINESS-EXTRACTION-REPORT
title: "POST-H-030-B Industrial readiness command extraction report"
status: approved
version: "1.0.0"
owner: POST-H-030-B
updated: "2026-07-09"
approval: approved
---

# POST-H-030-B — Industrial readiness command extraction report

Estado: `implemented-initial/local-first`.

POST-H-030-B extrae la familia `industrial-readiness` desde `src/devpilot_core/cli.py` hacia `src/devpilot_core/cli_commands/industrial_readiness.py`, preservando compatibilidad pública.

## Comandos migrados

- `industrial-readiness check`
- `industrial-readiness production-ready-local`
- `industrial-readiness production-ready-local-final`

## Decisiones técnicas

- `cli.py` conserva parser, flags, wrappers públicos, impresión, eventos y persistencia.
- `cli_commands/industrial_readiness.py` concentra la construcción de `CommandResult`.
- `production-ready-local` y `production-ready-local-final` siguen pasando por `ApplicationService`.
- No se duplica lógica de claims ni no-go gates.
- No se introduce router dinámico ni carga dinámica de handlers.

## Safety invariants

- Network: false.
- External APIs: false.
- Remote execution: false.
- Connector write: false.
- Plugin execution: false.
- Source mutations at runtime: false.

## Limitaciones

Esta es una extracción inicial de una familia crítica. Los snapshots formales de compatibilidad CLI quedan para POST-H-030-E; release y workspace/onboarding quedan para POST-H-030-C/D.
