---
title: "Traceability Matrix — DevPilot Local"
doc_id: "DEVPL-REQ-005"
status: "approved"
version: "1.3.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "DEVPL-GSDLC-00-D"
updated: "2026-08-14"
approval: "approved_by_owner_direction"
source_baseline: "SPRINT-PRECODE-01 product baseline approved"
current_repo: "WORKING descendant of 00-C commit 3c2dbff91eaddbbb92af41bc7ac6b9aacb309ba0"
change_policy: "controlled_changes_via_DEVPL-GSDLC"
program_id: "DEVPL-GSDLC"
source_parent_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
source_working_commit: "3c2dbff91eaddbbb92af41bc7ac6b9aacb309ba0"
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
| GSDLC-OBJ-001 | Conducir el normal journey completo desde UI con estado/next action persistentes. |
| GSDLC-OBJ-002 | Crear/abrir/importar y bootstrappear proyectos desde DevPilot. |
| GSDLC-OBJ-003 | Ejecutar MIPSoftware/MIASI y autoría manual/import/agent-assisted como workflows gobernados. |
| GSDLC-OBJ-004 | Integrar planning, coding, tests, quality, Git, evidence y release. |
| GSDLC-OBJ-005 | Mantener local-first, seguridad, RBAC, costos y autoridad humana. |
| GSDLC-OBJ-006 | Demostrar el producto mediante el piloto `inventory-sales-local`. |

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
gsdlc_delta_coverage: 100%
gsdlc_orphan_requirements: 0
gsdlc_requirements_total: 31
source_working_commit: 5c6d0b2f060a5845769505d650754ef786542e99
ready_for_gsdlc_00_c_after_00_b_closure: true
```

## 6. Trazabilidad DEVPL-GSDLC — vision → requirement → backlog → acceptance gate

Esta matriz cubre **exclusivamente el delta successor DEVPL-GSDLC**. La matriz histórica de secciones 3–4 permanece como evidencia acumulativa.

| Requisito | Objetivo GSDLC | Backlog owner | Milestone | Future acceptance gate | Security/control/test owner | Status |
|---|---|---|---|---|---|---|
| GSDLC-FR-001 | GSDLC-OBJ-001 | DEVPL-GSDLC-01 | M1 | Al abrir o reanudar un proyecto la UI muestra todos los campos mínimos y el next action coincide con el workflow determinístico. | DEVPL-GSDLC-01 / security focal | planned |
| GSDLC-FR-002 | GSDLC-OBJ-001 | DEVPL-GSDLC-01 | M1 | Restart conserva fase/paso; estados de plataforma/runtime no sobrescriben el estado de ingeniería. | DEVPL-GSDLC-01 / focal acceptance | planned |
| GSDLC-FR-003 | GSDLC-OBJ-005 | DEVPL-GSDLC-02 | M1 | Login/logout/session expiry/revocation PASS; identidad del actor deriva de sesión. | DEVPL-GSDLC-02 / focal acceptance | planned |
| GSDLC-SEC-001 | GSDLC-OBJ-005 | DEVPL-GSDLC-02 | M1 | Wrong role, revoked/expired session, scope mismatch y actor spoofing quedan BLOCK; approval válido queda auditado. | DEVPL-GSDLC-02 / security focal | planned |
| GSDLC-SEC-002 | GSDLC-OBJ-005 | DEVPL-GSDLC-02 | M1 | Bind local-only; enterprise capabilities continúan POLICY-BLOCKED y tests históricos PASS. | DEVPL-GSDLC-02 / security focal | planned |
| GSDLC-FR-004 | GSDLC-OBJ-002 | DEVPL-GSDLC-03 | M1 | Las tres opciones son accesibles desde UI y conducen a flujos tipados sin shell arbitrario. | DEVPL-GSDLC-03 / focal acceptance | planned |
| GSDLC-FR-005 | GSDLC-OBJ-002 | DEVPL-GSDLC-03 | M1 | Dry-run no muta; execute solo dentro del workspace; Git/venv/deps verificados; rollback/evidence disponibles. | DEVPL-GSDLC-03 / security focal | planned |
| GSDLC-SEC-003 | GSDLC-OBJ-005 | DEVPL-GSDLC-03 | M1 | No existe endpoint/UI que acepte comandos arbitrarios; path traversal y command injection quedan BLOCK. | DEVPL-GSDLC-03 / security focal | planned |
| GSDLC-FR-006 | GSDLC-OBJ-003 | DEVPL-GSDLC-04 | M2 | Editor guarda draft gobernado, validators actualizan lifecycle y no se puede saltar un gate obligatorio. | DEVPL-GSDLC-04 / security focal | planned |
| GSDLC-FR-007 | GSDLC-OBJ-003 | DEVPL-GSDLC-04 | M2 | Import no sobrescribe aprobado sin review; archivos inválidos/maliciosos quedan bloqueados; provenance persistida. | DEVPL-GSDLC-04 / focal acceptance | planned |
| GSDLC-FR-008 | GSDLC-OBJ-001 | DEVPL-GSDLC-12 | M6 | Cambio externo detectado; aprobación no permanece vigente silenciosamente; diff y revalidación visibles. | DEVPL-GSDLC-12 / focal acceptance | planned |
| GSDLC-GOV-001 | GSDLC-OBJ-003 | DEVPL-GSDLC-05 | M2 | No se avanza a un step con prerequisitos/gates incumplidos; registry versionado y validado. | DEVPL-GSDLC-05 / security focal | planned |
| GSDLC-GOV-002 | GSDLC-OBJ-003 | DEVPL-GSDLC-05 | M2 | Agent/tool no registrado o sin policy/eval queda bloqueado; human approval se respeta. | DEVPL-GSDLC-05 / security focal | planned |
| GSDLC-FR-009 | GSDLC-OBJ-003 | DEVPL-GSDLC-05 | M2 | Advisor nunca inventa capabilities; opciones bloqueadas explican razón; salida estable para mismo estado. | DEVPL-GSDLC-05 / security focal | planned |
| GSDLC-NFR-001 | GSDLC-OBJ-005 | DEVPL-GSDLC-05 | M2 | Proyecto puede alcanzar PRE_CODE_READY por Manual/Paste/Upload con network_used=false y external_cost=0. | DEVPL-GSDLC-05 / focal acceptance | planned |
| GSDLC-FR-010 | GSDLC-OBJ-005 | DEVPL-GSDLC-06 | M3 | Sin provider configurado existe fallback mock/local; rutas externas requieren opt-in/policy y dejan trazabilidad. | DEVPL-GSDLC-06 / focal acceptance | planned |
| GSDLC-NFR-002 | GSDLC-OBJ-005 | DEVPL-GSDLC-06 | M3 | Budget excedido bloquea o requiere approval según policy; UI muestra estimación y consumo. | DEVPL-GSDLC-06 / security focal | planned |
| GSDLC-FR-011 | GSDLC-OBJ-003 | DEVPL-GSDLC-07 | M3 | Draft incluye provenance/model/context; apply requiere review/policy/approval; agent self-approval bloqueado. | DEVPL-GSDLC-07 / security focal | planned |
| GSDLC-FR-012 | GSDLC-OBJ-003 | DEVPL-GSDLC-07 | M3 | Respuesta sin evidencia suficiente no promueve afirmación a artefacto aprobado; citations navegables. | DEVPL-GSDLC-07 / security focal | planned |
| GSDLC-GOV-003 | GSDLC-OBJ-005 | DEVPL-GSDLC-07 | M3 | Tests demuestran que outputs LLM no pueden sobreescribir gate/policy/state machine. | DEVPL-GSDLC-07 / security focal | planned |
| GSDLC-FR-013 | GSDLC-OBJ-004 | DEVPL-GSDLC-08 | M4 | Coverage de requisitos planificados =100% o gaps explícitos; owner puede editar/rechazar antes de freeze. | DEVPL-GSDLC-08 / focal acceptance | planned |
| GSDLC-FR-014 | GSDLC-OBJ-004 | DEVPL-GSDLC-09 | M5 | Cada story mantiene context pack, plan, diff y estado; no aplica cambios fuera de manifest. | DEVPL-GSDLC-09 / focal acceptance | planned |
| GSDLC-FR-015 | GSDLC-OBJ-004 | DEVPL-GSDLC-09 | M5 | Apply solo tras validación/approval requerido; diff exacto y rollback evidence disponibles. | DEVPL-GSDLC-09 / security focal | planned |
| GSDLC-FR-016 | GSDLC-OBJ-004 | DEVPL-GSDLC-10 | M5 | Tests seleccionados ejecutan; blockers=0; resultados correlacionados a story y requirement. | DEVPL-GSDLC-10 / focal acceptance | planned |
| GSDLC-FR-017 | GSDLC-OBJ-004 | DEVPL-GSDLC-10 | M5 | Commit contiene solo paths autorizados; force-push/reset-hard/rebase automáticos siguen bloqueados. | DEVPL-GSDLC-10 / focal acceptance | planned |
| GSDLC-GOV-004 | GSDLC-OBJ-004 | DEVPL-GSDLC-10 | M5 | Evidence coverage del flujo cerrado=100%; ids permiten navegar acción→policy→approval→result→commit. | DEVPL-GSDLC-10 / security focal | planned |
| GSDLC-FR-018 | GSDLC-OBJ-004 | DEVPL-GSDLC-11 | M6 | Release no progresa con blockers; package reproducible, rollback verificable y tag gobernado. | DEVPL-GSDLC-11 / focal acceptance | planned |
| GSDLC-NFR-003 | GSDLC-OBJ-001 | DEVPL-GSDLC-12 | M6 | Restart conserva progreso; divergencias producen reconciliación/REVALIDATION_REQUIRED, no estado silenciosamente inválido. | DEVPL-GSDLC-12 / focal acceptance | planned |
| GSDLC-UX-001 | GSDLC-OBJ-001 | DEVPL-GSDLC-12 | M6 | Browser acceptance demuestra flujo completo sin comandos de usuario; bridges restantes son opcionales/diagnóstico y clasificados. | DEVPL-GSDLC-12 / security focal | planned |
| GSDLC-GOV-005 | GSDLC-OBJ-005 | DEVPL-GSDLC-12 | M6 | Historical sweep clasifica impacted contracts; 0 global assertions sin scope; history facts permanecen verificables. | DEVPL-GSDLC-12 / focal acceptance | planned |
| GSDLC-GOV-006 | GSDLC-OBJ-006 | DEVPL-GSDLC-13 | M7 | 02-B alcanza sus gates desde Guided SDLC UI; operator solo audita/evidence; workspace source attribution documentada. | DEVPL-GSDLC-13 / focal acceptance | planned |

### 6.1 Cobertura del delta

```yaml
gsdlc_requirements_total: 31
gsdlc_requirements_traced: 31
gsdlc_traceability_coverage: 100%
gsdlc_orphan_requirements: 0
source_working_commit: 5c6d0b2f060a5845769505d650754ef786542e99
```

### 6.2 Reglas de seguridad de trazabilidad

- `SEC` y requisitos agentic mantienen owner de control/prueba explícito.
- Un requisito `planned` no acredita capability implementada.
- La trazabilidad futura deberá extenderse a story/test/trace/commit conforme cierren GSDLC-08→13.
- Los contratos históricos continúan scoped a su hito y no pueden reemplazar el successor gate.

## 7. Trazabilidad histórica de cierre POST-H-EVAL-002-01-D

| Requisito de cierre | Evidencia autoritativa | Contrato | Resultado |
|---|---|---|---|
| Preservar RERUN-02 como forense | `PILOT-E2E-001-RUN-05B-RERUN-02` | no promoción, no Finalize | `BLOCK/FORENSIC-ONLY` |
| Aceptación browser de repo 326 | `PILOT-E2E-001-RUN-05B-RERUN-03` | 5 rutas, 8 negativos, 23 operaciones | `PASS` |
| Correlación HTTP manual | resumen HAR sanitizado | `13/13` | `PASS` |
| Bridges | registro reconciliado | `8/8` | `PASS` |
| Evidencia visual | ZIP browser cerrado | 13 viewport + 5 full-page | `PASS` |
| Stop seguro | `01_stop_verification.json` | PIDs registrados, puertos libres | `PASS` |
| Finalize idempotente | ledger y finalization report | `finalize_count=1` | `PASS` |
| Severidad y secretos | auditoría independiente | `S0=0`, `S1=0`, exposición `0` | `PASS` |
| Cierre documental | `repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip` | diff funcional `0` | pendiente de regresión Windows |

Contrato gobernante:

```text
tests/test_post_h_eval_002_01_d_governance_closure_327.py
```

Transición autorizada:

```text
current_micro_sprint = POST-H-EVAL-002-02-A
next_micro_sprint = POST-H-EVAL-002-02-B
```

## 9. DEVPL-GSDLC-00-D — Security/control/test traceability

La arquitectura objetivo de 00-C se transforma aquí en obligaciones de seguridad y prueba. Cada amenaza crítica debe tener control, owner de implementación futura y estrategia verificable.

| Threat | Control | Requisito relacionado | Backlog owner | Test/evidence future |
|---|---|---|---|---|
| GSDLC-TM-001 | GSDLC-CTRL-001 | GSDLC-SEC-001 | GSDLC-02 | auth/session negative suite + revocation evidence |
| GSDLC-TM-002 | GSDLC-CTRL-002 | GSDLC-SEC-002 | GSDLC-02 | RBAC/approval bypass negatives + actor/role evidence |
| GSDLC-TM-003 | GSDLC-CTRL-003 | GSDLC-SEC-001 | GSDLC-02 | origin/CSRF negative browser/API tests |
| GSDLC-TM-004 | GSDLC-CTRL-004 | GSDLC-SEC-003 | GSDLC-03 | path traversal/junction/symlink negative tests |
| GSDLC-TM-005 | GSDLC-CTRL-005 | GSDLC-FR-007 | GSDLC-04 | malicious upload/import fixtures + provenance evidence |
| GSDLC-TM-006 | GSDLC-CTRL-006 | GSDLC-FR-010 | GSDLC-04/GSDLC-11 | external edit race/restart reconciliation tests |
| GSDLC-TM-007 | GSDLC-CTRL-007 | GSDLC-FR-005 | GSDLC-03 | dependency-plan negative tests + lock/source evidence |
| GSDLC-TM-008 | GSDLC-CTRL-008 | GSDLC-GOV-002 | GSDLC-07/GSDLC-09 | unsafe patch rejection + review/approval evidence |
| GSDLC-TM-009 | GSDLC-CTRL-009 | GSDLC-GOV-002 | GSDLC-07 | prompt/tool injection negative suite |
| GSDLC-TM-010 | GSDLC-CTRL-010 | GSDLC-SEC-003 | GSDLC-03/GSDLC-09 | cross-workspace/capability misuse negatives |
| GSDLC-TM-011 | GSDLC-CTRL-011 | GSDLC-NFR-002 | GSDLC-06/GSDLC-07 | secret egress negatives + provider routing evidence |
| GSDLC-TM-012 | GSDLC-CTRL-012 | GSDLC-GOV-003 | GSDLC-06/GSDLC-07 | budget/loop exhaustion tests |
| GSDLC-TM-013 | GSDLC-CTRL-013 | GSDLC-SEC-002 | GSDLC-02/GSDLC-09 | stale approval negative matrix |
| GSDLC-TM-014 | GSDLC-CTRL-014 | GSDLC-FR-017 | GSDLC-09 | Git no-go/rollback/corruption tests |
| GSDLC-TM-015 | GSDLC-CTRL-015 | GSDLC-GOV-004 | GSDLC-09/GSDLC-11 | evidence tamper/freshness tests |
| GSDLC-TM-016 | GSDLC-CTRL-016 | GSDLC-FR-002 | GSDLC-01/GSDLC-11 | restart/state reconciliation tests |
| GSDLC-TM-017 | GSDLC-CTRL-017 | GSDLC-FR-004 | GSDLC-03 | malicious repo import fixtures |
| GSDLC-TM-018 | GSDLC-CTRL-018 | GSDLC-FR-018 | GSDLC-10/GSDLC-11 | package substitution/rollback/reproducibility tests |

### 9.1 Cobertura

```text
gsdlc_security_threats_total: 18
gsdlc_security_threats_traced: 18
gsdlc_security_traceability_coverage: 100%
gsdlc_critical_threats_without_control: 0
gsdlc_critical_threats_without_test_owner: 0
```

### 9.2 Historical-contract transition

Los tests históricos se enlazan a `docs/audits/devpl_gsdlc_00_d_historical_contract_sweep.json`. Un test histórico no se modifica por “hacer pasar pytest”; cualquier cambio requiere `classification=successor-needed` y aparece en el migration plan.
