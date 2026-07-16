---
doc_id: "DEVPL-POST-H-EVAL-002-01-BACKLOG"
id: "POST-H-EVAL-002-01"
title: "POST-H-EVAL-002-01 — Baseline, arranque y aceptación Web UI"
status: "approved"
version: "1.4.0"
owner: "Ordóñez"
updated: "2026-07-15"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
priority: "P0"
roadmap_wave: "EVAL-002-01"
roadmap_source: "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md"
source_repo: "repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip"
pilot_baseline_repo: "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
depends_on: "POST-H-034 closed/full-regression-pass"
implementation_status: "active/01-a-closed"
current_micro_sprint: "POST-H-EVAL-002-01-C"
next_micro_sprint: "POST-H-EVAL-002-01-D"
local_first: true
ui_first: true
dry_run_default: true
platform_freeze_default: true
---

# POST-H-EVAL-002-01 — Baseline, arranque y aceptación Web UI

## 1. Estado

`active/01-b-closed`. `01-B` quedó cerrado `PASS-WITH-GAPS` con instalación Windows reproducible, validadores PASS y cero S0/S1; `01-C` está autorizado. No se autoriza avanzar a EVAL-002-02 hasta cerrar A-D.

## 2. Propósito

Establecer un baseline reproducible y validar la experiencia Web UI antes de incorporar el proyecto piloto.

## 3. Objetivo

Preparar una ejecución reproducible del piloto, instalar el baseline 318 y validar la Web UI como consola de operador antes de incorporar el proyecto real.

## 2. Alcance

Incluye:

- charter, roles, riesgos y stop conditions;
- estructura de carpetas y evidencia;
- instalación del baseline;
- validadores de cierre y full regression opcional de arranque;
- API local, token temporal y frontend;
- rutas Dashboard, Reports, Traces, Approvals y Settings;
- estados 401/403/API-down/empty/BLOCK/error/timeout;
- métrica inicial UI/CLI.

No incluye creación del MVP ni cambios funcionales a DevPilot.

## 3. Micro-sprints

### POST-H-EVAL-002-01-A — Freeze, charter y evidence control

**Objetivo:** autorizar formalmente `PILOT-E2E-001-RUN-01`.

Entregables:

```text
00_control/PILOT-E2E-001_charter.md
00_control/evidence_manifest.json
00_control/initial_risk_register.md
00_control/stop_conditions.md
00_control/baseline_hashes.txt
00_control/baseline_git_commit.txt
```

Actividades:

1. calcular SHA-256 del ZIP 318 y del log de validación que acompaña al baseline;
2. registrar el commit fuente real obtenido con `git rev-parse HEAD`; no usar un hash histórico hardcodeado;
3. asignar roles;
4. declarar no-go gates;
5. aprobar política de red/provisión;
6. crear estructura de evidencia;
7. congelar plataforma.

Criterios PASS:

- hashes coinciden;
- `baseline_git_commit.txt` contiene el commit real del baseline 318 o declara explícitamente que el ZIP provino de `git archive`;
- charter aprobado;
- stop conditions explícitas;
- S0/S1 iniciales = 0;
- ninguna API key o secreto en evidencia.

Criterios BLOCK:

- baseline no identificable;
- hash distinto;
- ausencia de owner/operador;
- no-go gates ambiguos.

#### Evidencia y decisión de cierre de 01-A

- RUN: `PILOT-E2E-001-RUN-01`;
- paquete externo: `PILOT-E2E-001-RUN-01_POST-H-EVAL-002-01-A_evidence.zip`;
- SHA-256 del paquete: `f6385f047db79f0b02ae01d7c73b1d2d784f1a1acfc6361863e79917935618dc`;
- baseline ejecutable congelado: `repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip`;
- SHA-256 exacto del baseline: `bf5c10df92a104a9c212c19db28d518eff0d5e5a671b4b35ec71bfd79c7df308`;
- commit de empaquetado R1: `2c5f209`;
- ancla funcional: `0c7741f`;
- S0/S1 iniciales: `0/0`;
- plataforma instalada: `false`;
- workspace creado: `false`;
- decisión: `PASS`; la integración del patch y la generación del repo 319 son el handoff operativo estándar.

`01-B` queda autorizado después de esa integración; no se ejecuta en este micro-sprint.

### POST-H-EVAL-002-01-B — Instalación limpia y baseline verification

**Objetivo:** instalar DevPilot desde el ZIP 318 en una ruta nueva y vacía.

Entregables:

```text
01_baseline_installation/tool_versions.txt
01_baseline_installation/pip_freeze.txt
01_baseline_installation/platform_file_inventory.csv
01_baseline_installation/closure_contract.log
01_baseline_installation/project_state.json
01_baseline_installation/docs_governance.json
01_baseline_installation/tcr_v1.json
01_baseline_installation/tcr_v2.json
01_baseline_installation/evidence_freshness.json
```

Validaciones mínimas:

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_034_closure_regression_reconciliation.py -q
python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core release-candidate evidence-freshness --json
```

Criterios PASS:

- entorno Python funcional;
- frontend instalable;
- closure contract PASS;
- Project State/docs/TCR/freshness PASS;
- repo de plataforma separado del workspace piloto.

#### Cierre verificado de 01-B

- decisión: `PASS-WITH-GAPS`;
- evidencia final: `DevPilot_E2E_Evaluation_POST-H-EVAL-002-01-B.zip` SHA-256 `83174a229e93bff2590e19896ea0ba9c0848827e0d37e7b5243580888e6f173f`;
- 17/17 comandos PASS, closure contract 6/6 y validadores PASS;
- S0/S1 abiertos: `0/0`;
- gap S3 no bloqueante: exclusión futura de `*.egg-info` en paquetes de evidencia;
- 01-C autorizado; API/UI todavía no se levantaron en 01-B.

### POST-H-EVAL-002-01-C — API/UI startup and security posture

**Objetivo:** levantar API y UI localmente con seguridad básica verificada.

Entregables:

```text
02_ui_api_startup/api_preflight.json
02_ui_api_startup/api_startup.log
02_ui_api_startup/npm_tests.log
02_ui_api_startup/api_contract_drift.json
02_ui_api_startup/api_security_hardening.json
02_ui_api_startup/ui_api_smoke.json
```

Pruebas:

- bind `127.0.0.1`;
- token temporal no persistente;
- CORS sin wildcard;
- no secrets en logs/capturas;
- npm smoke/visual/operator/route enforcement PASS;
- API contract drift PASS.

Criterios BLOCK:

- bind no-local;
- token en URL/Git/evidence;
- control crítico sin auth;
- ruta crítica no carga.

### POST-H-EVAL-002-01-D — Web UI acceptance and bridge baseline

**Objetivo:** evaluar producto visual antes del SDLC real.

Entregables:

```text
03_ui_baseline_acceptance/ui_acceptance_report.md
03_ui_baseline_acceptance/critical_route_matrix.json
03_ui_baseline_acceptance/negative_state_matrix.json
03_ui_baseline_acceptance/initial_cli_bridge_register.md
03_ui_baseline_acceptance/screenshots/
```

Rutas obligatorias:

```text
/            Dashboard
/reports     Reports
/traces      Traces
/approvals   Approval Center
/settings    Settings
```

Estados negativos obligatorios:

- token ausente;
- token inválido;
- API caída;
- reportes vacíos;
- traces vacíos;
- acción prohibida;
- error de reporte controlado;
- operación lenta/timeout.

Criterios PASS:

```text
Critical Route Coverage = 5/5
UI Eligible Coverage = 100%
secret_exposure = 0
unhandled_errors = 0
S0/S1 = 0
```

## 4. Definition of Done

- micro-sprints A-D cerrados;
- baseline y UI aceptados;
- evidencia hashable y completa;
- bridges CLI iniciales registrados;
- no existe patch de plataforma no versionado;
- `POST-H-EVAL-002-02` autorizado.

## 5. Comandos de verificación

Usar los comandos completos del runbook aprobado. Cualquier desviación debe quedar en la bitácora de RUN.
