---
title: "Acceptance Criteria — DevPilot Local"
doc_id: "DEVPL-REQ-004"
status: "reviewed"
version: "0.2.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-02"
updated: "2026-06-02"
approval: "ready_for_owner_approval"
source_baseline: "SPRINT-PRECODE-01 product baseline approved"
---
# Acceptance Criteria — DevPilot Local

## 1. Propósito

Este documento define criterios de aceptación verificables para las historias, casos de uso y requerimientos de DevPilot Local. Su función es asegurar que cada capacidad importante tenga una condición observable de cumplimiento y evidencia asociada.

## 2. Criterios globales de aceptación del MVP

| ID | Criterio | Requisitos | Evidencia | PASS | FAIL/BLOCK |
|---|---|---|---|---|---|
| AC-MVP-001 | CLI ejecutable localmente | FR-MVP-001 | salida `--version` | Devuelve versión sin error. | No ejecuta o depende de red. |
| AC-MVP-002 | Readiness pre-code | FR-MVP-002, FR-MVP-014 | `readiness_check.json` | Reporta estado y checks. | No detecta artefactos faltantes. |
| AC-MVP-003 | Reportes locales | FR-MVP-003, FR-MVP-010 | `outputs/reports/` | JSON/Markdown generados. | Sin evidencia persistente. |
| AC-MVP-004 | Activación MIASI | FR-MVP-004 | salida `miasi-required` | `miasi_required=true`. | IA/agentes sin MIASI. |
| AC-MVP-005 | Frontmatter válido | FR-MVP-005 | reporte de validación | Campos obligatorios presentes. | `doc_id`, `status`, `version` u `owner` faltante. |
| AC-MVP-006 | Artefacto estructurado | FR-MVP-006 | reporte por documento | Secciones mínimas presentes. | Documento vacío o decorativo. |
| AC-MVP-007 | Checklist pre-code evaluado | FR-MVP-007 | checklist PASS/FAIL | Todos los obligatorios pasan. | Obligatorio sin evidencia. |
| AC-MVP-008 | Cero API keys reales | FR-MVP-008, NFR-001 | `.env.example`, tests | Funciona sin secretos. | Requiere token real. |
| AC-MVP-009 | Dry-run por defecto | FR-MVP-009, NFR-004 | política/comando | No modifica archivos sin confirmación. | Acción destructiva sin aprobación. |
| AC-MVP-010 | Trazabilidad inicial | FR-MVP-015, NFR-007 | `traceability_matrix.md` | Objetivo → requisito → prueba conectado. | Requisitos huérfanos. |

## 3. Criterios Given/When/Then — MVP

### AC-GWT-001 — Validar readiness

```gherkin
Given un workspace DevPilot con carpeta docs
When ejecuto python -m devpilot_core readiness-check
Then el sistema genera un reporte JSON con estado general y lista de checks
And cada artefacto requerido aparece con exists true/false
```

### AC-GWT-002 — Detectar MIASI

```gherkin
Given un proyecto marcado como agent-assisted SDLC
When ejecuto python -m devpilot_core miasi-required
Then el sistema devuelve miasi_required true
And lista Agent Card, Tool Card, Policy Card, Eval Card, Human Approval Card y Observability Card
```

### AC-GWT-003 — Validar frontmatter

```gherkin
Given un documento Markdown sin doc_id
When ejecuto validate-artifact sobre el documento
Then el sistema devuelve FAIL
And el mensaje indica que falta doc_id
```

### AC-GWT-004 — Validar cero dependencia externa

```gherkin
Given un entorno local sin API keys reales
When ejecuto pytest -q y readiness-check
Then todas las pruebas del MVP pasan
And ningún comando intenta llamar servicios externos
```

## 4. Criterios de aceptación MVP+

| ID | Criterio | Requisitos | Evidencia | PASS | FAIL/BLOCK |
|---|---|---|---|---|---|
| AC-PLUS-001 | Workspace registrado | FR-PLUS-001 | `.devpilot/project.yaml` | Descriptor válido. | No hay unidad de workspace. |
| AC-PLUS-002 | Git read-only | FR-PLUS-002 | reporte Git | Status, branch y commit reportados. | Modifica repo sin permiso. |
| AC-PLUS-003 | Repo analysis | FR-PLUS-003 | repo report | Módulos/docs/tests detectados. | Escaneo fuera de política. |
| AC-PLUS-004 | Patch review dry-run | FR-PLUS-005 | patch report | Evalúa sin aplicar. | Patch aplicado automáticamente. |
| AC-PLUS-005 | Code review asistido | FR-PLUS-006 | hallazgos | Hallazgos con severidad y evidencia. | Recomendaciones sin evidencia. |
| AC-PLUS-006 | Refactor seguro | FR-PLUS-007 | refactor plan | Incluye tests y rollback. | Cambios irreversibles o sin pruebas. |
| AC-PLUS-007 | Entorno validado | FR-PLUS-008 | env report | Python, venv y dependencias reportadas. | Entorno ambiguo. |
| AC-PLUS-008 | Agentes controlados | FR-PLUS-010 | Agent/Policy/Eval cards | Agentes solo recomiendan en fase inicial. | Agente ejecuta sin aprobación. |

## 5. Criterios de aceptación post-MVP

| ID | Criterio | Requisitos | Evidencia esperada |
|---|---|---|---|
| AC-POST-001 | Desktop consume core | FR-POST-001 | UI ejecuta comandos o servicios del core sin duplicar lógica. |
| AC-POST-002 | Web controlada | FR-POST-002 | Auth, logging, threat model y despliegue documentados. |
| AC-POST-003 | Dashboard workspace | FR-POST-003 | Vista de gates, documentos, riesgos y trazas. |
| AC-POST-004 | Agentes especializados | FR-POST-004 | Cards, policies, evals, trazas y aprobación humana. |

## 6. Criterios de rechazo

Un incremento debe rechazarse si:

- introduce dependencia obligatoria de API externa en MVP;
- modifica archivos o repos sin dry-run y aprobación;
- agrega agente sin MIASI;
- agrega requerimiento crítico sin criterio de aceptación;
- genera reporte sin evidencia reproducible;
- rompe `pytest -q`;
- no deja trazabilidad hacia producto o requisito.

## 7. Estado

```yaml
acceptance_criteria_status: reviewed
ready_for_owner_approval: true
```
