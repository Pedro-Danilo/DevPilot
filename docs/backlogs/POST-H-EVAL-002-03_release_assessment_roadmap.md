---
doc_id: "DEVPL-POST-H-EVAL-002-03-BACKLOG"
id: "POST-H-EVAL-002-03"
title: "POST-H-EVAL-002-03 — Release, clean install y assessment industrial"
status: "approved"
version: "1.6.1"
owner: "Ordóñez"
updated: "2026-08-02"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
priority: "P0"
roadmap_wave: "EVAL-002-03"
roadmap_source: "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md"
minimum_source_repo: "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
minimum_source_repo_identity_policy: "resolve-from-external-immutable-baseline-manifest"
minimum_source_repo_manifest_path: "D:\\Projects\\DevPilot_Artifacts\\POST-H-EVAL-002\\baselines\\repo_327\\BASELINE_CURRENT.json"
minimum_source_repo_manifest_schema: "devpilot.post_h_eval_002.operational_baseline.v1"
minimum_source_repo_sha256_embedded: false
source_repo_resolution: "resolve-latest-governed-DevPilot-baseline-from-POST-H-EVAL-002-02-closure-manifest"
pilot_baseline_repo: "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
depends_on: "POST-H-EVAL-002-02 closed/pass"
implementation_status: "approved/not-started"
current_micro_sprint: "POST-H-EVAL-002-03-A"
next_micro_sprint: "POST-H-EVAL-002-03-B"
workspace_id: "inventory-sales-local"
workspace_root: "D:\\Projects\\DevPilot_Workspaces\\inventory-sales-local"
evaluation_root: "D:\\Projects\\DevPilot_E2E_Evaluation"
artifacts_root: "D:\\Projects\\DevPilot_Artifacts\\POST-H-EVAL-002"
temporary_root: "D:\\Projects\\DevPilot_Temp"
local_first: true
ui_first: true
dry_run_default: true
---

# POST-H-EVAL-002-03 — Release, clean install y assessment industrial

## 1. Estado vigente

`approved/not-started`.

Este backlog depende del cierre `PASS` o `PASS-WITH-GAPS` no bloqueante de `POST-H-EVAL-002-02`. Repo 327 es el baseline mínimo lógico de plataforma. Su identidad física mínima se resuelve desde:

```text
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\repo_327\BASELINE_CURRENT.json
```

03-A debe resolver y verificar el baseline DevPilot efectivo más reciente declarado por el manifest de cierre de 02-E cuando durante la ola 02 se haya producido un patch de plataforma. El SHA-256 no se incrusta en este backlog porque el documento puede formar parte del propio `git archive`; la identidad verificable reside en manifests externos inmutables.

Ninguna actividad 03-A–03-E está autorizada antes del cierre formal de 02-E.

## 2. Precedencia documental

1. frontmatter vigente;
2. sección **Estado vigente**;
3. cierre autoritativo de POST-H-EVAL-002-02;
4. Project State, roadmap y runbook vigentes;
5. notas históricas fechadas, solo como evidencia forense.

## 3. Propósito

Comprobar reproducibilidad de release y clean install del proyecto piloto, y convertir la evidencia acumulada en un diagnóstico industrial accionable para DevPilot.

## 4. Objetivo

Demostrar que `inventory-sales-local` puede empaquetarse, instalarse desde cero, operar su flujo crítico y reiniciarse sin depender del entorno de desarrollo. Luego, evaluar DevPilot en una operación representativa y derivar un roadmap trazable.

## 5. Rutas y aislamiento

```text
DevPilot:       D:\Projects\DevPilot_Local
Workspace:      D:\Projects\DevPilot_Workspaces\inventory-sales-local
Evaluación:     D:\Projects\DevPilot_E2E_Evaluation
Artefactos:     D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
Temporal:       D:\Projects\DevPilot_Temp
Clean install:  D:\Projects\DevPilot_E2E_Evaluation\validation\POST-H-EVAL-002-03-C\<run-id>\install_root
```

`C:\Users\Pedro\Downloads` es ingreso temporal, no ubicación de ejecución ni fuente de verdad.

## 6. Política de pruebas y artefactos

- El workspace Git y el release manifest identifican la fuente exacta del RC.
- El baseline mínimo 327 debe verificarse contra `BASELINE_CURRENT.json`; el baseline efectivo de 03-A debe verificarse contra el manifest autoritativo de cierre de 02-E.
- Ningún SHA-256 de un ZIP se considera válido por estar escrito en este backlog: siempre debe recalcularse sobre el artefacto y compararse con su manifest externo.
- La regresión del piloto puede reutilizarse en 03-A únicamente si corresponde al mismo commit y no cambiaron código, tests, dependencias, configuración o migraciones.
- Cualquier cambio que invalide esa evidencia obliga a ejecutar las pruebas afectadas y, cuando corresponda, la regresión completa del piloto.
- No se ejecuta full pytest de DevPilot salvo cambio de plataforma o señal de Test Impact/riesgo residual.
- Se genera un único RC source ZIP autoritativo y un único paquete de evidencia por micro-sprint.
- No se empaquetan `.git`, `.venv`, `node_modules`, caches, SQLite operativa, `.env`, secretos, tokens, HAR bruto ni outputs runtime.
- Los entornos temporales de clean install se eliminan solo después de archivar evidencia suficiente y verificar hashes.

## 7. Micro-sprints

### POST-H-EVAL-002-03-A — Documentation and RC readiness

Entregables del workspace:

```text
README.md
installation_guide.md
operations_runbook.md
troubleshooting.md
CHANGELOG.md
release_notes.md
release_manifest.json
requirements_test_traceability.md
backup_restore_plan.md
```

Actividades:

1. auditar el cierre del backlog 02 y resolver desde su manifest autoritativo el baseline DevPilot vigente, su commit y su SHA-256;
2. reconciliar documentación con el comportamiento as-built;
3. validar comandos, rutas, variables, migraciones y limitaciones;
4. cerrar findings documentales;
5. verificar evidence freshness y `S0/S1 = 0`;
6. ejecutar o reutilizar regresión vigente del piloto bajo criterios explícitos de frescura;
7. fijar versión, commit y contenido candidato a RC;
8. bloquear overclaims enterprise/SaaS/compliance.

PASS:

- documentación reproducible;
- regresión del piloto PASS vigente;
- trazabilidad completa;
- no overclaims;
- versión y commit congelados;
- RC autorizado;
- `POST-H-EVAL-002-03-B` autorizado.

### POST-H-EVAL-002-03-B — Package, checksums and local release candidate

Entregables:

```text
09_release_candidate/source_zip/
09_release_candidate/checksums.sha256
09_release_candidate/release_manifest.json
09_release_candidate/build_logs/
09_release_candidate/secret_and_runtime_scan.json
09_release_candidate/backup_rollback_dry_run.json
09_release_candidate/rc_decision.md
```

Validar:

- source ZIP limpio del proyecto piloto, no de DevPilot;
- frontend y backend reproducibles;
- dependencias y lockfiles declarados;
- migraciones/inicialización SQLite controladas;
- checksums y manifest consistentes;
- backup/rollback dry-run;
- ausencia de secretos, rutas absolutas y runtime state;
- Local RC de DevPilot usado únicamente como evidencia de plataforma.

PASS:

- ZIP limpio e íntegro;
- build reproducible;
- checksums verificables;
- dependencias/migraciones declaradas;
- backup/rollback dry-run PASS;
- `rc_decision` sustentada;
- `POST-H-EVAL-002-03-C` autorizado.

### POST-H-EVAL-002-03-C — Clean installation and post-install UI

La instalación debe ejecutarse en una ruta nueva dentro del área de validación, sin reutilizar:

- `.venv`;
- `node_modules`;
- SQLite operativa;
- configuración temporal;
- rutas absolutas anteriores;
- procesos o puertos de la instalación de desarrollo.

Flujo post-instalación:

```text
verificar artefacto y checksum
→ instalar backend
→ instalar/build frontend
→ inicializar base controlada
→ arrancar backend y frontend
→ crear producto
→ registrar entrada
→ registrar venta
→ verificar stock
→ generar reporte
→ ejecutar smoke tests
→ detener procesos
→ reiniciar
→ repetir verificación crítica
```

Además, verificar desde Web UI DevPilot:

- workspace/status;
- Reports;
- Traces;
- Operator Dashboard;
- no-go gates;
- RC evidence.

PASS:

```text
clean_install = PASS
critical_business_flow = PASS
post_install_restart = PASS
DevPilot_UI_observability = PASS
process_cleanup = PASS
ports_released = PASS
```

### POST-H-EVAL-002-03-D — Industrial baseline assessment

Entregables:

```text
12_final_assessment/post_h_eval_002_baseline_assessment.md
12_final_assessment/pilot_findings_registry.json
12_final_assessment/pilot_metrics.json
12_final_assessment/ui_gap_register.md
12_final_assessment/architecture_hotspots.md
12_final_assessment/risk_register_final.md
12_final_assessment/maturity_scorecard.json
12_final_assessment/prioritized_gap_matrix.md
12_final_assessment/evidence_coverage_map.json
```

Dimensiones:

- instalación;
- UI/Product UX;
- onboarding;
- SDLC;
- agentes/RAG/tools/multiagente;
- testing;
- observabilidad;
- seguridad;
- release;
- documentación;
- operación.

Escala:

```text
0 inexistente
1 diseño/documento
2 implementado aislado
3 integrado con workaround importante
4 integrado y repetible
5 probado en operación representativa
```

Cada puntuación debe incluir evidencia, confianza y limitaciones. La existencia de código no justifica por sí sola una puntuación de integración u operación.

### POST-H-EVAL-002-03-E — Roadmap recommendation and handoff

Entregables:

```text
12_final_assessment/roadmap_recommendation.md
12_final_assessment/next_wave_backlog_candidates.md
12_final_assessment/onboarding_report_v2_update_plan.md
12_final_assessment/POST-H-EVAL-002_closure_report.md
12_final_assessment/final_artifact_manifest.json
```

Actividades:

1. auditar el assessment 03-D;
2. priorizar gaps por impacto, riesgo, frecuencia, costo, dependencia y valor;
3. separar defectos, UX gaps, deuda arquitectónica y capacidades futuras;
4. proyectar olas/backlogs ejecutables;
5. no habilitar capacidades sensibles por inferencia;
6. decidir cierre global `PASS`, `PASS-WITH-GAPS` o `BLOCK`;
7. sincronizar Project State y fuentes canónicas solo después de una decisión válida;
8. fijar baseline final y handoff;
9. no implementar la primera ola recomendada en el mismo micro-sprint.

## 8. Criterios globales de salida

### PASS

- RC y clean install PASS;
- `S0/S1 = 0`;
- no-go gates preservados;
- assessment completo y sustentado;
- roadmap recommendation aprobada;
- cierre de gobernanza y baseline final verificables.

### PASS-WITH-GAPS

- RC alcanzado;
- solo S2/S3 abiertos;
- workarounds seguros, documentados y priorizados;
- ninguna evidencia crítica faltante;
- ninguna capacidad sensible habilitada.

### BLOCK

- corrupción o pérdida de datos;
- secreto expuesto;
- acción sensible no gobernada;
- RC no reproducible;
- clean install fallido;
- trazabilidad crítica incompleta;
- assessment sin evidencia suficiente.

## 9. Definition of Done del backlog 03

- A–E cerrados secuencialmente;
- RC limpio y verificable;
- clean install y reinicio PASS;
- diagnóstico industrial basado en evidencia;
- nuevo roadmap recomendado;
- plan de Onboarding Report v2 definido;
- Project State y fuentes canónicas sincronizados;
- paquete final autoritativo y hashes generados;
- `POST-H-EVAL-002` formalmente cerrado.

## 10. Registro histórico no autoritativo

Las entradas de 2026-07-21, 2026-07-22 y 2026-07-28 describen bloqueos anteriores de 01-D. Fueron superadas por `PILOT-E2E-001-RUN-05B-RERUN-03`, cuyo resultado autoritativo fue `CLOSED/PASS`, y por el posterior cierre de gobernanza repo 327. Se conservan únicamente como historial forense y no condicionan la autorización futura de 03-A, que depende exclusivamente del cierre de 02-E.
