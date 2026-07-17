---
doc_id: "DEVPL-POST-H-EVAL-002-03-BACKLOG"
id: "POST-H-EVAL-002-03"
title: "POST-H-EVAL-002-03 — Release, clean install y assessment industrial"
status: "approved"
version: "1.3.0"
owner: "Ordóñez"
updated: "2026-07-17"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
priority: "P0"
roadmap_wave: "EVAL-002-03"
roadmap_source: "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md"
source_repo: "repo_DevPilot_Local_323_POST_H_EVAL_002_01_D_UI_ACCEPTANCE_FIX.zip"
pilot_baseline_repo: "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
depends_on: "POST-H-EVAL-002-02 closed/pass"
implementation_status: "approved/not-started"
current_micro_sprint: "POST-H-EVAL-002-03-A"
next_micro_sprint: "POST-H-EVAL-002-03-B"
local_first: true
ui_first: true
dry_run_default: true
---

# POST-H-EVAL-002-03 — Release, clean install y assessment industrial

## 1. Estado

`approved/not-started`. Depende del cierre PASS de `POST-H-EVAL-002-02`.

## 2. Propósito

Comprobar reproducibilidad de release y convertir el piloto en un diagnóstico industrial accionable.

## 3. Objetivo

Demostrar reproducibilidad operacional del proyecto piloto y convertir la evidencia acumulada en un diagnóstico industrial y un nuevo roadmap de DevPilot.

## 2. Micro-sprints

### POST-H-EVAL-002-03-A — Documentation and RC readiness

Entregables del proyecto piloto:

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

- reconciliar docs y comportamiento real;
- cerrar findings de documentación;
- verificar evidence freshness de DevPilot;
- verificar cero S0/S1;
- congelar versión del MVP.

PASS:

- docs reproducibles;
- no claims enterprise/SaaS/compliance;
- full regression del proyecto PASS;
- trazabilidad completa;
- RC autorizado.

### POST-H-EVAL-002-03-B — Package, checksums and local release candidate

Entregables:

```text
09_release_candidate/source_zip/
09_release_candidate/checksums.sha256
09_release_candidate/release_manifest.json
09_release_candidate/build_logs/
09_release_candidate/rc_decision.md
```

Validar:

- source ZIP limpio;
- build frontend;
- dependencias declaradas;
- migraciones/base demo controlada;
- checksums;
- backup/rollback dry-run;
- local RC DevPilot como evidencia de plataforma.

No asumir que comandos de packaging de DevPilot empaquetan automáticamente el workspace piloto; documentar alcance real.

### POST-H-EVAL-002-03-C — Clean installation and post-install UI

Instalar en ruta nueva sin reutilizar:

- `.venv`;
- `node_modules`;
- SQLite operativa;
- configuración temporal;
- rutas absolutas anteriores.

Flujo post-instalación:

```text
arrancar backend
→ arrancar frontend
→ crear producto
→ registrar entrada
→ registrar venta
→ verificar stock
→ generar reporte
→ smoke tests
→ reiniciar
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
clean_install=PASS
critical_business_flow=PASS
post_install_restart=PASS
DevPilot_UI_observability=PASS
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

### POST-H-EVAL-002-03-E — Roadmap recommendation and handoff

Entregables:

```text
12_final_assessment/roadmap_recommendation.md
12_final_assessment/next_wave_backlog_candidates.md
12_final_assessment/onboarding_report_v2_update_plan.md
12_final_assessment/POST-H-EVAL-002_closure_report.md
```

Actividades:

1. priorizar gaps por impacto/riesgo/frecuencia/costo;
2. separar defectos, UX gaps y capacidades futuras;
3. decidir nuevas olas;
4. no habilitar capacidades sensibles por inferencia;
5. proyectar Onboarding Report v2 después del assessment;
6. cerrar el hito con PASS, PASS-with-gaps o BLOCK justificado.

## 3. Criterios globales de salida

### PASS

- RC y clean install PASS;
- S0/S1 = 0;
- no-go gates preservados;
- assessment completo;
- roadmap recommendation aprobada.

### PASS-with-gaps

- RC alcanzado;
- solo S2/S3 abiertos;
- workarounds seguros y priorizados;
- ninguna evidencia faltante crítica.

### BLOCK

- corrupción/pérdida de datos;
- secreto expuesto;
- acción sensible no gobernada;
- RC no reproducible;
- clean install falla;
- trazabilidad incompleta crítica;
- assessment no puede sostener sus conclusiones.

## 4. Definition of Done

- A-E cerrados;
- paquete y clean install verificados;
- diagnóstico industrial basado en evidencia;
- nuevo roadmap recomendado;
- plan de Onboarding Report v2 definido;
- `POST-H-EVAL-002` formalmente cerrado.
