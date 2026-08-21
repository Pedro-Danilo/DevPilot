---
doc_id: "DEVPL-GSDLC-04-B-CLOSURE-REPORT"
title: "DEVPL-GSDLC-04-B — Manual editor, draft persistence and version history — pre-Windows closure report"
status: "implemented/ready-for-windows"
version: "1.0.4"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "pending_windows_evidence_and_owner_adjudication"
---

# DEVPL-GSDLC-04-B — Pre-Windows closure report

## 1. Decisión

`IMPLEMENTED / READY-FOR-WINDOWS`. Este reporte **no** declara `CLOSED/PASS`. El cierre formal exige evidencia Windows, browser smoke real y adjudicación posterior del owner.

## 2. Fuente de ejecución

- Repo: `repo_DevPilot_Local_365_DEVPL_GSDLC_04_A_ARTIFACT_LIFECYCLE_WINDOWS_VALIDATED_CANDIDATE.zip`
- Commit adjudicado: `6b6cb70eb16c94f4aa374fc74d9ff2f8f8b6c893`
- SHA-256: `0359182b736d8cbb1f90ad92cf56fd02c7081fc357674597c02c2706fedb67a6`
- 04-A: `CLOSED/PASS`; 04-B autorizado.

## 3. Capacidades implementadas

1. `ArtifactDraftApplicationService` con persistencia runtime separada del artefacto fuente.
2. `SAVE/AUTOSAVE/HISTORY/DISCARD/RECOVER`, revisiones inmutables y recuperación después de restart.
3. Concurrencia optimista server-side mediante hash de source/preimage y hash de revisión vigente.
4. Provenance `MANUAL`, actor/rol/sesión derivados de principal autenticado.
5. Cinco rutas API protegidas por human session + Server RBAC; legacy token no es autoridad.
6. `ArtifactManualEditor` integrado en `ui.workspace-documents`, preview Markdown/JSON seguro, hints JSON, autosave, history, conflict y recovery states.
7. `DocumentEditPlanner` consume el draft gobernado para Markdown/JSON; `sessionStorage` queda solo como compatibilidad histórica YAML/YML.
8. Schema y contratos current-active actualizados; UOC-005 permanece como único boundary para source apply/rollback.

## 4. Validación local pre-Windows

- Test focal 04-B: **11/11 PASS**.
- Acumulativo 04-A + UOC-004 + UOC-005 + 04-B: **48/48 PASS**.
- Impacto RBAC/API/UI: **36/36 PASS**.
- Documentation Source Registry: **5/5 PASS**.
- Smoke estático UI 04-B: **15/15 PASS**.
- TypeScript `noEmit` sobre la superficie tocada: **PASS** usando una declaración ambient local de `ImportMeta.env`; el build Vite completo permanece gate Windows porque `node_modules` no se aprovisionó en este sandbox.
- Schema catalog: **PASS, 207/207**.
- Validation Gateway `docs`: **PASS** (Artifact Profile Registry + strict readiness).
- TCR v1: **PASS, 286 contratos**.
- TCR v2: **PASS, 286 contratos / 96 P0 / 0 missing paths / 0 unsafe commands**.
- Project State: **PASS**.
- Documentation Governance: **PASS, 948/948, drift 0, blocking findings 0**.
- API contract drift: **PASS** con warnings históricos no bloqueantes sobre transportes públicos omitidos del OpenAPI estático.
- API security hardening: **PASS**.
- Operador Python `py_compile`: **PASS**.
- Full regression: **0 ejecuciones** por política A→D.
- `npm ci --offline`: no completado porque el cache de este sandbox no contiene Vite; no se habilitó red. `npm ci` + build quedan como gate Windows.

Los resultados definitivos están materializados en `DEVPL_GSDLC_04_B_TEST_IMPACT.json`, `DEVPL_GSDLC_04_B_CONTRACT_RECONCILIATION_SWEEP.json` y `DEVPL_GSDLC_04_B_CURRENT.json`.

## 5. Riesgos y límites

- La persistencia runtime está deliberadamente en `outputs/drafts/gsdlc_04_b`; no es evidencia ni source control.
- El editor 04-B no promueve drafts a `APPROVED/FROZEN`; eso pertenece a 04-D.
- Los hints JSON de 04-B cubren parseo y metadatos de schema; la validación completa del perfil sigue perteneciendo al review flow.
- La prueba browser real, restart en Windows y conflicto concurrente visual siguen pendientes.
- No se declara calidad industrial final del workbench hasta 04-E.

## 6. PASS/BLOCK

### PASS-CANDIDATE

- authoring manual Markdown/JSON usable desde la UI;
- draft persiste sin escribir source;
- history/recover son reproducibles;
- lost update queda bloqueado por preimage/revision hash;
- actor deriva de sesión server-side;
- `S0=0`, `S1=0`, `full=0`.

### BLOCK

- source aprobado cambia al guardar/autoguardar draft;
- draft se usa como approval/evidence;
- XSS/raw HTML no confiable;
- stale preimage aceptado;
- legacy token/localStorage obtiene autoridad;
- runtime DB/store entra al ZIP fuente;
- browser Windows no demuestra restart recovery y conflict state.

## 7. Comandos y procedimiento

La única autoridad operativa es `GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_B_v1_0_7.md`. Este reporte no duplica comandos para evitar divergencia operacional.


## 8. Correctivo PRE-WINDOWS 001 — branch preparation harness

La primera ejecución Windows de 04-B quedó bloqueada antes de source mutation por una expresión PowerShell que invocaba `.Trim()` sobre la salida nula de `git branch --list` cuando la rama objetivo aún no existía. La evidencia preservada confirmó package SHA válido, predecessor HEAD exacto y worktree limpio.

Correctivo `v1.0.1`:

- mueve creación/selección de rama a `--phase prepare-repo` del operador Python;
- usa return codes de Git (`show-ref --verify --quiet`) y no parsing accidental de PowerShell;
- bloquea rama divergente sin reset/rebase/force;
- persiste checkpoints JSON externos incluso si Git status es vacío;
- agrega `repo-review` para consolidar diff check, tracked-runtime scan y status;
- no cambia el diseño funcional del editor ni consume full regression.

La corrida bloqueada permanece evidencia forense; no requiere rollback porque no alcanzó `apply`.


## 9. Correctivo PRE-WINDOWS 002 — Git blob preimage authority y señal terminal

La segunda ejecución Windows alcanzó `prepare-repo=PASS` y creó/seleccionó correctamente la rama 04-B sobre el predecessor exacto. El siguiente `preflight` bloqueó siete paths por `preimage-mismatch-or-unexpected-file` aun cuando `HEAD` seguía en `6b6cb70...c893` y `git status` estaba limpio. `apply` no se ejecutó.

RCA:

- el manifest fue generado contra bytes del candidate repo365;
- el operador v1.0.1 comparaba esos hashes contra bytes del worktree;
- Git puede normalizar/smudge LF/CRLF en checkout sin marcar el path dirty;
- por tanto, el hash byte-a-byte del worktree no es autoridad suficiente para un repo Git limpio;
- el contrato original ya exigía usar Git blob como autoridad cuando LF/CRLF pudiera variar.

Correctivo v1.0.2:

- cada preimage modificado registra Git blob OID SHA-1 esperado y SHA-256 canonical-LF;
- preflight usa SHA exacto cuando coincide y, ante diferencia de representación, valida el blob del predecessor;
- solo acepta esa ruta si `git diff` y `git diff --cached` están limpios;
- `skip-worktree` y `assume-unchanged` bloquean;
- postimage continúa requiriendo SHA-256 exacto;
- todas las fases Python imprimen como última línea `PASS` verde o `BLOCK` rojo;
- provisión, runtime, hashes del fixture, restore, browser evidence validation, commit y evidence packaging pasan a un harness Python dedicado.

Las dos primeras corridas bloqueadas no alcanzaron `apply` y no requirieron rollback.


## 10. Correctivo PRE-WINDOWS 003 — post-apply whitespace review y convergencia de estado

La tercera ejecución Windows alcanzó `bootstrap=PASS`, `prepare-repo=PASS`, `preflight=PASS` y **`apply=PASS`**. El delta 04-B quedó completamente materializado: `pending=[]`, `conflicts=[]`, `47/47 already_applied`. El bloqueo ocurrió después, en `repo-review`.

RCA:

- `git diff --check` emitió diagnósticos LF→CRLF para 24 archivos; esas advertencias son propias de la representación del checkout Windows y no constituyen por sí mismas un error de contenido;
- existía además un hallazgo real y único: `src/devpilot_core/interfaces/api/routers/workspace_edits.py:240: new blank line at EOF`;
- el source delta PRE-WINDOWS contenía dos terminadores LF al final de ese archivo, por lo que el bloqueo del `diff --check` fue correcto;
- el problema de diseño del harness era mezclar warnings de EOL con el hallazgo real en un único mensaje enorme y no disponer de una transición state-aware desde `v1.0.2 applied` a un correctivo posterior.

Correctivo v1.0.3:

- corrige `workspace_edits.py` a exactamente un terminador de línea final;
- `repo-review` ejecuta Git con `core.safecrlf=false`, separa warnings de errores reales y agrega higiene determinística sobre los archivos declarados, incluidos archivos nuevos/untracked;
- el manifest admite únicamente **preimages alternativas explícitas** para estados correctivos conocidos, de modo que `v1.0.3` puede converger desde repo365 limpio o desde el estado Windows `v1.0.2 already applied` sin reset, rebase, force ni sobrescritura ciega;
- la nueva fase `converge-source` combina inspección, apply correctivo, postimage verification y repo-review en un solo checkpoint idempotente;
- validation usa el Python del `.venv` del repo y resuelve `npm.cmd` explícitamente en Windows;
- el harness de commit también suprime warnings benignos de safecrlf y stagea solo la superficie realmente dirty y declarada;
- la guía v1.0.3 utiliza rutas absolutas bajo `C:\Users\Pedro\Downloads` y no exige completar placeholders de paths;
- se conserva la regla visual: toda instrucción Python concluye con última línea verde `PASS` o roja `BLOCK`.

Este correctivo **no revierte** el apply v1.0.2. Reconcilia únicamente el estado ya aplicado y continúa la validación. Full regression permanece en `0`.


## 11. Correctivo PRE-WINDOWS 004 — runtime de tres consolas y token explícito seguro

La cuarta ejecución Windows confirmó que la implementación 04-B y sus gates están sanos antes del browser: `converge-source=PASS`, provisioning PASS, focal `11/11`, acumulativo `48/48`, impacto `36/36`, schema/TCR/Project State/Docs Governance/API security PASS, UI static `15/15`, Vite production build PASS, fixture PASS y hash inicial PASS. El bloqueo ocurrió únicamente al intentar levantar API/UI mediante el antiguo `runtime-start` conjunto.

RCA literal de evidencia Windows:

- `api.log`: `API_EXECUTE_REQUIRES_EXPLICIT_TOKEN_BLOCK`; `api serve --execute` requiere que `DEVPILOT_API_TOKEN` exista explícitamente;
- v1.0.3 no configuró ese token antes de `Popen`;
- UI/Vite sí alcanzó `127.0.0.1:5173`, por lo que la aplicación podía verse parcialmente aunque la API estuviera ausente;
- el estado/PID solo se escribía después de que ambos runtimes quedaran READY, dejando un hueco de recovery cuando Vite sobrevivía como child process;
- el esquema de arrancar API+UI desde la consola general contradice la práctica Windows ya validada del proyecto: tres consolas independientes.

Correctivo v1.0.4:

- elimina `runtime-start` del flujo operativo autoritativo;
- hace obligatorio **Consola 1 CONTROL + Consola 2 API + Consola 3 UI**;
- incorpora `devpl_gsdlc_04_b_runtime_console.py`, con roles API/UI en foreground dedicado y logs redirigidos a evidencia;
- el rol API genera un token criptográficamente aleatorio únicamente en memoria, lo coloca en `DEVPILOT_API_TOKEN` del child process y nunca lo imprime/persiste;
- cada launcher registra PID/estado antes del readiness y deja una última línea verde PASS cuando el servicio está listo;
- `runtime-status` desde Consola 1 exige API+UI READY antes de abrir browser;
- `runtime-stop` desde Consola 1 cierra los child PIDs registrados y funciona incluso si Ctrl+C no responde en Consola 2/3;
- `runtime-recover` resuelve específicamente el orphan v1.0.3 en 5173 solo con evidencia suficiente y nunca usa kill por nombre;
- un listener inesperado en 8787 o un 5173 no atribuible a la evidencia conocida permanece BLOCK fail-closed.

No se requiere rollback de source. Full regression permanece en `0` y browser B1→B9 sigue pendiente.


## 12. Correctivo PRE-WINDOWS 005 — fixture PathGuard y active-workspace binding

La quinta ejecución Windows (guía v1.0.4) confirmó que el rediseño de tres consolas funciona: API y UI alcanzaron READY, `runtime-status=PASS`, login humano `owner.local` respondió correctamente y el cierre por Consola 1 dejó 8787/5173 libres. El primer `Project Entry / OPEN_EXISTING` devolvió HTTP 403 con `PROJECT_INTAKE_ALLOWED_ROOT_BLOCKED`.

RCA: el launcher API v1.0.4 configuró el token efímero, pero omitió `DEVPILOT_ALLOWED_WORKSPACE_ROOTS` y `DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT`. Por ello PathGuard rechazó el fixture, que está deliberadamente fuera del repo plataforma. Además, la plantilla de observaciones existente permaneció en una versión previa porque `prepare-observations` no actualizaba plantillas vacías ya existentes.

Correctivo v1.0.5:

- el launcher API autoriza exclusivamente `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER`;
- el mismo fixture queda como active workspace root y se elimina del child API una selección registry heredada que pudiera tener precedencia;
- `fixture-binding-precheck` valida read-only PathGuard, Project Entry dry-run y UI workspace context antes de iniciar browser;
- `runtime-status` exige además `fixture_binding_ready=true` y versiones runtime v1.0.5;
- la guía reemplaza `Complete Open` por instrucciones UI botón por botón, incluido approval y execute;
- se exige captura `00_project_entry_fixture_open.png`;
- una plantilla de observaciones antigua solo se refresca automáticamente si permanece sin resultados manuales; de lo contrario se bloquea para preservar evidencia.

No se requiere rollback de source. B1→B9 permanecen pendientes y full regression sigue en 0.


## 13. Correctivo PRE-WINDOWS 007 — evidencia browser versionada y parser delimitado

La ejecución Windows con bundle v1.0.6 pasó bootstrap, runtime-stop, convergencia, focal 12/12, acumulativo 49/49, impacto 36/36 y preparación del fixture. `prepare-observations` bloqueó antes de runtime/browser.

RCA: la plantilla histórica estaba vacía, pero `_observations_have_manual_results` escaneaba todo el Markdown y trataba los valores de referencia del bloque “Para un cierre PASS-CANDIDATE” (`browser_acceptance=PASS`, `S0_open=0`, etc.) como resultados humanos. El mismo diseño podía contaminar posteriormente el parser de `browser-evidence-validate`.

Correctivo v1.0.7:

- elimina por completo la heurística cross-version;
- crea `DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_v1_0_7.md` y nunca sobrescribe observaciones de otras guías;
- una segunda ejecución de prepare-observations preserva el archivo v1.0.7 existente sin inferir su contenido;
- el validator lee exclusivamente las secciones delimitadas `BEGIN/END_BROWSER_MATRIX` y `BEGIN/END_BROWSER_SUMMARY`;
- los textos instructivos quedan fuera del contrato parseable;
- `browser-preflight` consolida observaciones + fixture hash before + fixture binding en un único gate antes de levantar API/UI;
- B1→B9 siguen sin ejecutarse y no se requiere rollback.

## 14. Correctivo PRE-WINDOWS 008 — fixture Git clean y recovery stateful

La ejecución Windows v1.0.7 superó bootstrap, source convergence, focal 14/14, acumulativo 51/51, impacto 36/36, browser-preflight, API/UI READY, dry-run, revalidación, solicitud y aprobación. `POST /project-entry/execute` devolvió 403 y el bootstrap transaccional hizo rollback sin writes externos.

RCA determinístico: `prepare-browser` v1.0.7 creó y committeó los tres archivos baseline del fixture y luego escribió `.devpilot-gsdlc04b-browser-fixture.json`. Ese marker quedó untracked. El verificador heredado de GSDLC-03 para `OPEN_EXISTING` exige `git status` limpio y añadió `git-not-clean`, disparando rollback. El comportamiento del producto fue correcto; el defecto estaba en ownership del fixture del operador Windows.

v1.0.8:

- mueve ownership del fixture a evidencia externa; no escribe marker dentro del workspace;
- agrega `browser-recovery-008`: detiene solo los runtime PIDs registrados y elimina el marker legado solo si es la única entrada dirty y su metadata pertenece al fixture exacto;
- cualquier otro dirty state sigue BLOCK; no usa reset/clean/rebase/force;
- el fixture-binding probe y el launcher API exigen Git limpio antes de browser;
- el approval fallido v1.0.7 no se reutiliza: después del repair se exige dry-run/revalidate/approval nuevos;
- Consola 2 continúa silenciosa tras READY por diseño; `runtime/api_console.log` es la evidencia de access log para evitar deadlocks/interleaving de stdout;
- para reducir superficie de fallos, el correctivo 008 solo reejecuta focal 04-B + Source Registry + Documentation Governance y un self-test stateful de dirty-marker→rollback→repair→execute PASS; no repite gates ya verdes ni full regression.

B1→B9 permanecen pendientes. No se autoriza 04-C hasta browser PASS, commit/candidate/evidence Windows y adjudicación owner.

## Corrective Recovery-009 — restart state machine after B2

Windows v1.0.8 advanced through a successful `OPEN_EXISTING`, produced browser evidence `00/01/02`, executed B1/B2, proved the approved Markdown source unchanged during draft autosave, and shut down API/UI cleanly for B3. The subsequent API restart was blocked before server start because the v1.0.8 runtime guard applied a `PRE_OPEN` residue rule after the workspace had already reached a successful post-open state.

The two files involved are not invalid residue after a successful open:

- `.devpilot/bootstrap-execution.json` is the final PASS execution manifest intentionally written by `ProjectBootstrapExecutor`;
- `.devpilot/workspace-registration.json` is the target-local registration intentionally written by the same transaction.

Historical GSDLC-03-D tests also require these files after a successful bootstrap/open transaction. They are excluded from workspace Git status and therefore can coexist with a clean source tree.

Recovery-009 introduces an explicit fixture lifecycle contract:

- `PRE_OPEN`: exact baseline fixture with no bootstrap/registration metadata;
- `POST_OPEN_PASS`: exact baseline Git blobs plus both metadata files, validated as `OPEN_EXISTING`, project `gsdlc04b-browser`, target exact, verification Git clean, non-empty plan/preimage/approval, local-only, no network/external API, and zero writes outside workspace.

Partial metadata, `ROLLED-BACK`, mismatched project/target, dirty Git, unexpected tracked files or malformed JSON remain fail-closed and are never deleted automatically.

The new read-only `browser-resume-009` checkpoint preserves the already-started v1.0.8 browser run and requires before restart:

- ports 8787/5173 free;
- fixture `POST_OPEN_PASS` + Git clean;
- screenshots `00`, `01`, `02` present;
- B2 source hash evidence PASS;
- current observation file preserved;
- exactly one active persisted runtime draft for `docs/manual_authoring.md` with a valid current revision and unchanged source preimage.

After this checkpoint the guide resumes directly at B3. It explicitly forbids replaying Open Existing, B1 or B2. Corrective validation remains limited to focal 04-B, Source Registry and Documentation Governance; full regression remains at zero.


## 16. Correctivo PRE-WINDOWS 010 — autoridad Git/canonical-LF para hash final del fixture

La ejecución Windows v1.0.9 alcanzó el paso final de restauración del fixture después de B7 y obtuvo `fixture-restore=PASS`. Las capturas browser `00`→`08` ya estaban presentes. El siguiente `fixture-hash --label after` bloqueó porque comparaba SHA-256 de bytes físicos contra el hash inicial.

RCA determinístico:

- hash físico inicial Markdown LF: `1f79747c99fcba3f81d43086adacbf1ce20d82c2b0bae25f05d820e933da0038`;
- hash físico después de `git restore` en Windows CRLF: `fe5e3a19387f8afbd27b3468f4caf1d3cffa3b2533d8110b5418fb5d8460317e`;
- `fe5e3a19...` es exactamente la representación CRLF del mismo contenido cuyo canonical-LF es `1f79747c...`;
- no existe evidencia de cambio lógico del source.

v1.0.10 reemplaza la comparación raw-byte como autoridad por `Git blob + canonical-LF + git diff/cached clean`; el SHA físico queda solo como diagnóstico. Una diferencia exclusivamente LF/CRLF pasa; un cambio real continúa bloqueando. No se repiten B1→B9 ni full regression.
