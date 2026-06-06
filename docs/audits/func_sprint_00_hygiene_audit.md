---
title: "DevPilot Local — FUNC-SPRINT-00: higiene del repo y sincronización de baseline"
doc_id: "DEVPL-FUNC-00-HYGIENE-AUDIT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-00"
updated: "2026-06-06"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-00 — Higiene del repo y sincronización de baseline

## 1. Propósito

Este artefacto registra la ejecución de `FUNC-SPRINT-00`, cuyo objetivo es dejar el repositorio limpio, reproducible y sincronizado con la baseline documental aprobada antes de iniciar la implementación funcional fuerte.

## 2. Entradas auditadas

| Entrada | Estado |
|---|---|
| `repo_DevPilot_Local_01.zip` | Usado como fuente de verdad |
| `docs/functional_backlog_after_precode.md` | Promovido a `approved` |
| `.gitignore` | Revisado y ampliado |
| `README.md` | Actualizado al estado funcional actual |
| Caches locales | Eliminadas del paquete refinado |
| `tests/` | Disponible |
| `src/devpilot_core/` | Disponible |

## 3. Acciones realizadas

| ID | Acción | Resultado |
|---|---|---|
| FUNC-00-001 | Revisar `.gitignore` | PASS |
| FUNC-00-002 | Eliminar `__pycache__` y artefactos generados del paquete refinado | PASS |
| FUNC-00-003 | Actualizar README con baseline funcional real | PASS |
| FUNC-00-004 | Promover backlog funcional a `approved` | PASS |
| FUNC-00-005 | Registrar auditoría de aprobación y sprint | PASS |
| FUNC-00-006 | Crear script de limpieza dry-run para el entorno Windows | PASS |
| FUNC-00-007 | Ejecutar pruebas con `PYTHONPATH=src python -m pytest -q` | PASS |
| FUNC-00-008 | Ejecutar CLI `readiness-check` | PASS |
| FUNC-00-009 | Ejecutar CLI `miasi-required` | PASS |

## 4. Validaciones ejecutadas

```text
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m devpilot_core --version
PYTHONPATH=src python -m devpilot_core readiness-check
PYTHONPATH=src python -m devpilot_core miasi-required
```

## 5. Resultado

El repositorio queda apto para iniciar:

```text
FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados
```

## 6. Decisiones de higiene

Se creó `scripts/func_sprint_00_cleanup.ps1`, un script PowerShell seguro con modo dry-run por defecto para detectar artefactos generados antes de eliminarlos explícitamente con `-Execute`.

Se excluyeron del paquete refinado:

- `__pycache__/`;
- `.pytest_cache/`;
- `*.pyc`;
- `*.egg-info`;
- ZIPs locales;
- artefactos de build.

## 7. Criterios PASS

| Criterio | Resultado |
|---|---|
| No hay caches Python en el paquete refinado | PASS |
| `.gitignore` cubre artefactos generados | PASS |
| `pytest` pasa con configuración de ruta explícita | PASS |
| CLI bootstrap responde | PASS |
| Baseline documental permanece aprobada | PASS |
| Backlog funcional queda aprobado | PASS |

## 8. Criterios BLOCK evaluados

| Criterio BLOCK | Estado |
|---|---|
| `pytest` falla | No bloquea |
| Faltan documentos pre-code aprobados | No bloquea |
| Hay caches dentro del paquete refinado | No bloquea |
| El backlog funcional no está aprobado | No bloquea |
| El CLI bootstrap no responde | No bloquea |

## 9. Próxima acción

Iniciar `FUNC-SPRINT-01` sin crear todavía agentes ejecutores, Git write, patch apply o llamadas externas. El próximo sprint debe construir el modelo común de resultados, errores y contratos del CLI.
