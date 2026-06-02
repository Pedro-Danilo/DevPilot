---
title: "Traceability Matrix — DevPilot Local"
doc_id: "DEVPL-REQ-005"
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
# Traceability Matrix — DevPilot Local

## 1. Propósito

Esta matriz conecta objetivos de producto, documentos fuente, requerimientos, historias, casos de uso, criterios de aceptación y pruebas/evidencias previstas. Su función es impedir que existan objetivos sin requerimientos, requerimientos sin aceptación o capacidades sin evidencia.

## 2. Objetivos de negocio/producto

| ID | Objetivo | Fuente |
|---|---|---|
| BG-001 | Profesionalizar el ciclo de vida completo de desarrollo de software personal. | `product_vision.md` |
| BG-002 | Convertir MIPSoftware y MIASI en gates verificables. | `business_case.md` |
| BG-003 | Mantener enfoque local-first, privacidad y costo externo cero en MVP. | `mvp_scope.md` |
| BG-004 | Evolucionar obligatoriamente CLI → MVP+ → desktop → web. | `product_roadmap.md` |
| BG-005 | Gestionar proyectos mediante workspaces. | `product_vision.md`, `stakeholder_map.md` |
| BG-006 | Integrar Git, repos reales, patch review, refactor seguro y code review en MVP+. | `mvp_scope.md` |
| BG-007 | Activar MIASI para agentes, tool calling, LLMs y automatización inteligente. | `product_vision.md`, `devpl_pre_0107_refinement_review.md` |

## 3. Matriz producto → requerimiento → historia → caso de uso → aceptación → evidencia

| Objetivo | Requisito | Historia | Caso de uso | Criterio | Evidencia/prueba esperada | Fase |
|---|---|---|---|---|---|---|
| BG-001 | FR-MVP-002 | US-MVP-002 | UC-MVP-001 | AC-MVP-002 | `readiness_check.json`, test de artefactos mínimos | MVP |
| BG-002 | FR-MVP-005 | US-MVP-003 | UC-MVP-003 | AC-MVP-005 | test de frontmatter inválido | MVP |
| BG-002 | FR-MVP-007 | US-MVP-007 | UC-MVP-004 | AC-MVP-007 | reporte checklist pre-code | MVP |
| BG-003 | FR-MVP-008 | US-MVP-001 | UC-MVP-001 | AC-MVP-008 | `pytest -q` sin `.env` real | MVP |
| BG-003 | FR-MVP-009 | US-MVP-006 | UC-MVP-003 | AC-MVP-009 | política dry-run, test de no modificación | MVP |
| BG-004 | FR-POST-001 | US-POST-001 | N/A futuro | AC-POST-001 | diseño desktop consume core | Post-MVP |
| BG-004 | FR-POST-002 | US-POST-002 | N/A futuro | AC-POST-002 | threat model web y auth | Post-MVP |
| BG-005 | FR-PLUS-001 | US-PLUS-001 | UC-PLUS-001 | AC-PLUS-001 | `.devpilot/project.yaml` | MVP+ |
| BG-006 | FR-PLUS-002 | US-PLUS-002 | UC-PLUS-002 | AC-PLUS-002 | reporte Git read-only | MVP+ |
| BG-006 | FR-PLUS-003 | US-PLUS-003 | UC-PLUS-003 | AC-PLUS-003 | repo scan report | MVP+ |
| BG-006 | FR-PLUS-005 | US-PLUS-004 | UC-PLUS-004 | AC-PLUS-004 | patch review dry-run report | MVP+ |
| BG-006 | FR-PLUS-006 | US-PLUS-005 | UC-PLUS-004 | AC-PLUS-005 | code review report | MVP+ |
| BG-006 | FR-PLUS-007 | US-PLUS-006 | UC-PLUS-005 | AC-PLUS-006 | refactor plan + tests | MVP+ |
| BG-006 | FR-PLUS-008 | US-PLUS-007 | N/A | AC-PLUS-007 | env validation report | MVP+ |
| BG-007 | FR-MVP-004 | US-MVP-004 | UC-MVP-002 | AC-MVP-004 | salida `miasi-required` | MVP |
| BG-007 | FR-PLUS-010 | US-PLUS-008 | UC-PLUS-006 | AC-PLUS-008 | Agent/Policy/Eval cards + approval | MVP+ |
| BG-001 | FR-MVP-015 | US-MVP-008 | UC-MVP-004 | AC-MVP-010 | matriz de trazabilidad actualizada | MVP |
| BG-001 | FR-MVP-011 | US-MVP-009 | UC-MVP-003 | AC-GWT-003 | mensajes de error accionables | MVP |

## 4. Matriz requerimiento → tipo de prueba

| Requisito | Tipo de prueba | Nombre sugerido |
|---|---|---|
| FR-MVP-001 | CLI smoke test | `test_cli_version_outputs_version` |
| FR-MVP-002 | Unit/integration | `test_readiness_check_reports_required_artifacts` |
| FR-MVP-003 | Integration | `test_readiness_writes_json_report` |
| FR-MVP-004 | Unit | `test_miasi_required_for_agent_assisted_project` |
| FR-MVP-005 | Unit | `test_frontmatter_validator_rejects_missing_doc_id` |
| FR-MVP-006 | Unit | `test_artifact_validator_requires_sections` |
| FR-MVP-007 | Unit/integration | `test_pre_code_checklist_pass_fail` |
| FR-MVP-008 | Environment test | `test_project_runs_without_real_api_keys` |
| FR-MVP-009 | Security test | `test_mutating_commands_default_to_dry_run` |
| FR-MVP-015 | Unit | `test_traceability_links_product_requirement_test` |
| FR-PLUS-001 | Unit | `test_workspace_descriptor_created_or_detected` |
| FR-PLUS-002 | Integration | `test_git_status_is_read_only` |
| FR-PLUS-005 | Security/integration | `test_patch_review_does_not_apply_patch` |
| FR-PLUS-010 | Agentic eval | `test_agent_actions_require_policy_and_approval` |

## 5. Brechas intencionales pendientes

| Brecha | Motivo | Sprint esperado |
|---|---|---|
| C4 detallado de workspace | Pertenece a arquitectura. | SPRINT-PRECODE-03 |
| Threat model de Git/patch/refactor | Pertenece a seguridad. | SPRINT-PRECODE-04 |
| Estrategia concreta de tests | Pertenece a calidad. | SPRINT-PRECODE-05 |
| Agent Cards completas | Pertenece a MIASI aplicado. | SPRINT-PRECODE-06 |

## 6. Estado

```yaml
traceability_status: reviewed
ready_for_owner_approval: true
```
