---
title: "Tool Card — DevPilot Local"
doc_id: "DEVPL-MIASI-TOOL"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
source_baseline: "arquitectura approved + seguridad approved + calidad/operación approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
baseline_role: "precode_approved_baseline"
---

# Tool Card — DevPilot Local

## 1. Propósito

Este documento define el estándar de herramientas que podrán usar los agentes y flujos de DevPilot Local. Las herramientas son capacidades invocables por agentes, CLI o validadores: leer documentos, validar artefactos, inspeccionar Git, analizar repositorios, generar reportes, proponer patches, ejecutar pruebas o solicitar aprobación.

La regla central es:

> Ninguna herramienta puede modificar archivos, repositorios, configuración, dependencias, ambientes o despliegues sin modo dry-run, política explícita y aprobación humana cuando el riesgo lo exija.

## 2. Categorías de herramientas

| Categoría | Ejemplos | Fase | Riesgo |
|---|---|---|---:|
| Document tools | `read_artifact`, `validate_frontmatter`, `validate_template`, `generate_report` | MVP | Bajo/Medio |
| Checklist tools | `run_checklist`, `evaluate_gate`, `export_findings` | MVP | Bajo |
| Workspace tools | `detect_workspace`, `read_project_descriptor`, `list_docs` | MVP/MVP+ | Medio |
| Git tools | `git_status`, `git_diff`, `git_branch_info`, `git_log_summary` | MVP+ | Medio |
| Repo tools | `repo_tree`, `repo_inventory`, `dependency_inventory`, `risk_scan` | MVP+ | Medio/Alto |
| Patch tools | `parse_patch`, `patch_dry_run`, `patch_risk_score`, `rollback_plan` | MVP+ | Alto |
| Code tools | `code_review`, `static_check`, `refactor_plan`, `test_gap_analysis` | MVP+ | Alto |
| Test tools | `pytest_plan`, `run_tests_dry_run`, `collect_results` | MVP+ | Medio/Alto |
| Model tools | `call_model_mock`, `call_local_model`, `call_external_model` | MVP/MVP+ | Medio/Alto |
| Persistence tools | `write_report`, `append_trace`, `record_gate_result`, `read_sqlite_state` | MVP+ | Medio |
| Approval tools | `create_approval_request`, `record_decision` | MVP+ | Alto |
| MCP/API tools | `discover_connector`, `call_connector_dry_run` | Post-MVP | Alto |

## 3. Tool contract mínimo

Todo tool debe declarar:

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `tool_id` | Sí | Identificador estable. |
| `name` | Sí | Nombre invocable. |
| `purpose` | Sí | Propósito técnico. |
| `risk_level` | Sí | Bajo, medio, alto, crítico. |
| `side_effects` | Sí | Ninguno, lectura, escritura, ejecución, red. |
| `default_mode` | Sí | `dry_run` salvo justificación. |
| `allowed_paths` | Sí si toca filesystem | Rutas permitidas. |
| `forbidden_paths` | Sí si toca filesystem | Rutas prohibidas. |
| `requires_approval` | Sí | Reglas de aprobación. |
| `input_schema` | Sí | Estructura de entrada. |
| `output_schema` | Sí | Estructura de salida. |
| `error_schema` | Sí | Errores normalizados. |
| `observability_events` | Sí | Eventos requeridos. |
| `tests_required` | Sí | Pruebas mínimas. |

## 4. Herramientas permitidas en MVP

| Tool | Propósito | Side effect | Approval | Estado |
|---|---|---|---:|---|
| `read_artifact` | Leer documentos del workspace. | lectura | No | MVP |
| `validate_frontmatter` | Validar frontmatter YAML. | ninguno | No | MVP |
| `validate_artifact_structure` | Validar secciones obligatorias. | ninguno | No | MVP |
| `run_precode_checklist` | Ejecutar checklist pre-code. | ninguno | No | MVP |
| `miasi_required` | Determinar activación MIASI. | ninguno | No | MVP |
| `generate_draft_document` | Crear propuesta de documento en memoria o output seguro. | escritura controlada | Sí si escribe | MVP |
| `audit_documentation` | Generar hallazgos y recomendaciones. | ninguno/escritura reporte | No/Sí |
| `write_report` | Escribir reporte en `outputs/reports`. | escritura controlada | No si ruta segura | MVP |
| `append_trace_event` | Agregar evento JSONL. | escritura controlada | No si ruta segura | MVP |

## 5. Herramientas MVP+ con restricciones

| Tool | Propósito | Restricción |
|---|---|---|
| `git_status` | Leer estado Git. | Solo lectura. |
| `git_diff` | Leer diferencias. | Solo lectura. |
| `repo_inventory` | Inventariar estructura. | No lee secretos ni binarios grandes sin política. |
| `patch_dry_run` | Simular patch. | No aplica cambios reales. |
| `code_review` | Revisar código. | No modifica archivos. |
| `refactor_plan` | Proponer refactor. | Produce plan, no ejecución. |
| `run_tests` | Ejecutar pruebas. | Requiere modo controlado y timeout. |
| `external_model_call` | Usar API externa. | Requiere CostGuard, SecretGuard y consentimiento. |

## 6. Herramientas prohibidas por defecto

| Tool / Acción | Motivo |
|---|---|
| Borrar archivos de proyecto | Riesgo destructivo. |
| Sobrescribir archivos sin backup | Riesgo de pérdida de trabajo. |
| Ejecutar comandos arbitrarios | Riesgo de ejecución no controlada. |
| Modificar Git history | Riesgo de pérdida de trazabilidad. |
| Enviar código a APIs externas sin consentimiento | Riesgo de privacidad/secreto. |
| Leer `.env` real y exponer valores | Riesgo de secret leakage. |
| Aplicar patches directamente | Debe pasar por dry-run y aprobación. |
| Desplegar a servicios externos | Fuera de MVP. |

## 7. Matriz de riesgo de tools

| Riesgo | Ejemplo | Controles mínimos |
|---|---|---|
| Bajo | Validar frontmatter | logs, tests |
| Medio | Leer documentos | path allowlist, redacción |
| Alto | Leer repos/código | workspace policy, secret scan, trazas |
| Alto | Generar patch | dry-run, diff report, aprobación |
| Crítico | Aplicar patch, borrar, desplegar | bloqueado hasta fase posterior |

## 8. Criterios PASS

Una herramienta puede implementarse si:

- tiene Tool Card;
- tiene schema de entrada/salida;
- tiene pruebas;
- declara side effects;
- respeta dry-run;
- emite eventos;
- valida rutas;
- no filtra secretos;
- define errores y fallback;
- está registrada en Tool Registry.

## 9. Criterios BLOCK

Bloquear herramienta si:

- ejecuta comandos arbitrarios;
- modifica archivos sin backup/aprobación;
- lee rutas fuera del workspace;
- expone secretos;
- llama APIs externas sin CostGuard;
- carece de pruebas;
- carece de observabilidad.

## Actualización FUNC-SPRINT-12 — Tool calls simulados por Agent Runtime

Los agentes documentales MVP usan herramientas declaradas en `.devpilot/miasi/tool_registry.json`, pero Sprint 12 no incorpora un Tool Runtime industrial. Cada operación se representa como `AgentToolCall` y se somete a `PolicyEngine` antes de cualquier lectura o escritura controlada.

Herramientas usadas por los agentes MVP:

- `artifact.read` para lectura de documentos.
- `artifact.frontmatter.validate` y `artifact.structure.validate` mediante validadores existentes.
- `checklist.precode.run` para el checklist ejecutable.
- `document.draft.generate` para borradores bajo `outputs/drafts`.
- `policy.check` como gate de seguridad.

Criterios PASS:

- Tool declarada en Tool Registry.
- Operación permitida por PathGuard/SecretGuard/CostGuard.
- `dry-run` no escribe archivos.

Criterios BLOCK:

- Secreto sintético en payload.
- Ruta fuera del workspace.
- Intento de sobrescritura de draft.
- Tool no declarada o acción incompatible.

Riesgo: la ejecución real de herramientas externas, shell, Git write, patch apply y modelos externos sigue fuera de alcance.


## Actualización FUNC-SPRINT-14 — Git read-only y repo inventory

Sprint 14 implementa herramientas de repositorio en modo lectura, alineadas con `.devpilot/miasi/tool_registry.json`:

- `git.status`: consulta branch/status/diff stats mediante comandos Git allowlisted.
- `git.diff`: se cubre inicialmente como `diff --stat` y `diff --cached --stat`, sin exponer ni aplicar patches.
- `repo.inventory`: inventario local por categoría/tamaño/riesgo con detección de secretos sintéticos.

Criterios PASS:

- Operación read-only.
- Sin `git add`, `commit`, `checkout`, `reset`, `merge`, `rebase`, `tag` ni `push`.
- Sin lectura fuera del workspace.
- Sin emisión de contenido secreto crudo.
- Reportes solo bajo `outputs/reports`.

Criterios BLOCK:

- Comando Git no allowlisted.
- `shell=True` o ejecución arbitraria.
- Fuga de secreto.
- Intento de modificar repo o historial.

Riesgo: esta integración es preliminar y no reemplaza análisis industrial de dependencias, licencias, vulnerabilidades, secretos por entropía o revisión semántica de código.


## Actualización FUNC-SPRINT-15 — Herramientas de patch/code review

### Propósito

Registrar que `patch.parse`, `patch.dry_run` y `code.review` ya cuentan con implementación inicial local y determinística.

### Funcionamiento

- `patch.parse`: parsea unified diffs sin aplicar cambios.
- `patch.dry_run`: produce hallazgos sobre rutas, secretos, binarios, borrados y patrones riesgosos sin modificar el repositorio.
- `code.review`: ejecuta reglas estáticas iniciales sobre archivos locales sin emitir contenido crudo.

### Integración

Las herramientas están expuestas por los comandos `patch-review` y `code-review`, y siguen el contrato `CommandResult`, observabilidad JSONL, reportes opcionales y persistencia SQLite best-effort.

### Criterios PASS/BLOCK

PASS: análisis local, dry-run, sin escritura, sin secretos crudos. BLOCK: rutas fuera del workspace, `.env`, `.git`, secreto sintético o intento de aplicación.

### Riesgos

Implementación preliminar. No reemplaza SAST/SCA, linters, revisión humana, evaluación semántica ni sandbox real de aplicación de patches.


## Actualización FUNC-SPRINT-16 — refactor.plan

### Propósito

Registrar `refactor.plan` como herramienta MIASI implementada para planificación de refactor seguro en modo `plan-only`.

### Funcionamiento

La herramienta analiza targets permitidos, produce candidatos estructurales y genera pasos con pruebas y rollback. No modifica archivos, no genera patches aplicables y no ejecuta comandos de test.

### Integración

- CLI: `python -m devpilot_core refactor-plan --target <ruta> --goal <objetivo> --json`.
- Policy: `PolicyEngine`, `PathGuard`, `SecretGuard`.
- Review: `CodeReviewEngine` como precondición.
- Evidence: `ReportEngine`, `EventLogger`, `LocalStore`.

### Criterios PASS

`dry_run=true`, `plan_only=true`, `files_modified=0`, `patch_generated=false`, pruebas requeridas y rollback incluidos.

### Criterios BLOCK

Target fuera del workspace, ruta denegada, secreto sintético, target inexistente, error de sintaxis o intento de ejecución.

### Riesgos

Tool preliminar. No ejecuta refactors reales; sirve como contrato previo para futuros flujos con aprobación humana, sandbox y rollback.

## Actualización FUNC-SPRINT-17 — ModelAdapter y herramientas de modelo

Sprint 17 marca `model.call.mock` como herramienta implementada y mantiene `model.call.local` como planificada y `model.call.external` como deshabilitada. El objetivo es disponer de un contrato ejecutable multi-modelo sin habilitar red ni costos.

Herramientas relevantes:

| Tool | Estado | Side effect | Riesgo | Control |
|---|---|---|---|---|
| `model.call.mock` | implemented | none | low | `MODEL_LOCAL_ALLOW`, SecretGuard, CostGuard |
| `model.call.local` | planned | local_compute | medium | `MODEL_LOCAL_ALLOW`, futura configuración local |
| `model.call.external` | disabled | network_cost | high | `MODEL_EXTERNAL_DENY`, CostGuard, SecretGuard, aprobación futura |

Criterios PASS: `MockModelAdapter` genera, clasifica y embebe de forma determinística; no requiere API key; no hay red; el proveedor externo queda bloqueado por defecto; ningún secreto crudo se escribe en reportes/trazas.

Criterios BLOCK: prompt con secreto sintético, proveedor no registrado, API externa sin presupuesto/política explícita, configuración con valor de API key crudo, o cualquier intento de contacto real con proveedor local/API dentro de Sprint 17.

Riesgo: esta es una primera versión contractual. Las rutas Ollama/LM Studio/OpenAI/Gemini son placeholders hasta que existan clientes, timeouts, retries, evaluación, budgets persistentes y aprobación humana cuando aplique.

## FUNC-SPRINT-32 — Tool `tests.run`

`tests.run` queda implementada en versión `implemented-initial` como herramienta local approval-gated para ejecutar perfiles pytest controlados. Usa `SafeSubprocessRunner`, command allowlist, timeout, cwd seguro y redacción de stdout/stderr.

Esta capacidad no convierte a DevPilot en CI/CD. Tampoco habilita patch apply, refactor execution, Git write, deploy ni comandos arbitrarios.

Criterios de seguridad:

- approval válido obligatorio;
- scope exacto por perfil;
- no `shell=True`;
- salida redactada;
- evidencia JSON/Markdown opcional;
- eventos locales de ejecución.


## Actualización FUNC-SPRINT-33 — Protección contra tool injection

`ToolInjectionGuard` se agrega como defensa local para detectar prompts que intentan forzar herramientas o saltar el flujo MIASI de aprobación/política. Esta capa no autoriza herramientas por sí misma: solo produce findings que `PolicyEngine` combina con `ApprovalPolicyChecker`, `PathGuard`, `SecretGuard` y `CostGuard`.

Ejemplos de riesgo cubierto:

- forzar `tests.run` sin approval;
- intentar `patch apply`, `git push`, `deploy` o shell fuera de política;
- insertar sintaxis tipo `tool=<id>` en prompts de agente.

Limitación: detección pattern-based, no sandbox ni RBAC.


## Tool Card — GitAdapter v2 read-only — FUNC-SPRINT-35

### Propósito

Ampliar las herramientas Git de solo lectura para alimentar RepoAnalyzer, DependencyGraph, drift y quality gates posteriores.

### Herramientas

- `git.branches`: lista ramas locales/remotas sin checkout.
- `git.tags`: lista tags sin crear ni borrar tags.
- `git.log`: lista commits recientes con límite explícito.
- `git.diff_report`: genera reporte estructurado de cambios staged, unstaged y untracked.

### Restricciones

No se permiten `git add`, `git commit`, `git checkout`, `git reset`, `git push`, creación de tags, merge ni rebase. La implementación usa allowlist y `shell=False`.

### Riesgos

`git.diff_report` es heurístico y no reemplaza SAST/SCA ni revisión humana. No lee contenido completo de diffs ni detecta todas las clases de secretos.
