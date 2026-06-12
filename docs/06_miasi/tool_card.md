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

Sprint 17 marca `model.call.mock` como herramienta implementada y mantiene `model.call.local` como implementada inicialmente para Ollama y `model.call.external` como deshabilitada. El objetivo es disponer de un contrato ejecutable multi-modelo sin habilitar red ni costos.

Herramientas relevantes:

| Tool | Estado | Side effect | Riesgo | Control |
|---|---|---|---|---|
| `model.call.mock` | implemented | none | low | `MODEL_LOCAL_ALLOW`, SecretGuard, CostGuard |
| `model.call.local` | implemented-initial | local_compute | medium | `MODEL_LOCAL_ALLOW`, futura configuración local |
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

## Tool Card — DependencyGraph read-only — FUNC-SPRINT-36

### Propósito

Agregar una herramienta de análisis estático para construir un import graph Python inicial sin ejecutar código. Sirve como insumo para RepoAnalyzer, architecture drift, review rule packs y quality gates posteriores.

### Herramienta

- `repo.dependency_graph`: analiza imports Python mediante AST y produce nodos, edges, dependencias, dependientes, imports externos, `fan_in` y `fan_out`.

### Restricciones

La herramienta es read-only. No importa módulos analizados, no ejecuta archivos Python, no llama red, no usa modelos ni modifica el workspace. Excluye `outputs/`, `.git/`, `.venv/`, caches y build artifacts.

### Criterios PASS

- Parseo AST local.
- Salida `CommandResult` JSON-serializable.
- Syntax errors como findings controlados.
- Reporte opcional JSON/Markdown.

### Criterios BLOCK

Ejecución/importación de código analizado, traversal fuera del workspace, red/APIs/modelos, o sobredeclarar el grafo como SAST/SCA/call graph completo.

### Riesgos

Imports dinámicos, plugins y relaciones runtime pueden no detectarse. La herramienta produce señales estructurales, no prueba semántica completa de acoplamiento.

## Tool Card — RepoAnalyzer v2 read-only — FUNC-SPRINT-37

### Propósito

Agregar una herramienta de análisis de salud de repositorio que consolida `repo-inventory`, `DependencyGraph` y `GitAdapter` para entregar señales de estructura, dependencias, pruebas, documentación, Git y riesgos básicos.

### Herramienta

- `repo.analyze`: genera resumen heurístico de salud del repositorio con secciones `source/tests/docs/config`, hotspots, riesgos y estado Git parcial o completo.

### Restricciones

La herramienta es read-only. No ejecuta código analizado, no aplica patches, no modifica archivos, no escribe fuera de reportes solicitados, no llama red, no usa modelos y no depende de APIs externas. Excluye `outputs/`, `.git/`, `.venv/`, caches, `build/` y `dist/`.

### Criterios PASS

- Salida `CommandResult` JSON-serializable.
- Reporte opcional JSON/Markdown con `--write-report`.
- Repos sin Git generan análisis parcial, no crash.
- Secretos sintéticos se reportan sin valores crudos.
- Health score documentado como heurístico.

### Criterios BLOCK

Analizar outputs runtime como salud de repo, emitir secretos crudos, ejecutar código analizado, usar red/APIs/modelos, o habilitar patch apply/refactor execution/Git write/deploy.

### Riesgos

El score puede ser malinterpretado como certificación. Las heurísticas de módulos sin test cercano pueden generar falsos positivos. No reemplaza SAST/SCA, análisis de licencias, vulnerabilidades, complejidad industrial ni revisión humana.


## Tool Card — Architecture/code drift read-only — FUNC-SPRINT-38

### Propósito

Agregar una herramienta de análisis de divergencia arquitectura/código que compare documentación C4/arquitectura contra módulos reales del repositorio sin modificar archivos.

### Herramienta

- `repo.architecture_drift`: genera matriz `documented ↔ code`, findings `doc_missing`, `code_missing`, `name_mismatch`, niveles de confianza y reporte opcional JSON/Markdown.

### Restricciones

La herramienta es read-only. No ejecuta código analizado, no modifica documentos, no aplica patches, no escribe fuera de reportes solicitados, no llama red, no usa modelos y no depende de APIs externas. Los componentes `planned`, `future` y `disabled` sin código no deben tratarse como fallos bloqueantes.

### Criterios PASS

- Salida `CommandResult` JSON-serializable.
- Reporte opcional JSON/Markdown con `--write-report`.
- Separación explícita de `doc_missing`, `code_missing` y `name_mismatch`.
- `confidence` y rationale por fila de matriz.
- Sin LLM, red, API externa ni mutaciones.

### Criterios BLOCK

Inventar relaciones no soportadas, modificar documentación automáticamente, ejecutar código analizado, usar red/APIs/modelos, emitir bloqueos por componentes aspiracionales o habilitar patch apply/refactor execution/Git write/deploy.

### Riesgos

El matching por nombres, paths y aliases es heurístico. Puede requerir un futuro Component Registry o Command Catalog para reducir falsos positivos/falsos negativos y madurar hacia un quality gate industrial.


## Tool Card — Repo Quality Gate dry-run — FUNC-SPRINT-39

### Propósito

Agregar una herramienta de gate integral para revisión local de repositorio antes de aceptar cambios. Consolida rule packs, análisis de repositorio, code review, patch review opcional y política de seguridad en una salida auditable.

### Herramienta

- `repo.quality_gate`: ejecuta `repo quality-gate` y produce estado `PASS`, `FAIL`, `BLOCK` o `ERROR` en modo dry-run.

### Restricciones

La herramienta es dry-run. No modifica archivos, no aplica patches, no ejecuta Git write, no despliega, no llama red, no usa APIs externas, no usa modelos y no emite secretos crudos. `PatchReviewEngine` solo corre si se proporciona patch y nunca aplica cambios.

### Criterios PASS

- Salida `CommandResult` JSON-serializable.
- Rule packs versionables y serializables.
- `--write-report` genera evidencia JSON/Markdown.
- Warnings no bloquean por defecto.
- `FAIL` y `BLOCK` de motores integrados se propagan.
- MIASI declara la tool.

### Criterios BLOCK

Ignorar findings `BLOCK`, emitir secretos crudos, aplicar patches, modificar archivos, ejecutar Git write, usar red/APIs/modelos o bloquear por warnings meramente informativos.

### Riesgos

El gate es `implemented-initial`. No reemplaza SAST/SCA, análisis de licencias, coverage real, revisión humana ni CI industrial. Las reglas y severidades deberán madurar con perfiles por repositorio y umbrales configurables.


## Tool Card — Patch preflight seguro — FUNC-SPRINT-40

### Propósito

Agregar una herramienta de preflight para verificar patches antes de cualquier aplicación real. La herramienta responde si el patch tiene riesgos y si `git apply --check` lo considera aplicable en el estado actual del workspace.

### Herramienta

- `patch.check`: ejecuta `patch check --patch-file ...` y produce un `CommandResult` con revisión de patch, apply-check y evidencia de no mutación.

### Restricciones

La herramienta es dry-run. No aplica patches, no modifica archivos del workspace productivo, no ejecuta Git write, no crea sandbox, no ejecuta rollback, no usa red, no usa APIs externas, no usa modelos y no emite secretos crudos. `git apply --check` solo se ejecuta mediante `SafeSubprocessRunner` y allowlist explícita.

### Criterios PASS

- El patch file está dentro del workspace.
- `PatchReviewEngine` no emite `BLOCK`.
- `git apply --check` retorna cero.
- El working tree permanece igual antes y después.
- Reportes opcionales se escriben solo bajo `outputs/reports`.

### Criterios BLOCK

Path fuera del workspace, secreto sintético detectado, policy block, SafeSubprocessRunner bloqueado, uso de subprocess fuera de allowlist o cualquier evidencia de mutación del working tree.

### Riesgos

La versión es `implemented-initial`. No reemplaza sandbox, ChangeSet, rollback, CI, SAST/SCA ni revisión humana. Debe mantenerse separada de cualquier futuro `patch apply`.


## Tool Card — PatchSandbox y ChangeSet

`patch.sandbox` queda declarado como tool MIASI de riesgo alto con side effect `controlled_write`. La tool ejecuta `PatchPreflightEngine`, aplica el patch solo dentro de `outputs/sandbox`, genera un `ChangeSet` con hashes antes/después y mantiene bloqueada cualquier aplicación sobre el workspace productivo.

Criterios PASS: sandbox bajo `outputs/sandbox`, ChangeSet sin contenido crudo, preflight obligatorio, no Git write y reportes auditables.

Criterios BLOCK: mutación productiva, omisión de preflight, secretos crudos en evidencia, pruebas sin aprobación `tests.run`, rollback ejecutable no autorizado o escritura fuera de rutas runtime controladas.

Riesgos: capacidad `implemented-initial`; el rollback ejecutable pertenece a `FUNC-SPRINT-42` y la aplicación real de patches al workspace productivo permanece fuera de alcance.


## Tool Card — RollbackManager y backup local

`rollback.plan`, `rollback.list`, `rollback.show` y `rollback.execute` quedan definidos para `FUNC-SPRINT-42`. `rollback.plan` crea metadata y backups locales controlados desde un `ChangeSet`; `rollback.list/show` son read-only; `rollback.execute` permanece approval-gated y no-mutating en la versión inicial.

Criterios PASS: planes serializables, backups bajo `.devpilot/rollback/`, redacción de evidencia, bloqueo de secretos, list/show read-only.

Criterios BLOCK: ejecución sin aprobación, paths fuera del workspace, backups con secretos detectables, runtime points versionados o restauración automática no autorizada.


## Tool Card — RefactorExecutor controlado en sandbox

Herramienta: `refactor.sandbox`.

Propósito: ejecutar planes de refactor revisables únicamente en `outputs/sandbox`, con approval explícito, `ChangeSet`, rollback plan y pruebas opcionales.

Tool contract: requiere `target`, `plan_id` y `approval_id`. El subject de approval es `refactor:<plan_id>:<target>`. Si se solicitan pruebas se requiere además approval `tests.run` con subject `sandbox:<profile>`.

Side effects: `controlled_write` limitado a `outputs/sandbox` y metadata runtime de `.devpilot/rollback`.

Criterios PASS: approval válido, target workspace-local, plan id conocido, transformación determinística, workspace productivo intacto, ChangeSet y rollback plan generados.

Criterios BLOCK: approval ausente o con scope incorrecto, target fuera de root, plan ambiguo, ausencia de cambios determinísticos, mutación productiva, rollback plan fallido o tests sin approval.

Riesgos: capacidad `implemented-initial`; no realiza refactors semánticos, no aplica al workspace productivo y debe evolucionar hacia operaciones AST/IDE-like con validadores más fuertes.


## Tool Card — RepoEngineeringGate cierre Fase C

### Propósito

`repo.engineering_gate` consolida señales de ingeniería de repositorio para decidir si Fase C puede cerrarse y si el proyecto puede preparar Fase D de IA local gobernada.

### Herramientas

- CLI: `python -m devpilot_core repo engineering-gate --profile full --json --write-report`.
- Core: `src/devpilot_core/repo/engineering_gate.py`.

### Tool contract

Entrada: perfil `quick|full`, target de análisis, code target opcional y patch file opcional para review dry-run.
Salida: `CommandResult` con summary, componentes, capacidades Fase C, findings y reportes opcionales.

### Criterios pass

- No muta workspace productivo.
- No usa Git write, deploy, LLMs ni APIs externas.
- Agrega `GitAdapter`, `DependencyGraph`, `RepoAnalyzer`, `ArchitectureDrift`, `RepoQualityGate` y MIASI.
- En perfil `full`, verifica cierre documental de Fase C.

### Criterios block

- Falta una tool/policy crítica en MIASI.
- Algún componente emite `FAIL`, `BLOCK` o `ERROR`.
- Falta documentación/manifests de cierre.
- Runtime paths no están excluidos.

### Riesgo

Riesgo alto por su rol de gate de cierre, aunque su side effect es solo `report`. Requiere observabilidad y evidencia, pero no approval porque no ejecuta cambios productivos.


## Tool Card — Model providers locales gobernados

`FUNC-SPRINT-45` actualiza el contrato de herramientas de modelo:

- `model.call.mock`: implementado, sin red, sin API key, proveedor default.
- `model.call.local`: implementado inicialmente para Ollama opcional en Sprint 46; LM Studio queda implementado inicialmente en Sprint 47.
- `model.call.external`: disabled y approval-gated; no se llama por defecto.

Toda llamada de modelo debe pasar por `ModelAdapterRouter`, `ProviderRegistry`, `PolicyEngine`, `SecretGuard` y `CostGuard`.

PASS: mock operativo, locales localhost-only/deshabilitados por defecto, externos disabled. BLOCK: raw secrets, endpoint remoto en provider local, API externa habilitada por defecto o agente llamando adapters directamente.


## FUNC-SPRINT-46 — OllamaAdapter local opcional

DevPilot declara `model.health.local` como herramienta implementada inicial para health checks localhost-only y actualiza `model.call.local` a `implemented-initial` para llamadas Ollama controladas. Las llamadas siguen bloqueadas si el provider local está deshabilitado, si el endpoint no es localhost, si SecretGuard detecta secretos o si PolicyEngine/CostGuard bloquean la solicitud.

La implementación es preliminar: cubre Ollama con timeouts y fake-server tests; habilita LM Studio local OpenAI-compatible de forma inicial; no habilita APIs externas, streaming, budget ledger persistente ni AgentRuntime model-aware.


## FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible

DevPilot mantiene `model.health.local` como herramienta implementada inicial para health checks localhost-only y extiende `model.call.local` para cubrir LM Studio local OpenAI-compatible. Las llamadas siguen bloqueadas si el provider local está deshabilitado, si la base URL no es localhost, si SecretGuard detecta secretos o si PolicyEngine/CostGuard bloquean la solicitud.

La implementación es preliminar: cubre `/v1/models`, `/v1/chat/completions` y `/v1/embeddings` con timeouts y fake-server tests; no habilita OpenAI externo, streaming, budget ledger persistente ni AgentRuntime model-aware.


## Tool Card FUNC-SPRINT-48 — Model governance tools

Sprint 48 incorpora herramientas de gobierno de modelos: `model.health.local`, `model.capabilities.read` y `model.budget.status`. Todas operan local-first, no contactan APIs externas, no almacenan prompts ni secretos crudos y quedan gobernadas por `ProviderRegistry`, `ModelAdapterRouter`, `SecretGuard`, `CostGuard`, `LocalStore` y políticas MIASI.

Criterios PASS: reportes JSON reproducibles, proveedores externos bloqueados, budget ledger sin payloads crudos y fallback a `mock` explícito/configurado. Criterios BLOCK: gasto externo por defecto, endpoint remoto, metadata con secretos o provider unavailable con traceback.

## FUNC-SPRINT-49 — Prompt Registry como herramienta agentic gobernada

Sprint 49 registra prompts como herramientas read-only/controlled dentro de MIASI:

- `prompt.registry.read`: lectura del catálogo de prompts versionados.
- `prompt.contract.validate`: validación de schema, placeholders y safety básica.
- `prompt.render.controlled`: renderizado local controlado para llamadas de modelo con `prompt_id/version`.

Estas herramientas no llaman red, no ejecutan acciones críticas, no escriben prompts y no almacenan payloads crudos. Su estado es `implemented-initial` porque el chequeo de inyección de prompt es determinístico y básico.


## FUNC-SPRINT-50 — Model evaluation matrix como herramienta MIASI

Sprint 50 registra `model.eval.run` como herramienta MIASI de tipo report/read-only. Ejecuta `ModelEvalRunner` sobre fixtures locales, usa `PromptRegistry`, `ModelAdapterRouter` y `BudgetLedger`, y produce una matriz redacted de métricas por provider/model/prompt. PASS exige que `mock` no dependa de modelos reales y que providers locales no disponibles queden skipped/controlados. BLOCK si se llama API externa o se persisten prompts/completions crudos.


## FUNC-SPRINT-51 — AgentRuntime v2 model-aware tool

Sprint 51 registra `agent.model.generate` como herramienta MIASI `implemented-initial`. Esta tool representa llamadas de generación hechas desde un agente monoagente por medio de `AgentRuntime v2`, nunca mediante adapters directos.

Gate obligatorio:

```text
AgentRuntimeV2 + PromptRegistry + ModelAdapterRouter + BudgetLedger + SingleAgentOnly + NoHandoffs + NoExternalAPI + NoRawPrompts
```

PASS: llamadas con `mock` trazadas en `model_calls`, `prompt_id/version`, digest y budget events redacted. BLOCK: adapter directo, prompt/completion crudo, provider local obligatorio, API externa o handoff/multiagente.
