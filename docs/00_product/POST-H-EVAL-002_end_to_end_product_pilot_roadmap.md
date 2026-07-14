---
doc_id: "DEVPL-POST-H-EVAL-002-PILOT-ROADMAP"
id: "POST-H-EVAL-002"
title: "POST-H-EVAL-002 — Roadmap del piloto real end-to-end UI-first"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-13"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
priority: "P0"
source_repo: "repo_DevPilot_Local_315_POST_H_034-CLOSURE.zip"
source_runbook: "docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md"
implementation_status: "approved/planned"
current_wave: "EVAL-002-01"
next_wave: "EVAL-002-02"
local_first: true
ui_first: true
dry_run_default: true
platform_freeze_default: true
no_remote_execution_enabled: true
no_external_apis_required: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-EVAL-002 — Roadmap del piloto real end-to-end UI-first

## 1. Estado
 
`approved/planned`. La ejecución no ha comenzado; el primer micro-sprint autorizado es `POST-H-EVAL-002-01-A`.

## 2. Propósito

Este roadmap convierte el runbook aprobado de `POST-H-EVAL-002` en una secuencia gobernada de ejecución. El objetivo es validar DevPilot como producto integrado mediante un proyecto real, no añadir features por anticipación.

La secuencia prioriza la Web UI como superficie del operador, usa CLI únicamente como bridge documentado y congela la plataforma salvo defectos S0/S1 que impidan continuar.

## 2. Fuente de verdad

| Fuente | Uso |
|---|---|
| `repo_DevPilot_Local_315_POST_H_034-CLOSURE.zip` | Baseline inmutable de la plataforma |
| `Log_consola_no-regresion_POST-H-034-final.txt` | Evidencia 1911/1911 y cierre POST-H-034 |
| Runbook UI-first aprobado | Procedimiento operativo detallado |
| Backlogs EVAL-002-01/02/03 | Unidades ejecutables y gates |

Hashes de referencia:

```text
baseline ZIP: 9824313443e2fe874dd3e89fa3d72a60a4f4bc3e33232c373cb002bee77da5d1
log final:    fc13a5c5e5f938a0eab0e220ecb97d6e6d4fd5c534b6198e4df0a6b1c40fe346
```

## 3. Principios de ejecución

1. **Evaluación antes que evolución:** no convertir hallazgos en features durante la misma corrida.
2. **UI-first medible:** toda operación con superficie UI debe ejecutarse por UI; todo bridge CLI se registra.
3. **Baseline congelado:** una corrección de plataforma abre una nueva RUN y obliga a repetir los checkpoints afectados.
4. **Evidencia reproducible:** cada decisión debe apuntar a logs, reportes, traces, capturas o commits.
5. **Dry-run y approvals:** ninguna operación riesgosa se ejecuta sin plan, revisión y aprobación.
6. **No-go gates intactos:** connector write, plugin execution, remote execution, SaaS y multiusuario productivo siguen bloqueados.
7. **Separación de repos:** plataforma, proyecto piloto y evidencia viven en rutas distintas.
8. **Costo cero por defecto:** mock/local primero; APIs externas quedan fuera del primer piloto.

## 4. Proyecto piloto

```text
PILOT-E2E-001 — Sistema local de ventas e inventario
```

Stack de referencia:

```text
Frontend: React + TypeScript
Backend: FastAPI + Python
Persistencia: SQLite
Operación: localhost
Testing: unit + integration + contract + UI smoke + E2E crítico
```

## 5. Oleadas

### Oleada EVAL-002-01 — Baseline, arranque y aceptación UI

Backlog: `POST-H-EVAL-002-01_baseline_ui_acceptance.md`

Resultado esperado:

- charter aprobado;
- baseline 315 instalado y verificado;
- API/UI locales operativas;
- cinco rutas UI críticas y estados negativos evaluados;
- baseline de bridges CLI y UX gaps registrado.

Gate de salida:

```text
baseline-integrity=PASS
api-ui-startup=PASS
critical-ui-routes=5/5
negative-ui-states=PASS
S0/S1=0
```

### Oleada EVAL-002-02 — SDLC real, implementación y trazabilidad

Backlog: `POST-H-EVAL-002-02_sdlc_execution_traceability.md`

Resultado esperado:

- workspace piloto incorporado;
- pre-code strict PASS;
- MVP implementado por historias pequeñas;
- agentes/RAG/tools/handoffs evaluados con límites;
- requirement→change→test→trace→commit completo;
- full regression del proyecto piloto PASS.

Gate de salida:

```text
workspace-isolation=PASS
readiness-strict=PASS
mvp-stories-accepted=100%
traceability-blockers=0
pilot-regression=PASS
S0/S1=0
```

### Oleada EVAL-002-03 — Release, reinstalación y assessment

Backlog: `POST-H-EVAL-002-03_release_assessment_roadmap.md`

Resultado esperado:

- RC local reproducible;
- source ZIP/checksums/manifest disponibles;
- clean install ejecutada en ruta nueva;
- UI del proyecto y UI DevPilot verificadas después de reinstalar;
- assessment industrial y scorecard de madurez;
- gaps priorizados y recomendación de roadmap posterior.

Gate de salida:

```text
pilot-rc=PASS
clean-install=PASS
post-install-ui=PASS
assessment-complete=true
roadmap-recommendation-produced=true
```

## 6. Dependencias y orden obligatorio

```text
POST-H-034 closed/full-regression-pass
  ↓
POST-H-EVAL-002-01
  ↓
POST-H-EVAL-002-02
  ↓
POST-H-EVAL-002-03
  ↓
Diagnóstico industrial y roadmap de evolución
  ↓
Onboarding Report v2
```

No iniciar EVAL-002-02 si EVAL-002-01 está BLOCK. No iniciar RC si existe un S0/S1 abierto o trazabilidad incompleta.

## 7. Política de RUNs

Cada ejecución completa usa un identificador:

```text
PILOT-E2E-001-RUN-01
```

Si se modifica DevPilot:

```text
PILOT-E2E-001-RUN-02
```

No mezclar evidencia de RUNs diferentes. El manifest debe registrar baseline, commit, hashes, fechas y operador.

## 8. Métricas de programa

| Métrica | Objetivo inicial |
|---|---:|
| Critical Route Coverage | 5/5 |
| UI Eligible Coverage | 100% |
| UI Recovery Success | 100% |
| Secret exposure | 0 |
| S0/S1 abiertos al RC | 0 |
| Requirement traceability | 100% |
| Full regression proyecto | PASS |
| Clean install | PASS |
| Report discoverability | medir, sin maquillar |
| CLI Bridge Ratio | medir y priorizar |

## 9. Decision gates

### Gate G0 — Autorizar piloto

PASS si charter, roles, baseline, riesgos y stop conditions están aprobados.

### Gate G1 — Aceptar plataforma/UI

PASS si instalación, API, UI, seguridad local, rutas y estados negativos funcionan.

### Gate G2 — Autorizar pre-code

PASS si artefactos, MIASI, standards y readiness strict están conformes.

### Gate G3 — Autorizar RC

PASS si MVP, tests, documentación y trazabilidad están completos.

### Gate G4 — Cerrar evaluación

PASS si clean install, assessment y roadmap recommendation están terminados.

## 10. Política de incidentes

| Severidad | Tratamiento |
|---|---|
| S0 | Detener; preservar evidencia; patch obligatorio |
| S1 | Pausar; patch mínimo; nueva RUN o repetición de checkpoint |
| S2 | Continuar con workaround seguro y gap priorizado |
| S3 | Registrar; no interrumpir |

Los patches de plataforma no se incorporan silenciosamente. Deben tener test de regresión, full regression DevPilot y actualización del manifest de RUN.

## 11. Entregables finales

```text
PILOT-E2E-001 evidence manifest
UI acceptance report
CLI bridge and UX gap register
project SDLC traceability matrix
pilot RC package and checksums
clean installation report
industrial baseline assessment
maturity scorecard
prioritized gap matrix
roadmap recommendation
```

## 12. Definition of Done de POST-H-EVAL-002

- tres backlogs cerrados;
- proyecto piloto llega a RC o existe BLOCK técnicamente justificado;
- toda evidencia tiene hash y RUN;
- no-go gates no fueron relajados;
- UI-first fue medido con datos;
- CLI bridges fueron registrados;
- no existen findings S0/S1 sin decisión;
- assessment y roadmap recommendation están aprobados;
- Onboarding Report v2 queda listo como siguiente hito documental.
