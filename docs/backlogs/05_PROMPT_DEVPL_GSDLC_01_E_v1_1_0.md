---
doc_id: "DEVPL-PROMPT-GSDLC-01-E"
prompt_number: "05"
title: "Prompt operativo — DEVPL-GSDLC-01-E — Project Status shell, browser acceptance and backlog closure"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-01"
micro_sprint: "DEVPL-GSDLC-01-E"
execution_rule: "cierre de backlog; GSDLC-02 bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-rebind"
source_repo: "repo_DevPilot_Local_352_DEVPL_GSDLC_01_D_FILESYSTEM_GIT_RECONCILIATION.zip"
source_git_commit: "7c050d12d9641642aae971f0d32934f5af5a9557"
source_repo_sha256: "d5722222d1b0e9675f3c136df12df0310224450467332e13b9222ea2c4ade4f8"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
source_backlog: "DEVPL-GSDLC-01_guided_sdlc_state_engine_and_project_status_v1_2_0_APPROVED.md"
source_backlog_sha256: "3334968bce3b188f0c867e41a3f3d06d4f4a6e2845e1623b21b0a1c2f889aadd"
local_first: true
dry_run_default: true
external_api_required: false
network_required: false
pilot_workspace_mutation_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-01-E

> **Execution rebind v1.1.0.** La autoridad de entrada es repo352 / commit `7c050d12d9641642aae971f0d32934f5af5a9557` / SHA `d5722222d1b0e9675f3c136df12df0310224450467332e13b9222ea2c4ade4f8`, después de adjudicación externa `DEVPL-GSDLC-01-D = CLOSED/PASS`. Esta versión incorpora la política transversal owner-approved: E es el micro-sprint de cierre y ejecuta la full regression exactamente una vez en Windows, solo después de gates focales/API/UI/browser; si falla, se conserva la corrida y solo se hace selective retest, nunca una segunda full regression.

## 1. Mandato

Implementa **solo** `GSDLC-01-E — Project Status shell and browser acceptance` y ejecuta el cierre industrial acumulado A→E.

Este sprint introduce la experiencia primaria de estado de proyecto, pero **no** implementa auth GSDLC-02 ni acciones mutantes de avance.

## 2. Precondiciones duras

- A, B, C, D `CLOSED/PASS`;
- baseline/commit/SHA exactos de D;
- state engine, transition engine, status/next-action y reconciliation focales PASS;
- worktree clean;
- pilot workspace preservado;
- no-go gates false.

No fusionar E con GSDLC-02.

## 3. Contrato API

Agregar una operación read-only ApplicationService/GuidedSDLC y una ruta API Project Status.

Contrato recomendado y preferido salvo conflicto documentado con registry actual:

```text
operation_id: guided_sdlc.project_status
route_id: api.guided-sdlc.project-status
GET /api/v1/guided-sdlc/status
```

Debe consumir la proyección de C; no duplicar lógica.

La API debe exponer únicamente DTO sanitizado y actor-neutral. Auth productiva no se implementa aquí; se conserva la protección local existente de la API.

## 4. Project Status UI

Agregar una ruta primaria nueva:

```text
route_id: ui.project-status
path: /project/status
component: ProjectStatusView
```

Integrarla en el shell/navegación sin eliminar las nueve rutas UOC históricas/current.

La vista muestra como mínimo:

- workspace/project identity;
- phase;
- current step;
- progress;
- MIPSoftware;
- MIASI;
- artifact readiness;
- blockers;
- pending approvals summary/reference;
- quality signal/reference;
- Git state;
- revalidation status;
- model/token budget como `not_available/not_applicable` hasta GSDLC-06 si corresponde;
- NextAction;
- execution modes disponibles/disabled reasons cuando puedan derivarse honestamente.

### CTA `Continuar`

En GSDLC-01 es **no mutante**.

Debe:

- consumir `NextAction`;
- navegar a una superficie existente o placeholder seguro;
- nunca avanzar state por click;
- nunca llamar filesystem/Git directamente;
- mostrar disabled reason si el destino aún pertenece a una ola futura.

## 5. Estados visuales obligatorios

Implementar y probar:

- loading;
- ready;
- empty/no workspace;
- blocked;
- `REVALIDATION_REQUIRED`;
- stale;
- API error;
- timeout;
- unauthorized/forbidden conforme boundary local actual;
- unknown/incomplete status.

No ocultar BLOCK/ERROR detrás de mensajes genéricos.

## 6. Historical UI contracts

La UI pasa de nueve rutas UOC históricas a una superficie sucesora adicional.

No modificar documentos `ui_operational_console_final_*` para fingir que siempre existió `ui.project-status`.

Si tests históricos congelan conteo/rutas:

- preservar el hecho histórico 9-route en fixture/snapshot de cierre UOC;
- actualizar current-active registry para incluir `ui.project-status`;
- crear successor contract;
- documentar `historical_contract_sweep`.

Nunca borrar coverage UOC.

## 7. Frontend/API tests

Como mínimo:

- API contract route;
- ApplicationService boundary;
- TypeScript API type parity;
- route registry parity;
- ProjectStatusView rendering;
- all visible states;
- no direct filesystem/Git/core import;
- `Continue` navigation;
- revalidation display;
- responsive/a11y;
- XSS/escaping de reason/blocker text;
- no secrets;
- current route count successor logic;
- npm smoke/build.

## 8. Browser acceptance real

No aceptar solo fixtures DOM o unit tests.

La guía Windows debe arrancar API/UI locales, verificar puertos, ejecutar browser real y detener procesos al final.

Debe generar como mínimo estas capturas sanitizadas:

```text
01_project_status_ready_desktop.png
02_project_status_ready_mobile.png
03_project_status_blocked.png
04_project_status_revalidation_required.png
05_project_status_empty_workspace.png
06_project_status_api_error.png
07_project_status_continue_navigation.png
```

Cada screenshot debe tener metadata/manifest con:

- route;
- viewport;
- scenario;
- expected state;
- observed state;
- API fixture/source;
- timestamp;
- console error count;
- secrets/redactions.

Generar además:

- sanitized HAR summary, no tokens;
- state/API/UI parity matrix;
- accessibility result;
- browser console summary;
- screenshot hash manifest.

No almacenar token, cookies ni headers de autorización en HAR/evidence.

### Instrucción para personal no experto

La guía que generes al ejecutar este prompt debe indicar, paso a paso:

1. qué consola abrir;
2. qué comando único ejecutar;
3. cuándo abrir navegador;
4. URL exacta;
5. qué texto/estado debe observar;
6. nombre exacto de cada captura;
7. dónde guardar cada PNG;
8. cómo verificar que no aparezcan secretos;
9. cómo completar cualquier observación manual JSON/MD con valores permitidos;
10. cómo detener API/UI y verificar que los puertos quedaron libres.

No pedir al operador interpretar código.

## 9. Regresión y cierre

Orden obligatorio:

1. schema/API/UI focales;
2. npm test/build;
3. Docs Governance / Project State / TCR;
4. Test Impact;
5. browser acceptance real;
6. historical contract sweep;
7. **full regression exactamente una vez** para cierre de backlog, porque A→E introduce runtime + API + UI + testing/contracts globales;
8. packaging/promotion.

Si esa full regression identifica fallos:

- guardar log original inmutable;
- clasificar cada residual;
- corregir solo causas;
- ejecutar selective retest de fallidos + contratos impactados;
- **no repetir full regression**;
- registrar `validation_mode=composite-full-regression-selective-retest`.

## 10. Cierre de plataforma

Actualizar Project State/Source Registry con snapshots sucesores sin destruir GSDLC-00/R01.

El backlog final debe demostrar:

```text
state engine deterministic
Project Status functional
external drift revalidation functional
S0/S1 = 0
```

Al final:

- commit E;
- push feature;
- ff-only canonical;
- baseline sucesor limpio;
- Windows evidence;
- owner adjudication E;
- backlog closure adjudication GSDLC-01.

Solo después se autoriza GSDLC-02.

Feature:

```text
feat/devpl-gsdlc-01-e-project-status
```

Commit:

```text
feat(gsdlc-01-e): add persistent project status experience
```


## Reglas transversales obligatorias

1. **Fuente de verdad.** La ejecución de E se basa en `repo_DevPilot_Local_352_DEVPL_GSDLC_01_D_FILESYSTEM_GIT_RECONCILIATION.zip` / `7c050d12d9641642aae971f0d32934f5af5a9557` / SHA `d5722222d1b0e9675f3c136df12df0310224450467332e13b9222ea2c4ade4f8`, después de adjudicación `01-D=CLOSED/PASS`. En B→E la autoridad se rebindea obligatoriamente al baseline + commit + owner adjudication `CLOSED/PASS` del micro-sprint predecesor. No se debe asumir un número de repo sucesor: leerlo de la evidencia del predecesor.
2. **Git real.** El ZIP no contiene `.git`; antes de mutar el repo Windows, verificar rama, `HEAD`, ancestor, worktree clean y SHA del baseline externo. No usar el nombre de branch como sustituto de identidad de commit.
3. **Estado histórico.** No exigir `project_state.current_repo == repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip` como precondición. Ese campo contiene historia/sucesión de plataforma y debe evolucionar solo mediante contratos sucesores. No reescribir snapshots GSDLC-00/R01.
4. **Pilot pause.** `D:\Projects\DevPilot_Workspaces\inventory-sales-local` permanece preservado y sin mutaciones atribuibles a GSDLC-01. Los tests que necesiten workspace deben usar `tmp_path` o fixtures sintéticos.
5. **No-go.** Mantener `remote_execution=false`, `connector_write=false`, `plugin_execution=false`, external provider execution disabled, public API disabled, arbitrary shell disabled, force-push disabled y agent self-approval disabled.
6. **Sin IA para autoridad.** Ningún LLM/modelo participa en PASS/BLOCK, transitions, gate decisions, approval authority, path permission o reconciliation authority.
7. **Application boundary.** Ninguna UI puede leer filesystem/Git/core directamente. Toda capacidad expuesta sigue `UI → API → ApplicationService → GuidedSDLCService/domain service`.
8. **Mutaciones.** Toda mutación real sigue `plan → dry-run → deterministic validation/policy → approval cuando aplique → execute → verify → evidence`. No `reset --hard`, `clean`, `checkout -- .`, rebase automático ni force push.
9. **Histórico.** Antes de cerrar el micro-sprint, generar `historical_contract_sweep` con categorías `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`. No relajar tests solo para obtener verde.
10. **Higiene ZIP.** Baselines y paquetes no incluyen `.git/`, `.venv/`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `*.pyc` ni `.devpilot/devpilot.db`.
11. **EOL/hash.** Los manifests por artefacto se definen en dominio `canonical-git-blob`; los ZIP se generan con `git -c core.autocrlf=false -c core.eol=lf archive` y tienen SHA de transporte independiente.
12. **Regresión.** A→D usan Test Impact + focales. No repetir full regression por rutina. E ejecuta la regresión general de cierre **exactamente una vez** después de gates baratos; si aparecen residuales, corregir y hacer selective retest, nunca una segunda full regression.
13. **Documentación.** Registrar todo nuevo source/schema/test en Source Registry y TCR v1/v2 cuando corresponda; mantener Docs Governance y Project State consistentes.
14. **Operadores.** Preferir un único operador Python state-aware/idempotente por micro-sprint; no entregar cadenas frágiles de scripts PowerShell.
15. **Comandos Windows.** La guía final debe usar comandos PowerShell de una sola línea física y lenguaje apto para personal no experto.


## Topología Windows autorizada

No crear nuevas raíces top-level. Usar únicamente:

```text
D:\Projects\DevPilot_E2E_Evaluation
D:\Projects\DevPilot_Workspaces\inventory-sales-local
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
```

Repositorio Git de producto:

```text
D:\Projects\DevPilot_Local
```

Para este backlog, `inventory-sales-local` se verifica como preservado; no se usa como workspace de prueba mutable.


## Entregables que debes producir al ejecutar este prompt

No basta con describir cambios. Debes entregar artefactos ejecutables y verificables:

1. **Paquete de implementación** `.zip` con operador Python, payload/patch, schemas auxiliares y manifest del package.
2. **Delta candidate** `.zip` con exactamente los paths de repo que se crearán/modificarán, sin archivos extra.
3. **Repo candidate PRE-WINDOWS** limpio para inspección del owner, marcado expresamente como **no canónico**.
4. **Guía única `.md`** de implementación, validación, evidencia y recuperación; las instrucciones operativas detalladas no deben duplicarse en el chat.
5. Sidecars `.sha256` de cada ZIP y de la guía.
6. `SOURCE_DELTA_MANIFEST.json`, `ARTIFACT_HASHES.sha256`, `OPERATION_DECLARATION.json`, `CURRENT.json`, closure report y `historical_contract_sweep`.
7. Definición exacta de evidencia Windows esperada y nombres de outputs bajo las tres raíces autorizadas.
8. Sugerencia de commit convencional y feature branch.
9. Si un paso queda bloqueado, preservar evidencia y emitir patch/recovery focal; nunca recomendar borrar evidencia o reiniciar todo sin necesidad.

El operador Windows debe ser `dry-run` por defecto y bloquear si el estado real no coincide con la autoridad esperada.


## 11. PASS / BLOCK

**CLOSED/PASS candidate** si A→E están secuenciales, Project Status coincide 100% con API/state fixtures, browser real pasa, `Continue` no muta, historical UOC permanece preservado, full regression/composite evidence es válida y S0/S1=0.

**BLOCK** si UI contradice API, navegación normal requiere CLI, browser evidence es sintética únicamente, hay console S0/S1, se expone token/secret, se reescribe historia UOC o GSDLC-02 se habilita antes de owner closure.
