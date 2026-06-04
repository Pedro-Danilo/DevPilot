---
title: "Traceability Matrix — DevPilot Local"
doc_id: "DEVPL-REQ-005"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-02"
updated: "2026-06-02"
approval: "approved_by_owner_pending_commit"
source_baseline: "SPRINT-PRECODE-01 product baseline approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---
# Traceability Matrix — DevPilot Local

## 1. Propósito

Este documento conecta objetivos de producto, requerimientos, historias, casos de uso, criterios de aceptación y pruebas esperadas. Su objetivo es impedir requisitos huérfanos y preparar los siguientes sprints de arquitectura, seguridad, calidad y construcción funcional.

## 2. Objetivos de producto base

| ID | Objetivo de producto |
|---|---|
| BG-001 | Profesionalizar el ciclo de vida de software con MIPSoftware como estándar ejecutable. |
| BG-002 | Mantener local-first, costo externo cero y privacidad por defecto. |
| BG-003 | Evitar acciones destructivas mediante dry-run, policy gates y aprobación humana. |
| BG-004 | Evolucionar de CLI a desktop y web como compromiso técnico. |
| BG-005 | Usar workspaces como unidad operativa de proyectos gestionados. |
| BG-006 | Incorporar Git, repos reales, patches, code review, refactor y despliegue progresivamente. |
| BG-007 | Activar MIASI y agentes controlados cuando haya IA, automatización inteligente o tool calling. |

## 3. Matriz producto → requisito → historia → caso → aceptación → prueba

| Objetivo | Requisito | Historia | Caso de uso | Criterio | Prueba/evidencia sugerida | Nivel |
|---|---|---|---|---|---|---|
| BG-001 | FR-MVP-001 | US-MVP-001 | UC-MVP-001 | AC-MVP-001 | `test_cli_version_outputs_version` | MVP |
| BG-005 | FR-MVP-002 | US-MVP-002 | UC-MVP-001 | AC-MVP-002 | `test_workspace_detects_docs_and_outputs` | MVP |
| BG-001 | FR-MVP-003 | US-MVP-003 | UC-MVP-001 | AC-MVP-003 | `test_readiness_check_reports_required_artifacts` | MVP |
| BG-001 | FR-MVP-004 | US-MVP-004 | UC-MVP-003 | AC-MVP-006 | `test_frontmatter_missing_doc_id_fails` | MVP |
| BG-001 | FR-MVP-005 | US-MVP-004 | UC-MVP-003 | AC-MVP-007 | `test_artifact_structure_validation` | MVP |
| BG-001 | FR-MVP-006 | US-MVP-008 | UC-MVP-004 | AC-MVP-008 | `test_pre_code_checklist_gate` | MVP |
| BG-007 | FR-MVP-007 | US-MVP-005 | UC-MVP-002 | AC-MVP-005 | `test_miasi_required_for_devpilot` | MVP |
| BG-001 | FR-MVP-008 | US-MVP-006 | UC-MVP-001 | AC-MVP-004 | `test_readiness_writes_reports` | MVP |
| BG-002 | FR-MVP-009 | US-MVP-001 | UC-MVP-001 | AC-MVP-009 | `pytest -q` sin API keys | MVP |
| BG-003 | FR-MVP-010 | US-MVP-007 | UC-MVP-003 | AC-MVP-010 | `test_dry_run_no_write` | MVP |
| BG-001 | FR-MVP-011 | US-MVP-012 | UC-MVP-003 | AC-GWT-003 | `test_error_messages_are_actionable` | MVP |
| BG-001 | FR-MVP-012 | US-MVP-009 | UC-MVP-004 | AC-MVP-011 | `test_traceability_has_no_orphans` | MVP |
| BG-007 | FR-MVP-013 | US-MVP-010 | UC-MVP-005 | AC-MVP-012 | `test_doc_agent_drafts_without_overwrite` | MVP |
| BG-007 | FR-MVP-014 | US-MVP-011 | UC-MVP-006 | AC-MVP-013 | `test_audit_agent_reports_findings` | MVP |
| BG-001 | FR-MVP-015 | US-MVP-006 | UC-MVP-001 | AC-MVP-004 | `test_reports_are_persisted` | MVP |
| BG-007 | FR-MVP-016 | US-MVP-010, US-MVP-011 | UC-MVP-005, UC-MVP-006 | AC-MVP-012, AC-MVP-013 | `test_agent_suggestions_do_not_decide_gate` | MVP |
| BG-005 | FR-PLUS-001 | US-PLUS-001 | UC-PLUS-001 | AC-PLUS-001 | `.devpilot/project.yaml` schema | MVP+ |
| BG-006 | FR-PLUS-002 | US-PLUS-002 | UC-PLUS-002 | AC-PLUS-002 | Git read-only report | MVP+ |
| BG-006 | FR-PLUS-003 | US-PLUS-003 | UC-PLUS-003 | AC-PLUS-003 | Repo scan report | MVP+ |
| BG-006 | FR-PLUS-004 | US-PLUS-004 | UC-PLUS-004 | AC-PLUS-004 | Env validation report | MVP+ |
| BG-006 | FR-PLUS-005 | US-PLUS-005 | UC-PLUS-005 | AC-PLUS-005 | Patch review dry-run report | MVP+ |
| BG-006 | FR-PLUS-006 | US-PLUS-006 | UC-PLUS-006 | AC-PLUS-006 | Code review report | MVP+ |
| BG-006 | FR-PLUS-007 | US-PLUS-007 | UC-PLUS-007 | AC-PLUS-007 | Refactor plan + rollback | MVP+ |
| BG-007 | FR-PLUS-008 | US-PLUS-008 | UC-PLUS-008 | AC-PLUS-008 | Agent/Policy/Eval cards | MVP+ |
| BG-001 | FR-PLUS-009 | US-PLUS-009 | UC-PLUS-008 | AC-PLUS-009 | JSONL trace event | MVP+ |
| BG-003 | FR-PLUS-010 | US-PLUS-005, US-PLUS-008 | UC-PLUS-005, UC-PLUS-008 | AC-PLUS-005, AC-PLUS-008 | Approval request log | MVP+ |
| BG-004 | FR-POST-001 | US-POST-001 | UC-POST-001 | AC-POST-001 | Desktop uses core | Post-MVP |
| BG-004 | FR-POST-002 | US-POST-002 | UC-POST-002 | AC-POST-002 | Web threat model/auth | Post-MVP |
| BG-005 | FR-POST-003 | US-POST-001, US-POST-002 | UC-POST-001, UC-POST-002 | AC-POST-003 | Dashboard workspace | Post-MVP |
| BG-007 | FR-POST-004 | US-POST-003 | UC-POST-003 | AC-POST-004 | Multiagent eval/policy | Post-MVP |
| BG-006 | FR-POST-005 | US-POST-004 | UC-POST-004 | N/A future | Release checklist | Post-MVP |

## 4. Matriz requerimiento → tipo de prueba

| Requisito | Tipo de prueba | Nombre sugerido |
|---|---|---|
| FR-MVP-001 | CLI smoke test | `test_cli_version_outputs_version` |
| FR-MVP-002 | Unit | `test_workspace_detects_docs_and_outputs` |
| FR-MVP-003 | Unit/integration | `test_readiness_check_reports_required_artifacts` |
| FR-MVP-004 | Unit | `test_frontmatter_missing_doc_id_fails` |
| FR-MVP-005 | Unit | `test_artifact_structure_validation` |
| FR-MVP-006 | Unit/integration | `test_pre_code_checklist_gate` |
| FR-MVP-007 | Unit | `test_miasi_required_for_devpilot` |
| FR-MVP-008 | Integration | `test_report_writer_outputs_json_and_md` |
| FR-MVP-009 | Hermetic/offline | `test_no_api_key_required` |
| FR-MVP-010 | Safety | `test_dry_run_no_write` |
| FR-MVP-013 | Agent/mock | `test_doc_agent_drafts_without_overwrite` |
| FR-MVP-014 | Agent/mock | `test_audit_agent_reports_findings` |
| FR-PLUS-002 | Git adapter | `test_git_status_read_only` |
| FR-PLUS-005 | Patch safety | `test_patch_review_does_not_apply_patch` |
| FR-PLUS-008 | MIASI | `test_agent_requires_cards_policy_eval` |

## 5. Estado

```yaml
traceability_status: approved
ready_for_architecture_sprint: true
```
