---
doc_id: "DEVPL-GSDLC-04-D-UNIQUE-WINDOWS-GUIDE"
title: "DEVPL-GSDLC-04-D — Guía única de implementación, validación y evidencia Windows"
status: "ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-22"
approval: "pending_windows_execution"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-D"
predecessor_repo: "repo_DevPilot_Local_367_DEVPL_GSDLC_04_C_EXTERNAL_SOURCE_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip"
predecessor_commit: "ce03b2975320617e8a3663ced2d15736aa9e3c1a"
predecessor_sha256: "7700f77d00d578c183cd47908996235cc898d49876c8d48278b21c0b905d8484"
full_regression_allowed: false
three_console_runtime_required: true
---

# DEVPL-GSDLC-04-D — Guía única Windows

Esta es la **única instrucción operativa autoritativa** para instalar, validar y producir evidencia de `GSDLC-04-D — Validate, findings, diff, approval, apply and freeze`.

## 0. Reglas de ejecución

1. Descargue y extraiga el bundle exactamente en `C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_D_READY_FOR_WINDOWS_BUNDLE_v1_0_0`.
2. Use tres PowerShell separadas durante browser acceptance: **Consola 1 — CONTROL**, **Consola 2 — API**, **Consola 3 — UI**.
3. Cada comando PowerShell de esta guía ocupa una sola línea física. Copie y pegue la línea completa.
4. No use `reset --hard`, `git clean`, rebase, force push ni limpieza genérica para corregir un BLOCK.
5. No acceda a `D:\Projects\DevPilot_Workspaces\inventory-sales-local`.
6. No ejecute full regression. GSDLC-04-D debe terminar con `full regression = 0`; la única full del backlog está reservada para 04-E.
7. El operador es state-aware: si una ejecución se interrumpe, no reinicie desde cero ni borre cambios. Reanude desde el último checkpoint PASS de esta guía.
8. Las diferencias físicas LF/CRLF no son autoridad suficiente de fallo. El operador usa SHA físico primero y, solo para paths Git-clean, permite equivalencia canonical-LF si coinciden el working tree y el blob Git inmutable del predecessor.
9. No sobrescriba evidencia, candidate ni ZIP sellados. Si un artefacto ya existe y el operador lo bloquea, preserve el estado y reporte el BLOCK.
10. La única mutación de source esperada durante browser acceptance ocurre sobre el fixture controlado 04-D y debe ser exactamente `docs/gsdlc04d_review_candidate.md`; el repo DevPilot no se modifica durante el browser journey.
11. `sessionStorage/localStorage` son UX-only. Session, RBAC, approval, preimage, apply y freeze permanecen server-side.
12. El source write reutiliza UOC-005 `WorkspaceEditExecutionApplicationService`; no existe un segundo write engine ni arbitrary shell.

## 1. Consola 1 — instalar/verificar el package

Ejecute:

```powershell
python "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_D_READY_FOR_WINDOWS_BUNDLE_v1_0_0\DEVPL_GSDLC_04_D_BOOTSTRAP_v1_0_0.py" --bundle-root "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_D_READY_FOR_WINDOWS_BUNDLE_v1_0_0"
```

Debe terminar en una línea verde `PASS`. El bootstrap comprueba consenso de hashes del package, CRC del ZIP y `ARTIFACT_HASHES.json`; materializa el package bajo `D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d`. No modifica source ni Git.

Anote el valor `package_sha256`: se copiará literalmente al archivo de observaciones manuales.

## 2. Consola 1 — preparar la rama 04-D

La fuente de verdad debe ser el repo Windows limpio correspondiente a repo367, con HEAD exacto `ce03b2975320617e8a3663ced2d15736aa9e3c1a`.

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase prepare-repo --branch-name "feat/devpl-gsdlc-04-d-governed-artifact-apply" --execute
```

Debe terminar `PASS`. El operador solo crea o selecciona la rama 04-D si apunta exactamente al predecessor. No hace reset, rebase ni limpieza.

## 3. Consola 1 — preflight read-only

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase preflight --branch-name "feat/devpl-gsdlc-04-d-governed-artifact-apply"
```

Debe terminar `PASS`, sin conflictos y sin dirty paths fuera del source delta 04-D. No escribe source.

## 4. Consola 1 — converger source 04-D

Ejecute una sola vez:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase converge-source --branch-name "feat/devpl-gsdlc-04-d-governed-artifact-apply" --execute
```

Resultado esperado: `PASS`, `pending=[]`, `conflicts=[]`. El operador aplica únicamente los postimages del manifest y reemplaza archivo-a-archivo con retry acotado.

Si el comando se interrumpe después de aplicar parte del delta, vuelva a ejecutar primero el **Paso 3**. Si preflight da PASS, puede volver a ejecutar este paso; los postimages ya aplicados se reconocen y no se reescriben innecesariamente.

## 5. Consola 1 — repo-review

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase repo-review
```

Debe terminar `PASS`, con `unexpected_git_entries=[]`, `diff_check=PASS` y `forbidden_tracked_total=0`.

## 6. Consola 1 — provision-check

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --step provision-check
```

Debe confirmar `.venv`, `npm` y `ui/web/node_modules`. No instala dependencias y no usa red.

## 7. Consola 1 — validación focal/acumulativa 04-D

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase validate
```

Este gate ejecuta únicamente la validación 04-D focal, acumulativa A→D y basada en impacto: lifecycle, drafts, imports, UOC-004/UOC-005, RBAC, Documentation Source Registry, Contract Reconciliation, planner/executor, API plan/apply, Project State, TCR v1/v2, Documentation Governance, API contract/security, UI route enforcement, smoke UI 04-D y Vite build.

Debe terminar `PASS`. **No ejecuta full regression**.

## 8. Consola 1 — preparar fixture e inputs browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER" --browser-input-root "D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-D\browser_inputs" --step prepare-browser
```

El harness crea/reutiliza exclusivamente:

- fixture Git: `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER`;
- inputs: `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-D\browser_inputs`;
- observaciones: `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D\DEVPL_GSDLC_04_D_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md`.

El fixture contiene únicamente `.devpilot/project.yaml`, `docs/baseline.md` y `docs/baseline.json` como baseline Git. No copia `auth.db*`, `devpilot.db*` ni runtime stores.

## 9. Consola 1 — browser-preflight

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER" --browser-input-root "D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-D\browser_inputs" --step browser-preflight
```

Debe terminar `PASS`: puertos 8787/5173 libres, fixture Git clean, baseline equivalente a sus blobs Git y binding preparado al fixture 04-D.

## 10. Consola 2 — API

Abra una segunda PowerShell y ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_runtime_console.py" --role api --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER"
```

Espere `PASS — API lista ...` y deje la consola abierta. El token es efímero, no se imprime ni persiste.

## 11. Consola 3 — UI

Abra una tercera PowerShell y ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_runtime_console.py" --role ui --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER"
```

Espere `PASS — UI lista ...` y deje Consola 3 abierta.

## 12. Consola 1 — confirmar readiness conjunto

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER" --step runtime-status
```

Debe terminar `PASS` con API+UI READY y binding exclusivo al fixture 04-D.

## 13. Browser — abrir el fixture por journey normal

1. Abra `http://127.0.0.1:5173/`.
2. Inicie sesión con las credenciales locales habituales de `owner.local`.
3. En Project Home pulse **Open existing project**.
4. Configure exactamente: modo `Abrir existente`; Project ID `gsdlc04d-browser`; Nombre `GSDLC 04-D browser fixture`; ruta `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER`.
5. Genere dry-run una sola vez; compruebe PASS, `OPEN_EXISTING`, `Writes ejecutados=false`, `Network usada=false`.
6. Pulse **Revalidar preimage** y espere PASS.
7. Motivo de aprobación: `Abrir fixture GSDLC 04-D para browser acceptance.`
8. Solicite approval, abra Approval Center dirigido, apruebe exactamente el Approval ID mostrado, vuelva a Project Entry, pulse **Verificar approval** y después **Ejecutar plan aprobado**.
9. Continúe a Estado del proyecto → **Documentos**.
10. Debe ver simultáneamente `Artifact Workbench · importar fuente externa` y `Artifact Review · validate, approve, apply & freeze`.
11. Guarde `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D\browser\00_project_review_ready.png`.

Para cada captura use `Win+Shift+S`; guarde el PNG con el nombre exacto. Antes de guardar confirme que no contiene passwords, tokens, cookies, API keys ni secretos.

## 14. Browser C1 — DRAFT inválido → FINDINGS + navegación

1. En `Artifact Workbench · importar fuente externa`, seleccione `Importar archivo externo`.
2. Destino: `docs/gsdlc04d_invalid.md`.
3. Source label: `Browser 04-D invalid findings`.
4. Seleccione exactamente `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-D\browser_inputs\invalid_review_source.md`.
5. Pulse **Generar preview** y compruebe preview PASS, sin writes ni network.
6. Pulse **Crear DRAFT**. El panel `Artifact Review` debe recibir automáticamente ese Import ID.
7. En `Artifact Review` pulse **Validar DRAFT**.
8. Debe quedar en estado FINDINGS/BLOCK de promoción y mostrar al menos un finding; no debe aparecer un plan aplicable ni habilitarse un source write.
9. Si aparece **Ir al hallazgo**, púlselo y confirme que la UI intenta llevar la atención al location/section correspondiente cuando el origen es navegable.
10. Guarde `01_findings_navigation.png` mostrando findings y ausencia de promoción.
11. **No solicite approval y no intente aplicar este DRAFT inválido.**

## 15. Browser C2 — DRAFT válido → plan/diff inmutable

1. Vuelva al panel de importación.
2. Seleccione `Importar archivo externo`.
3. Destino: `docs/gsdlc04d_review_candidate.md`.
4. Source label: `Browser 04-D governed apply`.
5. Seleccione exactamente `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-D\browser_inputs\valid_review_source.md`.
6. Genere preview y después **Crear DRAFT**.
7. En `Artifact Review` pulse **Validar DRAFT**.
8. Debe mostrarse `APPROVAL_REQUIRED`, target exacto `docs/gsdlc04d_review_candidate.md`, `Plan hash`, `Base hash`, `Content hash` y un diff visible.
9. Guarde `02_plan_diff.png` procurando que target, plan hash y diff sean legibles.

## 16. Browser C3 — approval exacto dirigido

1. En **Motivo de approval** escriba `Promover artefacto 04-D validado mediante apply gobernado y freeze.`
2. Pulse **Solicitar approval** una sola vez.
3. Anote el Approval ID mostrado por el panel.
4. Pulse **Abrir Approval Center ↗**.
5. En la nueva pestaña verifique que el handoff apunta exactamente a ese Approval ID; no use otro approval del listado.
6. Apruebe exactamente ese ID como `owner.local`.
7. Guarde `03_targeted_approval.png` mostrando el Approval ID exacto y la decisión `approved`, sin credenciales.
8. Vuelva a la pestaña del Artifact Workbench.

## 17. Browser C4 — verificar approval + atomic apply

1. Pulse **Verificar approval** y espere `PASS · approval exacto ... está approved.`
2. Pulse **Aplicar cambio aprobado** una sola vez.
3. Debe aparecer `PASS · atomic apply verificado (...)`; anote que existe execution ID.
4. No edite manualmente el archivo creado.
5. Guarde `04_atomic_apply.png` mostrando el PASS del apply y el execution ID.

## 18. Browser C5 — freeze del hash aprobado

1. Pulse **Freeze hash aprobado** una sola vez.
2. Debe aparecer `PASS · FROZEN en hash ...; transition evidence emitida.`
3. El panel debe mostrar el review en estado `FROZEN` y el hash aprobado.
4. Guarde `05_frozen_hash.png` mostrando estado y hash.

## 19. Browser C6 — Sesión/RBAC

1. En la pestaña principal pulse **Cerrar sesión**.
2. Navegue a `http://127.0.0.1:5173/workspace/documents`.
3. Debe aparecer Login; Artifact Review y sus botones de approval/apply/freeze no deben estar disponibles.
4. La comprobación y la observación manual son obligatorias. `07_session_rbac.png` es opcional.
5. Después de este punto no necesita iniciar sesión de nuevo.

## 20. Consola 1 — verificar scope exacto del source write

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER" --step source-scope-after
```

Debe terminar `PASS` demostrando simultáneamente:

- Git dirty paths del fixture = exactamente `docs/gsdlc04d_review_candidate.md`;
- `docs/gsdlc04d_invalid.md` no existe;
- los tres archivos baseline permanecen equivalentes a sus Git blobs;
- review final = `FROZEN`;
- `approval_valid=true`;
- approved SHA coincide con el archivo real;
- approval ID, execution ID, plan ID y plan hash presentes;
- `unexpected_source_writes_total=0`.

## 21. Consola 1 — cerrar API y UI

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --step runtime-stop
```

Debe terminar `PASS`, `ports_free=true`. El harness termina únicamente árboles de procesos registrados por los launchers 04-D; nunca mata todos los procesos Python/Node por nombre.

## 22. Completar observaciones manuales

Abra:

`D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D\DEVPL_GSDLC_04_D_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md`

Complete:

- fecha/hora real de la aceptación;
- operador;
- browser/versión real;
- `ZIP de implementación SHA-256` con el `package_sha256` exacto del bootstrap;
- cada fila con `PASS` o `BLOCK` y una frase breve de lo realmente observado.

Si todos los casos fueron PASS, el bloque resumen debe quedar exactamente:

```text
- `browser_acceptance`: PASS
- `S0_open`: 0
- `S1_open`: 0
- `secrets_exposed`: false
- `network_runtime_used`: false
- `external_api_used`: false
- `pilot_workspace_accessed`: false
- `full_regression_runs`: 0
```

En **Decisión** escriba `PASS-CANDIDATE`, no `PASS`.

Justificación recomendada **solo si coincide con lo observado**: `Validation/findings, plan/diff inmutable, approval exacto, atomic apply UOC-005 y freeze quedaron demostrados end-to-end; el DRAFT inválido no escribió source, el DRAFT válido mutó únicamente el artefacto declarado, el hash FROZEN coincide con el source, session/RBAC permanecieron server-side, S0/S1=0 y full regression=0.`

## 23. Consola 1 — validar evidencia browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --step browser-evidence-validate
```

Debe devolver `PASS`, sin casos faltantes, sin filas BLOCK, sin observaciones vacías, sin screenshots obligatorios faltantes, resumen exacto y decisión `PASS-CANDIDATE` con justificación no vacía.

## 24. Consola 1 — repo-review final

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase repo-review
```

Debe terminar `PASS` y no listar dirty paths fuera del source delta 04-D. La mutación del fixture browser no pertenece al repo DevPilot y no afecta este gate.

## 25. Consola 1 — commit 04-D

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --phase git-commit --commit-message "feat(gsdlc-04-d): govern artifact review apply and freeze" --execute
```

El operador exige previamente el marker browser PASS. Stagea exclusivamente los dirty paths autorizados por el manifest. Debe terminar `PASS`, mostrar el nuevo commit SHA y `worktree_clean=true`.

## 26. Consola 1 — generar candidate Windows desde Git HEAD

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --phase package-git-head --execute
```

Resultado esperado:

`D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\gsdlc_04_d\repo_DevPilot_Local_368_DEVPL_GSDLC_04_D_GOVERNED_ARTIFACT_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip`

más su `.sha256`. Se genera con `git archive` y no incluye runtime/caches no trackeados.

## 27. Consola 1 — sellar evidencia Windows

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_d\DEVPL_GSDLC_04_D_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_d_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --step package-evidence
```

Debe generar:

- `D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\evidence\DEVPL_GSDLC_04_D_WINDOWS_EVIDENCE_v1_0_0.zip`;
- su `.sha256`.

El harness ejecuta redaction scan antes de sellar. Ante BLOCK preserve evidencia y no borre logs para ocultar el hallazgo.

## 28. Evidencia que debe devolver para owner adjudication

Adjunte en el siguiente prompt:

1. captura manual completa de Consola 1 de esta ejecución;
2. `DEVPL_GSDLC_04_D_WINDOWS_EVIDENCE_v1_0_0.zip`;
3. su `.sha256`;
4. `repo_DevPilot_Local_368_DEVPL_GSDLC_04_D_GOVERNED_ARTIFACT_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip`;
5. su `.sha256`.

No adjunte `.venv`, `node_modules`, `outputs`, runtime DBs ni el fixture completo: el evidence ZIP contiene checkpoints, hashes y screenshots necesarios.

## 29. Resultado esperado

Si todos los pasos terminan PASS, el estado correcto es:

`GSDLC-04-D = PASS-CANDIDATE / WINDOWS-VALIDATED / OWNER-ADJUDICATION-PENDING`

No declare todavía `CLOSED/PASS`. GSDLC-04-E permanece bloqueado hasta owner adjudication. La única full regression del backlog continúa reservada para 04-E.
