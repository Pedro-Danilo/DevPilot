---
doc_id: "ADR-POSTH-003"
title: "Modularización progresiva del CLI y command registry"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "accepted_by_owner"
decision_state: "accepted"
micro_sprint: "POST-H-EVAL-001-F"
---

# ADR-POSTH-003 — Modularización progresiva del CLI y command registry

## Contexto

El mapa arquitectónico `POST-H-EVAL-001-C` identificó que `src/devpilot_core/cli.py` concentra la orquestación de muchos dominios. Esta concentración ha sido útil para avanzar rápido, pero representa riesgo de mantenibilidad: acoplamiento alto, dificultad de pruebas por handler, crecimiento acumulativo de comandos y mayor probabilidad de drift entre CLI, ApplicationService, API y UI.

## Decisión

El CLI monolítico entra al roadmap de refactor arquitectónico mediante un **command registry** y handlers por dominio, sin cambiar semántica funcional ni contratos de salida.

La modularización debe ser progresiva:

```text
1. Inventario ejecutable de comandos y ownership.
2. Registry declarativo de comandos.
3. Extracción por handlers de dominio.
4. Preservación de CommandResult, exit codes, JSON output y reportes.
5. Tests de compatibilidad para comandos existentes.
```

## Alternativas consideradas

| Alternativa | Resultado | Motivo |
|---|---|---|
| Mantener CLI monolítico indefinidamente | Rechazada | Aumenta acoplamiento y costo de evolución |
| Reescritura completa del CLI | Rechazada | Riesgo alto de regresión y poco valor incremental |
| Modularización progresiva por registry/handlers | Aceptada | Reduce riesgo y preserva compatibilidad |

## Consecuencias

- `POST-H-005` debe crear base de architecture map executable/dependency ownership.
- `POST-H-006` debe implementar command registry y desacoplamiento de handlers.
- `ApplicationService` y API/UI deben consumir servicios, no duplicar lógica de CLI.
- Los cambios deben ser cubiertos por pruebas de compatibilidad, quality gates y contratos.

## Criterios PASS

```text
comandos existentes mantienen nombres, flags críticos y salida JSON
CommandResult se preserva
handlers tienen ownership por dominio
quality-gate hardening pasa
no se introduce dependencia externa innecesaria
```

## Criterios BLOCK

```text
cambio rompe comandos documentados sin migración
salida JSON cambia sin versión de contrato
ApplicationService duplica lógica del CLI
refactor mezcla features nuevas con modularización
```

## Riesgos

El principal riesgo es introducir regresión al mover handlers. La mitigación es ejecutar el refactor en micro-sprints con tests focales, snapshot de comandos y comparación de `CommandResult` antes/después.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core app contract --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m pytest tests	est_cli_core.py tests	est_application_services.py -q
```

## Estado

Aceptada en `POST-H-EVAL-001-F`. Debe materializarse después de `POST-H-005`, no antes.
