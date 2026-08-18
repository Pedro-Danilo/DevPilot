---
doc_id: "DEVPL-GSDLC-03"
title: "DEVPL-GSDLC-03 — Project Entry, Creation, Open and Git Import Workbench"
status: "approved"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "approved_by_owner"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "98e4b2f3f033580bfdd5fc027bf5afcd632f8169"
source_repo_sha256: "bb155968cd10c35a320cdcee3af1f9db4cb64ebed4acbca773f24918c3d58995"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
source_authority_rebound: true
predecessor_backlog: "DEVPL-GSDLC-02"
predecessor_closure_authority: "DEVPL_GSDLC_02_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
predecessor_micro_sprint_closure: "DEVPL_GSDLC_02_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-03"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
validation_policy: "cumulative-selective A-D; exactly-one-full-regression in E"
external_workspace_dependency: false
pilot_workspace_access_allowed: false
---

# 0. Aprobación, rebind y autoridad de ejecución

**Decisión owner:** `APPROVED / EXECUTABLE-DESIGN`.

Esta versión `1.2.0` aprueba el diseño `v1.1.0`, lo rebindea al cierre autoritativo de GSDLC-02 e incorpora las lecciones de operación/validación de GSDLC-02-E.

```text
repo
repo_DevPilot_Local_359_DEVPL_GSDLC_02_E_COMPOSITE_WINDOWS_VALIDATED_CANDIDATE.zip

commit
98e4b2f3f033580bfdd5fc027bf5afcd632f8169

SHA-256
bb155968cd10c35a320cdcee3af1f9db4cb64ebed4acbca773f24918c3d58995

canonical branch
eval/post-h-eval-002-02-a-onboarding
```

Autoridades de entrada obligatorias:

- `DEVPL_GSDLC_02_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md`;
- `DEVPL_GSDLC_02_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`;
- repo359 anterior.

La rama canónica debe promoverse `ff-only` al commit anterior antes de mutar source de 03-A. Esta promoción administrativa no repite pruebas.

## 0.1. Refinamientos aprobados v1.2.0

1. `inventory-sales-local` permanece fuera de la ejecución de GSDLC-03. No se lee, escribe ni usa como fixture.
2. Los fixtures CREATE/OPEN/IMPORT viven bajo rutas controladas de `D:\Projects\DevPilot_E2E_Evaluation`, no en el piloto real.
3. Operadores externos son harnesses de auditoría; el **journey normal del usuario debe completar Create/Open/Import desde UI sin PowerShell**.
4. Operadores Python deben ser state-aware, idempotentes, con subprocess nativo `argv` + `shell=False`, checkpoints incrementales y evidencia estructurada.
5. Git closure distingue gross touched surface de net diff; no asume que todo path tocado debe terminar staged.
6. Identidad de baseline tracked Git-clean usa blob Git cuando CRLF/LF pueda diferir físicamente.
7. A→D no ejecutan full regression por rutina. E ejecuta la única full del backlog exactamente una vez.
8. Si la full de E falla: log/marker inmutables, root-cause corrective + residual exacto + impacted acotado, sin segunda full.
9. Remote Git clone y dependency network son disabled-by-default; cualquier red real requiere plan explícito, policy y approval.
10. No free-form shell ni texto del usuario interpolado como comando.

# DEVPL-GSDLC-03 — Project Entry, Creation, Open and Git Import Workbench

## 1. Objetivo

Implementar la pantalla posterior al login con `Crear nuevo proyecto`, `Abrir proyecto existente` e `Importar repositorio Git`, más bootstrap guiado de carpeta/Git/.venv/dependencias.

## 2. Invariante de producto

> Un usuario autenticado puede iniciar o incorporar un proyecto real sin PowerShell: define parámetros, revisa un plan exacto, aprueba y DevPilot materializa o registra el workspace mediante operaciones tipadas, verificables y recuperables.

## 3. Dependencias y precondiciones

- DEVPL-GSDLC-02 `CLOSED/PASS`.
- Authenticated Project Shell operativo.
- RBAC y approval actor binding de GSDLC-02 vigentes.
- Baseline repo359 y cierre authorities disponibles.
- Canonical branch promovida `ff-only` al commit `98e4b2f3f033580bfdd5fc027bf5afcd632f8169` antes de source mutation.

Si una precondición no es reproducible, `BLOCK` antes de mutar.

## 4. Alcance

### 4.1 Incluido

- post-login Home;
- project intake wizard;
- environment discovery;
- CREATE_NEW;
- OPEN_EXISTING;
- IMPORT_GIT local;
- remote clone plan-only/approval-bound y disabled-by-default;
- Git init;
- `.venv`;
- dependency plan/install typed jobs;
- workspace registration/isolation;
- rollback de bootstrap parcial;
- browser acceptance create/open/import.

### 4.2 Fuera de alcance

- arbitrary shell;
- silent network install;
- cloud deploy;
- Git force push/reset-hard/rebase automático;
- uso del piloto `inventory-sales-local` como fixture;
- credential scraping o persistencia de Git secrets.

## 5. Superficies probablemente afectadas

- `src/devpilot_core/workspace/`;
- onboarding/bootstrap;
- typed Git operations;
- PathGuard/PolicyEngine/RBAC/Approval;
- governed jobs;
- ApplicationService/API;
- UI Home/ProjectWizard;
- schemas/catalogs;
- Source Registry/TCR;
- runbooks y evidence contracts.

La lista es orientativa. Cada micro-sprint debe congelar `SOURCE_DELTA_MANIFEST` before/after y ejecutar Test Impact.

## 6. Micro-sprints secuenciales

### GSDLC-03-A — Project Intake and technology catalog contracts

**Objetivo.** Definir parámetros, schemas y combinaciones soportadas sin habilitar escritura.

**Actividades**
1. Schema para nombre, root, mode, frontend, backend, DB, standards, provider mode y restricciones.
2. `TechnologyCatalog` versionado con requisitos Python/Node/Git, plantillas y operaciones tipadas.
3. Modos `CREATE_NEW`, `OPEN_EXISTING`, `IMPORT_GIT`.
4. Path collisions, allowed roots, nombres inválidos, symlink/path traversal y overlap con DevPilot.
5. Metadata previa de network/cost/approval.
6. Fixture declarativo React+TS/FastAPI/SQLite capaz de expresar el caso del piloto, sin acceder al piloto real.

**Entregables**
- ProjectIntake schema;
- TechnologyCatalog;
- ProjectCreationPlan schema;
- fixtures;
- historical_contract_sweep.

**PASS**
- caso inventory-sales-local expresable declarativamente;
- unknown/ambiguous stack BLOCK;
- no free-form command;
- `S0=0/S1=0`.

**Salida:** autoriza 03-B tras owner adjudication.

### GSDLC-03-B — Environment discovery and bootstrap planning

**Objetivo.** Descubrir prerequisitos y construir plan exacto sin writes.

**Actividades**
1. Detectar Python/Node/npm/Git mediante operaciones read-only tipadas y bounded.
2. Espacio, permisos, collisions y Git state cuando aplique.
3. Plan exacto de folders/files/Git/venv/dependencies/jobs.
4. Cada paso declara `writes`, `network`, `approval`, `rollback`.
5. Missing tools generan alternativas/diagnóstico; nunca instaladores arbitrarios.

**PASS**
- discovery `writes=0`;
- stable plan hash;
- side effects completos;
- no secret env dump;
- `S0=0/S1=0`.

**Salida:** autoriza 03-C.

### GSDLC-03-C — Dry-run for Create/Open/Import

**Objetivo.** Hacer revisables desde UI los tres entry modes antes de execute.

**Actividades**
1. CREATE_NEW dry-run con tree/Git/venv/deps/config.
2. OPEN_EXISTING dry-run con repo/workspace/standards/conflicts.
3. IMPORT_GIT local dry-run; remoto solo como network/credential plan disabled-by-default.
4. Plan hash inmutable y preimage revalidation.
5. Approval request se deriva del plan typed.

**PASS**
- writes=0;
- network runtime=0;
- UI permite revisar los tres;
- plan hash reproducible;
- approval preview deriva del plan;
- `S0=0/S1=0`.

**Salida:** autoriza 03-D.

### GSDLC-03-D — Approval-bound bootstrap execution

**Objetivo.** Ejecutar un plan aprobado de forma transaccional, observable y recuperable.

**Actividades**
1. Materializar solo dentro de fixture/workspace autorizado.
2. Git init/import local por typed operation.
3. `.venv` y dependency jobs declarados.
4. `.gitignore`, metadata DevPilot y standards mínimos.
5. Workspace register/isolation.
6. Fault injection por stage y rollback verificable.
7. Network para dependencies/remote clone permanece explicit-plan + approval; acceptance primaria debe poder correr offline/cache/local fixture.

**PASS**
- usable workspace;
- Git clean;
- venv/deps según plan;
- writes fuera de workspace = 0;
- rollback no deja residue;
- `S0=0/S1=0`.

**Salida:** autoriza 03-E.

### GSDLC-03-E — Post-login Home, entry options and browser acceptance

**Objetivo.** Cerrar el milestone visible `[Crear] [Abrir] [Importar Git]` y el backlog.

**Actividades**
1. Home post-login con tres opciones.
2. Formularios guiados con progressive disclosure y plan summary.
3. Progress/retry/recovery de jobs.
4. Success navega a Project Status.
5. Browser acceptance real CREATE/OPEN/IMPORT con roles permitidos/denegados.
6. Verificar que normal journey requiere `PowerShell=0` y `external operator project writes=0`.
7. Ejecutar **la única full regression del backlog exactamente una vez**, después de gates baratos + browser.

**PASS**
- 3 opciones visibles;
- Create E2E PASS;
- Open E2E PASS;
- Import local E2E PASS;
- role gating PASS;
- normal user PowerShell=0;
- S0=0/S1=0;
- full/composite evidence válida.

**Salida:** `CLOSED/PASS`, autoriza GSDLC-04.

## 7. Alcance transversal

- Es la primera demostración visible del wizard.
- Operators son auditoría, no parte del normal journey.
- Acceptance no puede escribir el piloto real.
- External workspace fixtures se consideran datos efímeros de prueba y deben quedar identificados por run.

## 8. Contratos históricos

Antes del cierre de cada micro-sprint:

- `historical-freeze`;
- `current-active`;
- `successor-needed`;
- `deprecated-after-proof`.

Preservar especialmente:
- POST-H-024 onboarding;
- POST-H-EVAL-002 02-A;
- UOC route history;
- GSDLC-01 Project Status;
- GSDLC-02 auth routes/session authority;
- legacy Git no-go;
- historical `filesystem_write_allowed=false` como hecho de capacidades anteriores, creando successors scoped para Project Bootstrap.

No editar snapshots históricos para obtener verde.

## 9. Seguridad

Toda mutación:

```text
plan → dry-run → policy/RBAC → approval → execute → verify → evidence
```

Obligatorio:
- PathGuard + symlink/path canonicalization;
- deny-by-default;
- typed operations;
- no shell text del usuario;
- no credential values en plan/log/UI/evidence;
- no network silenciosa;
- clone remoto disabled-by-default;
- dependency supply-chain metadata;
- bounded jobs/timeouts;
- rollback;
- no `reset --hard`, `clean`, rebase automático ni force push;
- no acceso al piloto real.

## 10. Estrategia de pruebas

Autoridad: `.devpilot/gsdlc/transversal_validation_policy.json`.

### A→D
- L0 integrity/authority;
- focal;
- cumulative backlog;
- Test Impact analyze/dry-run;
- deterministic validators impactados;
- capability acceptance correspondiente;
- **full regression = NO por rutina**.

Un hard trigger solo puede ejecutar una full intermedia si existe decisión owner-approved previa, y esa ejecución cuenta como la única corrida permitida de acuerdo con la política aplicable.

### E
Orden:
1. focal/cumulative;
2. schemas/API/UI;
3. Node/build;
4. governance/TCR;
5. Test Impact;
6. browser real create/open/import;
7. historical sweep;
8. **full regression exactamente una vez**;
9. package/review.

Si la full falla:
- preservar marker/log;
- no repetir;
- root-cause;
- exact failed-nodeid retest;
- bounded impacted retest;
- Historical Regression Guard;
- `validation_mode=composite-full-regression-selective-retest`.

## 11. Evidencia autoritativa

Cada micro-sprint:
- source delta manifest;
- Git pre/post;
- PASS/BLOCK machine-readable;
- S0/S1;
- network/external-api/secrets/mutations declaration;
- historical sweep;
- Test Impact;
- hashes.

Además:
- A: project_intake_contract_report;
- B: environment_discovery + bootstrap_plan;
- C: create/open/import dry-runs + plan hashes;
- D: execute/job/rollback/workspace manifests;
- E: browser screenshots/traces/parity + full/composite evidence.

## 12. Definition of Done

- Create/Open/Import UI;
- bootstrap Git/.venv/deps;
- rollback;
- UI-complete normal path;
- PowerShell requerido por usuario normal = 0;
- external operator project writes = 0;
- S0=0/S1=0.

## 13. Criterio de autorización de GSDLC-04

Solo `CLOSED/PASS` de 03-E/backlog, o `PASS-WITH-GAPS` con gaps exclusivamente S2/S3, owner, evidencia y sin invalidar la invariante.

## 14. Reglas de operadores Windows

Los prompts A→E deben exigir:

- Python state-aware;
- dry-run default;
- no acciones destructivas;
- native subprocess `argv`, `shell=False`;
- no parsing frágil de PowerShell para Git status;
- `git status --porcelain=v1 -z`;
- EOL-aware baseline con Git blob authority para tracked clean;
- checkpoint JSON después de cada check;
- BLOCK rojo y log suficiente;
- operadores reanudables desde el último checkpoint válido;
- stage/commit según **net diff**, no número bruto de paths tocados;
- PowerShell de guía en una sola línea física por bloque;
- no expansión a nuevas raíces fuera de las aprobadas.
