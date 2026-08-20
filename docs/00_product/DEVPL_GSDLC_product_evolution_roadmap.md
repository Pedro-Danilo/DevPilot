---
doc_id: "DEVPL-GSDLC-PRODUCT-EVOLUTION-ROADMAP"
title: "DevPilot Guided SDLC Product Evolution — Roadmap maestro"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-13"
approval: "approved_by_owner"
approved_by: "Ordóñez"
approved_at: "2026-08-13"
approval_decision: "APPROVE"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
source_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
source_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
pilot_effect_if_approved: "pause-at-POST-H-EVAL-002-02-B-entry"
backlogs_total: 15
---

# DevPilot Guided SDLC Product Evolution — Roadmap maestro v1.1.0

## 0.1 Estado de ejecución reconciliado — 2026-08-20

- `DEVPL-GSDLC-03 = CLOSED/PASS`.
- Successor owner-adjudicated: `repo_DevPilot_Local_364_DEVPL_GSDLC_03_E_PROJECT_ENTRY_BROWSER_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `7f6c9ed8a49fd9300d8b10eb3255969256eb2865`.
- `DEVPL-GSDLC-04 = APPROVED / EXECUTABLE-DESIGN`.
- `GSDLC-04-A = PASS-CANDIDATE / PRE-WINDOWS`: lifecycle/provenance server-authoritative, sin writes de workspace ni nuevas rutas API/UI.
- `GSDLC-04-B` continúa bloqueado hasta evidencia Windows y owner adjudication de 04-A.
- La evidencia browser/full de GSDLC-03 está sellada y no se reejecuta durante 04-A.


## 1. Visión objetivo

> **DevPilot es un entorno local de desarrollo de software guiado que conduce un proyecto desde su creación hasta release, ejecutando MIPSoftware y MIASI como workflows verificables, con autoría humana o agent-assisted, políticas, approvals, pruebas, Git, trazabilidad y evidencia integrados.**

La experiencia de producto objetivo es:

```text
Instalo DevPilot
→ lo abro
→ first-run/login
→ Crear / Abrir / Importar Git
→ defino proyecto, stack, restricciones y modelo IA
→ DevPilot propone plan
→ dry-run
→ approval RBAC
→ workspace + Git + .venv + dependencias
→ Project Status
→ MIPSoftware/MIASI paso a paso
→ Manual / Import / Agent / RAG
→ validate → remediate → approve → freeze
→ roadmap → backlog → sprints
→ story → code → diff → approve → apply
→ tests → quality → remediate
→ governed commit
→ siguiente story
→ release readiness → package/install/rollback/tag
→ RELEASED
```

## 2. Decisión de programa

La aprobación del roadmap **no cancela** POST-H-EVAL-002. Autoriza a GSDLC-00 a:

- pausar administrativamente el piloto en la entrada de 02-B;
- preservar 01-A→01-D y 02-A;
- preservar repo341 como parent histórico;
- reconciliar fuentes canónicas de DevPilot;
- iniciar la macro-evolución;
- reanudar el piloto en GSDLC-13.

Hasta que GSDLC-00 se implemente, repo341 y el estado actual del piloto siguen siendo las fuentes de verdad vigentes.

## 3. Hallazgo que justifica la evolución

DevPilot ya posee gran parte de las primitivas industriales: ApplicationService, PolicyEngine, schemas/validators, readiness, MIASI, approvals/RBAC inicial, workspace isolation, Git governado, Jobs, Test Impact, Quality, evidence/traces, RAG, memory, agents, ModelAdapter/CostGuard y release machinery.

La brecha es de **orquestación de producto + engineering state + UX**.

El programa debe impedir que DevPilot termine como:

```text
proyecto creado externamente
→ artefactos inyectados
→ DevPilot los inspecciona
```

y demostrar:

```text
usuario dentro de DevPilot
→ DevPilot guía y gobierna la construcción
→ artifacts/code/tests/Git/release nacen del workflow de producto
```

## 4. Principios no negociables

1. **UI-complete normal journey.** El camino normal de usuario debe ser realizable desde UI; CLI/API permanecen para automation/diagnostics.
2. **Operator-free project authorship.** Los harnesses externos no pueden escribir contenido del proyecto durante acceptance.
3. **Project-centric UX.** La navegación primaria se organiza alrededor de proyecto/fase/paso; Reports/Traces/Approvals/Jobs/Quality son vistas transversales.
4. **Persistent Project Status.** Siempre se puede conocer fase, paso, indicadores, blockers y próxima acción.
5. **Authenticated local operators.** Login/sesión/RBAC real para actions y approvals; enterprise IAM/tenancy siguen fuera de alcance.
6. **Role-bound approvals.** El actor proviene de la sesión y solo roles autorizados deciden.
7. **Executable MIPSoftware/MIASI.** Standards → registry/gates/next actions determinísticos.
8. **StepActionAdvisor.** Cada paso ofrece Manual/Paste/Upload/External Editor/Agent/RAG/Typed Operation según policy y disponibilidad.
9. **No arbitrary shell.** Toda mutación es typed operation.
10. **LLM assists, never governs.** PASS/BLOCK, transitions, permissions y approvals son determinísticos.
11. **Local-first/multi-model.** Mock/local obligatorios; API externa opcional y cost-aware.
12. **Evidence by transition.** No reconstruir evidencia manualmente al final.
13. **Source state ≠ engineering state ≠ runtime state.**
14. **External edit reconciliation.** IDE/Git externos fuerzan revalidación cuando corresponde.
15. **Historical contracts are scoped.** Ningún test histórico puede congelar indefinidamente un estado futuro.
16. **Progressive bridge retirement.** Un CLI bridge solo se depreca cuando existe reemplazo UI-native probado.

## 5. Arquitectura objetivo

```text
Authenticated User / Role
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│                         DevPilot UI                          │
│ Home · Project Status · Engineering · Planning · Stories    │
│ Quality · Git · Release · Reports · Traces · Approvals      │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
                    GuidedSDLCService
                     / WorkflowEngine
                               │
        ┌──────────────────────┼─────────────────────┐
        ▼                      ▼                     ▼
WorkspaceEngineeringState  Executable Standards  StepActionAdvisor
        │                 MIPSoftware + MIASI        │
        └──────────────────────┼─────────────────────┘
                               ▼
                       ApplicationService
          ┌──────────┬─────────┼─────────┬──────────┐
          ▼          ▼         ▼         ▼          ▼
       Artifacts     Git      Jobs     Quality     Agents
          │          │         │         │          │
          └──────────┴─────────┼─────────┴──────────┘
                               ▼
                    Evidence / Traces / Audit
                               │
                               ▼
                       Model Gateway v2
                 mock · local · API/broker
```

## 6. Modelo de estado

### 6.1 Tres fuentes separadas

**Platform State:** baseline/madurez de DevPilot.

**Workspace Engineering State:** fase, paso, artifacts, planning, sprint, story, gates, progress.

**Runtime Operational State:** sessions, jobs, approvals, locks, agent runs y retries.

### 6.2 Fases macro

```text
NEW
→ BOOTSTRAP_PLANNED
→ BOOTSTRAPPED
→ PRE_CODE
→ PRE_CODE_READY
→ PLANNING
→ IMPLEMENTING
→ VERIFYING
→ RELEASE_READY
→ RELEASED
→ OPERATING
```

### 6.3 Project Status mínimo

```text
Project
Current phase
Current step
MIPSoftware %
MIASI status
Artifacts ready/pending
Blockers
Pending approvals
Quality signal
Git branch / dirty
Model/token budget
Next action
Available execution modes
```

## 7. Identidad y roles

GSDLC-02 introduce autenticación de **operadores locales**, sin declarar enterprise multiuser.

Roles iniciales:

| Rol | Responsabilidad principal |
|---|---|
| owner | gobierno general y decisiones máximas locales |
| product-owner | producto, roadmap, backlog y sprint |
| architect | arquitectura/ADRs |
| security-reviewer | security gates y approvals de seguridad |
| developer | source changes y ejecución técnica permitida |
| qa-reviewer | testing/quality reviews |
| release-manager | release approvals/tags |
| operator | operación/diagnóstico local |
| agent-supervisor | approvals y supervisión de acciones agentic de alto riesgo |

Las matrices exactas de permisos se implementan y prueban en GSDLC-02.

## 8. Autoría y herramientas por paso

Todo artefacto/step gobernado puede exponer, cuando sea aplicable:

```text
MANUAL
PASTE
UPLOAD_IMPORT
EXTERNAL_EDITOR
AGENT
RAG
TYPED_OPERATION
```

`ExecutionModeAdvisor` decide disponibilidad usando state + role + policy + provider + budget y explica disabled reasons.

## 9. Oleadas y dependencias

| Orden | Backlog | Resultado |
|---:|---|---|
| 0 | GSDLC-00 | Activación, pausa del piloto, rebaseline y contratos |
| paralelo | GSDLC-R01 | Investigación multi-modelo y access strategy |
| 1 | GSDLC-01 | Guided State Engine + Project Status |
| 2 | GSDLC-02 | Local Identity/Login/Sessions/RBAC/Approval Authority |
| 3 | GSDLC-03 | Home + Crear/Abrir/Importar Git + bootstrap |
| 4 | GSDLC-04 | Artifact Workbench manual/import |
| 5 | GSDLC-05 | MIPSoftware/MIASI ejecutables + StepActionAdvisor |
| 6 | GSDLC-06 | Model Gateway v2 + token/cost |
| 7 | GSDLC-07 | Agent/RAG contextual |
| 8 | GSDLC-08 | Roadmap/Backlog/Sprints |
| 9 | GSDLC-09 | Story/Coding Workbench |
| 10 | GSDLC-10 | Tests/Quality/Git/Evidence |
| 11 | GSDLC-11 | Release/Lifecycle |
| 12 | GSDLC-12 | UX/resume/reconcile/security/full hardening |
| 13 | GSDLC-13 | Pilot rebind y 02-B real |

R01 puede correr en paralelo después de GSDLC-00-A; solo bloquea GSDLC-06.

## 10. Milestones de valor

### M0 — Program baseline
GSDLC-00 CLOSED/PASS.

### M1 — Authenticated project wizard
GSDLC-03 CLOSED/PASS.

Usuario: login → Create/Open/Import → bootstrap → Project Status, sin PowerShell.

### M2 — Guided pre-code manual/import
GSDLC-05 CLOSED/PASS.

Usuario llega a PRE_CODE_READY mediante MIPSoftware/MIASI y Artifact Workbench, sin IA obligatoria.

### M3 — Guided pre-code agent-assisted
GSDLC-07 CLOSED/PASS.

Mismo flujo con agentes/RAG/costos controlados.

### M4 — Guided planning
GSDLC-08 CLOSED/PASS.

Requirements → roadmap → backlog → sprints.

### M5 — Guided implementation
GSDLC-10 CLOSED/PASS.

Story → code → tests → quality → commit.

### M6 — Guided release
GSDLC-12 CLOSED/PASS.

Proyecto completo, resumible, reconciliable, seguro y release-ready.

### M7 — Pilot proven
GSDLC-13 CLOSED/PASS.

`inventory-sales-local` completa 02-B sin operador externo escribiendo los artefactos.

## 11. Contrato de UX normal

En el alcance ya cerrado de cada milestone:

```text
PowerShell required by normal user = 0
External operator project writes = 0
Required unclassified CLI bridge = 0
```

Una CLI equivalente puede seguir disponible para expert automation, CI o diagnóstico.

## 12. Política de contratos históricos

Cada micro-sprint debe clasificar contratos impactados:

- `historical-freeze`;
- `current-active`;
- `successor-needed`;
- `deprecated-after-proof`.

Casos críticos conocidos:

- assertions de repo/current baseline;
- UOC route counts;
- UOC historical `write_enabled=false`;
- platform `filesystem_write_allowed=false`;
- external API disabled-by-default;
- POST-H-034-D multiuser/auth boundary;
- Git no-go force-push/reset-hard/rebase;
- pilot 01/02-A evidence.

El programa debe crear successors explícitos, no editar la historia para hacer pasar tests.

## 13. Estrategia de pruebas

- micro A→D: Test Impact + focal + validators;
- micro E: browser acceptance cuando hay UX;
- negative security cases desde la misma ola que introduce capability;
- full regression únicamente por escalation o GSDLC-12-E;
- pilot acceptance independiente en GSDLC-13.

## 14. Seguridad macro

No-go persistentes salvo backlog/ADR futuro explícito:

- arbitrary shell;
- force push;
- reset-hard/rebase automáticos;
- public/non-local API;
- enterprise IAM/tenancy/SSO;
- connector write genérico;
- plugin arbitrary execution;
- remote execution;
- cloud deploy;
- secrets in source/evidence;
- browser scraping/cookie piggyback de apps LLM;
- agent self-approval;
- unbounded loops/cost.

## 15. Métricas

- `% normal journey UI-complete`;
- `required CLI bridges per stage`;
- artifact source mix manual/import/agent;
- first-pass validation rate;
- revalidation events;
- approval latency by role;
- resume success;
- requirement→planning→story→test→commit coverage;
- agent accept/reject/modify rate;
- tokens/cost per artifact/story;
- local fallback success;
- S0/S1;
- browser accessibility/performance.

## 16. Definition of Done del programa

DEVPL-GSDLC solo puede cerrar si:

1. existe login local, sesión y RBAC server-side;
2. approvals están vinculados a actor/role autenticado;
3. Home ofrece Create/Open/Import;
4. Create puede materializar folder/Git/.venv/deps desde UI;
5. Project Status siempre explica fase/paso/blockers/next action;
6. StepActionAdvisor ofrece modos aplicables por paso;
7. pre-code MIPSoftware/MIASI puede completarse manual/import desde UI;
8. agente/RAG puede asistir sin gobernar gates ni approvals;
9. roadmap/backlog/sprints se construyen desde UI;
10. story puede llegar a code/tests/quality/commit desde UI;
11. release local se prepara desde UI;
12. restart/external Git edits se reconcilian;
13. normal journey no necesita PowerShell ni operador que escriba source;
14. full regression y browser matrix PASS;
15. `inventory-sales-local` completa 02-B bajo ese flujo;
16. S0=0 y S1=0.

## 17. Decisión del owner requerida

La aprobación de v1.1.0 autoriza **solo el programa y sus backlogs**. No autoriza aplicar source changes todavía.

La implementación comienza con un prompt operativo separado de GSDLC-00.


## 18. Estado de ejecución después de GSDLC-00

`DEVPL-GSDLC-00 = CLOSED/PASS` una vez sellado por 00-E con baseline autoritativo.

- baseline successor: `repo_DevPilot_Local_342_DEVPL_GSDLC_00_PROGRAM_ACTIVATION_REBASELINE.zip`;
- repo341 permanece parent histórico inmutable;
- `DEVPL-GSDLC-01` queda autorizado;
- `DEVPL-GSDLC-R01` puede continuar según su secuencia;
- `POST-H-EVAL-002-02-B` permanece pausado;
- ninguna capability Guided SDLC runtime fue implementada por GSDLC-00.


## DEVPL-GSDLC-03-D — Approval-bound bootstrap execution

Estado de implementación: **PASS-CANDIDATE / PRE-WINDOWS**. Introduce ejecución transaccional tipada exclusivamente sobre un workspace externo autorizado y después de revalidar plan/preimage, human-session/RBAC, approval binding y policy. CREATE/OPEN/IMPORT local son soportados; remote Git y network dependencies permanecen disabled-by-default. Fault injection + rollback son parte de la aceptación. La full regression sigue reservada a 03-E.


### GSDLC-03-E Windows composite closure — CLOSED/PASS

Project Entry completed authoritative browser acceptance: 14 scenarios / 12 screenshots PASS, Create/Open/Import complete in the browser, S0/S1=0, normal-user PowerShell=0 and external operator project writes=0. The backlog full regression ran exactly once and failed historically with `2418 PASS / 67 FAIL / 0 ERROR / 4 SKIP`; no second full was executed. Approved composite recovery then produced REG-001 `56/67 PASS` with 11 residuals, followed by REG-002 `11/11 PASS`, bounded impact `13/13 PASS`, Historical Regression Guard PASS, Documentation Governance PASS and TCR v1/v2 PASS. The original full log remains immutable.

03-E is owner-adjudicated `CLOSED/PASS`; repo364 is its canonical successor. GSDLC-04 is authorized and 04-A is the active cumulative/selective micro-sprint.
