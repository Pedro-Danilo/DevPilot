---
title: "ADR-0002 — Core local-first con CLI inicial y UI futura"
doc_id: "DEVPL-ADR-0002"
status: "accepted"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-08"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0002 — Core local-first con CLI inicial y UI futura

## Contexto

DevPilot debe iniciar rápido, ser testeable, local-first y útil antes de construir interfaces visuales. Sin embargo, la evolución hacia desktop y web es un compromiso del producto.

## Decisión

Construir primero un **DevPilot Core** reutilizable y exponerlo inicialmente por CLI. Desktop y Web deberán consumir el mismo core, no duplicar lógica.

## Consecuencias

- La CLI permite validar reglas, reportes y gates con bajo costo.
- El core se mantiene como activo principal.
- Desktop/Web llegan después con menor riesgo.
- Se evita crear una UI bonita sobre reglas inmaduras.

## Actualización 2026-06-08 — FUNC-SPRINT-18

Estado de implementación: `implemented-initial`.

Sprint 18 materializa esta ADR sin implementar UI todavía. Se creó una frontera de Application Services y DTOs serializables:

```text
src/devpilot_core/application/dtos.py
src/devpilot_core/application/services.py
python -m devpilot_core app contract --json
docs/07_interfaces/internal_application_contract.md
```

La decisión se mantiene: el CLI, la futura aplicación desktop y la futura interfaz web deben consumir el mismo DevPilot Core. No se agregaron dependencias de FastAPI, Tauri, Electron ni frameworks frontend. La selección tecnológica sigue pendiente de una ADR futura.

### Consecuencias

- El core queda más desacoplado de la CLI.
- Las operaciones de validación tienen una frontera reutilizable.
- Los DTOs preparan contratos para desktop/web.
- El riesgo de duplicar lógica de validadores en UI disminuye.

### Riesgos pendientes

- No hay autenticación, sesiones ni RBAC para UI.
- No hay API HTTP, IPC ni empaquetado desktop.
- No hay versionado formal de schemas JSON.
- No hay selección definitiva de stack.
