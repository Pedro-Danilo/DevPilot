---
title: "DevPilot Local — Backlog ejecutable posterior a pre-code"
doc_id: "DEVPL-FUNC-BACKLOG-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-PRECODE"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
---

# DevPilot Local — Backlog ejecutable posterior a pre-code

## 1. Objetivo

Definir las acciones inmediatas después del cierre de la fase pre-code. El propósito es convertir la documentación aprobada en capacidades ejecutables de DevPilot Local sin saltar directamente a agentes autónomos ni a interfaces visuales complejas.

## 2. FUNC-SPRINT-01 — Core CLI de validación MIPSoftware/MIASI

### Objetivo

Implementar el primer núcleo funcional fuerte de DevPilot: comandos CLI que validen documentos, frontmatter, estados, checklist pre-code y readiness de un workspace local.

### Backlog ejecutable

| ID | Tarea | Entregable | Criterio PASS |
|---|---|---|---|
| FUNC-001 | Crear módulo `devpilot_core.validators.frontmatter` | Validador de frontmatter | Detecta campos obligatorios y falla con exit code. |
| FUNC-002 | Crear módulo `devpilot_core.validators.artifact` | Validador de secciones mínimas | Valida documentos MIPSoftware/MIASI. |
| FUNC-003 | Crear comando `validate-artifact` | CLI | Reporte JSON/Markdown por documento. |
| FUNC-004 | Crear comando `validate-frontmatter` | CLI | PASS/FAIL por archivo. |
| FUNC-005 | Crear comando `checklist-pre-code` | CLI | Evalúa `docs/checklists/checklist_pre_code.md`. |
| FUNC-006 | Mejorar `readiness-check --strict` | CLI | Valida existencia, estado, frontmatter y baseline. |
| FUNC-007 | Crear `reports/` contract | JSON schema mínimo | Reportes reproducibles. |
| FUNC-008 | Crear trazas JSONL mínimas | `outputs/traces/events.jsonl` | Cada comando emite evento. |
| FUNC-009 | Agregar pruebas pytest | `tests/` | Tests PASS para casos válidos e inválidos. |
| FUNC-010 | Documentar comandos | README/runbook | Comandos reproducibles. |

### Comandos objetivo

```powershell
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md
python -m devpilot_core checklist-pre-code
python -m devpilot_core readiness-check --strict
pytest -q
```

### Criterios BLOCK

- No se permite escritura fuera de `outputs/`.
- No se permite uso de APIs externas.
- No se permite aplicar patches.
- No se habilitan agentes ejecutores.
- No se ignoran fallos de frontmatter o documentos obligatorios.

## 3. FUNC-SPRINT-02 — Workspace Manager mínimo

| ID | Tarea | Entregable |
|---|---|---|
| FUNC-011 | Diseñar `.devpilot/project.yaml` | Descriptor de workspace |
| FUNC-012 | Crear `workspace detect` | Detección de workspace |
| FUNC-013 | Crear `workspace status` | Estado de documentos/gates |
| FUNC-014 | Crear política de rutas | allowlist/denylist inicial |
| FUNC-015 | Tests de seguridad de rutas | pytest |

## 4. FUNC-SPRINT-03 — Report Engine, JSONL y evidencias

| ID | Tarea | Entregable |
|---|---|---|
| FUNC-016 | Normalizar reportes JSON | contratos |
| FUNC-017 | Generar reportes Markdown | outputs/reports |
| FUNC-018 | Implementar eventos JSONL | outputs/traces |
| FUNC-019 | Redacción de secretos sintéticos | tests |
| FUNC-020 | Snapshot tests de reportes | pytest |

## 5. FUNC-SPRINT-04 — Agentes documentales controlados MVP

| ID | Tarea | Entregable |
|---|---|---|
| FUNC-021 | Implementar `PreCodeDocumentationAgent` mock/local | agente dry-run |
| FUNC-022 | Implementar `DocumentationAuditAgent` mock/local | agente dry-run |
| FUNC-023 | Tool Registry declarativo | YAML/JSON |
| FUNC-024 | Policy checks para tools | Policy Engine mínimo |
| FUNC-025 | Eval fixtures documentales | JSONL |

## 6. FUNC-SPRINT-05 — Git read-only y repo inventory MVP+

| ID | Tarea | Entregable |
|---|---|---|
| FUNC-026 | Implementar `git-status` | CLI read-only |
| FUNC-027 | Implementar `repo-inventory` | inventario local |
| FUNC-028 | Detectar archivos sensibles | reporte redactado |
| FUNC-029 | No modificar repos | tests |
| FUNC-030 | Trazas Git | JSONL |

## 7. Reglas de secuencia

No avanzar a Git/patch/refactor hasta que `FUNC-SPRINT-01` y `FUNC-SPRINT-02` estén en PASS. No habilitar agentes con herramientas de escritura hasta que Policy Engine, approval y trazas estén implementados y probados.
