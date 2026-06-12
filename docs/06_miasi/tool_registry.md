---
title: "Tool Registry — DevPilot Local"
doc_id: "DEVPL-MIASI-TOOL-REGISTRY"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
baseline_role: "precode_approved_baseline"
---

# Tool Registry — DevPilot Local

| Tool ID | Nombre | Fase | Side effect | Riesgo | Estado |
|---|---|---|---|---:|---|
| `artifact.read` | read_artifact | MVP | lectura | Bajo | Planned |
| `artifact.frontmatter.validate` | validate_frontmatter | MVP | ninguno | Bajo | Planned |
| `artifact.structure.validate` | validate_artifact_structure | MVP | ninguno | Bajo | Planned |
| `checklist.precode.run` | run_precode_checklist | MVP | ninguno | Bajo | Planned |
| `miasi.required` | miasi_required | MVP | ninguno | Bajo | Existing/minimal |
| `report.write` | write_report | MVP | escritura controlada | Medio | Planned |
| `trace.append` | append_trace_event | MVP | escritura controlada | Medio | Planned |
| `document.draft.generate` | generate_draft_document | MVP | escritura opcional | Medio | Planned |
| `documentation.audit` | audit_documentation | MVP | reporte | Medio | Planned |
| `git.status` | git_status | MVP+ | lectura | Medio | Implemented |
| `git.diff` | git_diff | MVP+ | lectura | Medio | Implemented |
| `git.branches` | git_branches_read_only | MVP+ | lectura | Medio | Implemented |
| `git.tags` | git_tags_read_only | MVP+ | lectura | Medio | Implemented |
| `git.log` | git_log_read_only | MVP+ | lectura | Medio | Implemented |
| `git.diff_report` | git_diff_report_read_only | MVP+ | reporte | Medio | Implemented |
| `repo.inventory` | repo_inventory | MVP+ | lectura | Medio | Planned |
| `repo.dependency_graph` | repo_dependency_graph_read_only | MVP+ | reporte | Medio | Implemented-initial |
| `repo.analyze` | repo_analyze_read_only | MVP+ | reporte | Medio | Implemented-initial |
| `repo.architecture_drift` | repo_architecture_drift_read_only | MVP+ | reporte | Medio | Implemented-initial |
| `repo.quality_gate` | repo_quality_gate_dry_run | MVP+ | reporte dry-run | Alto | Implemented-initial |
| `patch.parse` | parse_patch | MVP+ | ninguno | Medio | Planned |
| `patch.dry_run` | patch_dry_run | MVP+ | simulación | Alto | Planned |
| `patch.check` | patch_preflight_check | MVP+ | simulación dry-run | Alto | Implemented-initial |
| `code.review` | code_review | MVP+ | reporte | Alto | Planned |
| `tests.run` | run_tests_controlled | MVP+ | ejecución controlada | Alto | Planned |
| `model.call.mock` | call_mock_model | MVP | ninguno | Bajo | Planned |
| `model.call.local` | call_local_model | MVP+ | cómputo local | Medio | Planned |
| `model.call.external` | call_external_model | MVP+ | red/costo | Alto | Disabled by default |

## Política

Toda herramienta nueva debe agregarse a este registro antes de implementarse.

## Estado operacional de `tests.run` — FUNC-SPRINT-32

`tests.run` pasa de `planned` a `implemented-initial` como herramienta MIASI de ejecución controlada. Su implementación reside en `devpilot_core.testing.TestsRunTool` y usa `SafeSubprocessRunner` como frontera de ejecución.

Restricciones:

- requiere aprobación humana para `tests.run/execute/<profile>`;
- solo ejecuta perfiles definidos en `.devpilot/testing/test_profiles.json`;
- no acepta comandos arbitrarios;
- no usa `shell=True`;
- conserva `PathGuard`, `SecretGuard`, `CostGuard` y `ApprovalPolicyChecker` en el flujo.

Perfiles iniciales: `smoke`, `unit`, `all`.


## Estado operacional GitAdapter v2 — FUNC-SPRINT-35

`git.branches`, `git.tags`, `git.log` y `git.diff_report` quedan declaradas como tools read-only de Fase C. No requieren approval porque no modifican archivos, index ni historial, pero siguen sujetas a `GIT_READ_ALLOW`, `PolicyEngine`, allowlist interna y ausencia de `shell=True`.

## Estado operacional DependencyGraph — FUNC-SPRINT-36

`repo.dependency_graph` queda declarada como tool read-only de Fase C. No requiere approval porque no modifica archivos ni ejecuta código analizado. Su implementación usa AST y debe permanecer local-first, sin red, sin APIs externas y sin modelos.

## Estado operacional RepoAnalyzer v2 — FUNC-SPRINT-37

`repo.analyze` queda declarada como tool read-only de Fase C. No requiere approval porque no modifica archivos ni ejecuta código analizado. Su implementación consolida inventario, DependencyGraph y GitAdapter para producir señales heurísticas de salud de repositorio. Debe permanecer local-first, sin red, sin APIs externas, sin modelos y sin emisión de secretos crudos.


## Estado operacional Architecture/code drift — FUNC-SPRINT-38

`repo.architecture_drift` queda declarada como tool read-only de Fase C. No requiere approval porque no modifica archivos ni ejecuta código analizado. Su implementación compara arquitectura documentada contra módulos reales mediante heurísticas locales, DependencyGraph y RepoAnalyzer. Debe permanecer local-first, sin red, sin APIs externas, sin modelos y sin cambios automáticos en documentación o código.


## Estado operacional Repo Quality Gate — FUNC-SPRINT-39

`repo.quality_gate` queda declarada como tool MIASI de Fase C en estado `implemented-initial`. No requiere approval porque no modifica archivos ni aplica patches; aun así se clasifica como riesgo alto por su rol de gate antes de cambios de repositorio. Su implementación es dry-run, local-first y basada en `ReviewRulePack`, `RepoAnalyzer`, `CodeReviewEngine`, `PatchReviewEngine` opcional y `PolicyEngine`.

Restricciones: sin Git write, sin patch apply, sin red, sin APIs externas, sin modelos y sin secretos crudos en reportes. Los warnings son asesoría por defecto; findings `FAIL` y `BLOCK` de motores integrados se propagan al resultado del gate.


## Estado operacional Patch preflight — FUNC-SPRINT-40

`patch.check` queda declarada como tool MIASI de Fase C en estado `implemented-initial`. No requiere approval porque no aplica patches ni modifica el workspace productivo; aun así se clasifica como riesgo alto por ejecutar una verificación Git local controlada.

Restricciones: solo `git apply --check` mediante `SafeSubprocessRunner` y allowlist explícita, sin `shell=True`, sin Git write, sin patch apply, sin sandbox, sin rollback, sin red, sin APIs externas, sin modelos y sin secretos crudos en reportes. `BLOCK` representa riesgo/política/seguridad; `FAIL` representa no aplicabilidad del patch.


## Estado operacional PatchSandbox

`patch.sandbox` queda declarado como tool MIASI de riesgo alto con side effect `controlled_write`. La tool ejecuta `PatchPreflightEngine`, aplica el patch solo dentro de `outputs/sandbox`, genera un `ChangeSet` con hashes antes/después y mantiene bloqueada cualquier aplicación sobre el workspace productivo.

Criterios PASS: sandbox bajo `outputs/sandbox`, ChangeSet sin contenido crudo, preflight obligatorio, no Git write y reportes auditables.

Criterios BLOCK: mutación productiva, omisión de preflight, secretos crudos en evidencia, pruebas sin aprobación `tests.run`, rollback ejecutable no autorizado o escritura fuera de rutas runtime controladas.

Riesgos: capacidad `implemented-initial`; el rollback ejecutable pertenece a `FUNC-SPRINT-42` y la aplicación real de patches al workspace productivo permanece fuera de alcance.


## Estado operacional RollbackManager — FUNC-SPRINT-42

Se agregan tools `rollback.plan`, `rollback.list`, `rollback.show` y `rollback.execute`. La capacidad es `implemented-initial`: permite crear y consultar rollback points locales, pero no habilita restauración automática. `rollback.execute` existe como frontera CLI gated y bloqueada por diseño hasta que futuros sprints definan restore semantics, pruebas post-rollback y aprobación humana completa.


## Estado operacional RefactorExecutor — FUNC-SPRINT-43

`refactor.sandbox` queda declarado como tool `implemented-initial`, de riesgo alto y approval obligatorio. Ejecuta únicamente transformaciones mecánicas determinísticas en sandbox, produce `ChangeSet`, invoca `RollbackManager` para rollback plan y permite pruebas fijas en sandbox con approval separado de `tests.run`.

La herramienta no habilita escritura productiva, Git write, refactors semánticos, ejecución arbitraria ni APIs externas.


## Estado operacional RepoEngineeringGate

- Tool ID: `repo.engineering_gate`.
- Estado: `implemented-initial`.
- Riesgo: `high`.
- Side effect: `report`.
- Approval: no requerido porque es read-only/report-only.
- Policy rule: `ENGINEERING_GATE_READ_ONLY_ALLOW`.
- Comando: `python -m devpilot_core repo engineering-gate --profile full --json --write-report`.

La herramienta cierra Fase C de forma reproducible, pero no habilita Git write, patch apply productivo, refactor productivo, deploy, LLMs ni APIs externas.
