---
doc_id: "DEVPL-GSDLC-04-E-UNIQUE-WINDOWS-GUIDE"
title: "DEVPL-GSDLC-04-E — Guía única de implementación, browser closure y full regression exactly-once"
status: "ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-22"
approval: "execution_required"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-E"
source_repo: "repo_DevPilot_Local_368_DEVPL_GSDLC_04_D_GOVERNED_ARTIFACT_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "e1d9d1c722dc3fa389ce4cb7c3e18bc401d081cd"
source_repo_sha256: "314c32d765fc2e4a2f470c4facc091b72d5951a3a9956c019d05561a885de8b9"
full_regression_allowed: true
full_regression_max_runs: 1
full_regression_after_browser_only: true
pilot_workspace_access_allowed: false
three_console_runtime_required: true
---

# DEVPL-GSDLC-04-E — Guía única Windows

Esta guía es la **única autoridad operativa** para implementar y validar GSDLC-04-E. No mezcle instrucciones de 04-D ni de correctives anteriores.

El objetivo es demostrar, en un fixture aislado, el cierre completo del Artifact Workbench: autoría MANUAL + PASTE/UPLOAD/IMPORT, validate/findings, plan/diff, approval/apply/freeze, detección de edición externa y `REVALIDATION_REQUIRED`, recovery y accesibilidad. Después del browser PASS se consume **una sola vez** la full regression de todo GSDLC-04.

## 0. Reglas no negociables

1. No use `reset --hard`, `git clean`, rebase, force push ni checkout destructivo.
2. No acceda a `D:\Projects\DevPilot_Workspaces\inventory-sales-local`.
3. No copie `auth.db*`, `devpilot.db*` ni stores runtime al repo/candidate.
4. No ejecute la full regression antes de que esta guía lo indique.
5. Cuando ejecute la full regression, hágalo **una sola vez**. Si termina FAIL/BLOCK, **NO vuelva a ejecutar ese comando**. Preserve todo y devuelva evidencia para recuperación compuesta.
6. En browser, no use PowerShell para crear o editar artefactos del journey normal. Los cambios externos pedidos por esta guía se realizan con Notepad/VS Code/File Explorer sobre el fixture aislado.
7. No guarde screenshots con passwords, tokens, cookies, `.env`, API keys ni secretos.
8. Ante cualquier línea roja `BLOCK`, deténgase. No intente “arreglar” manualmente Git/source.
9. Todos los comandos PowerShell de esta guía están escritos en una sola línea física.

## 1. Descargar y extraer el bundle

Descargue `DEVPL_GSDLC_04_E_READY_FOR_WINDOWS_BUNDLE_v1_0_0.zip` y extráigalo exactamente en:

`C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_E_READY_FOR_WINDOWS_BUNDLE_v1_0_0`

Debe existir:

`C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_E_READY_FOR_WINDOWS_BUNDLE_v1_0_0\DEVPL_GSDLC_04_E_BOOTSTRAP_v1_0_0.py`

## 2. Consola 1 — bootstrap

Ejecute:

```powershell
python "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_E_READY_FOR_WINDOWS_BUNDLE_v1_0_0\DEVPL_GSDLC_04_E_BOOTSTRAP_v1_0_0.py" --bundle-root "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_E_READY_FOR_WINDOWS_BUNDLE_v1_0_0"
```

Debe terminar `PASS`. Anote `package_sha256`; se copiará luego en las observaciones manuales.

El package queda en:

`D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0`

## 3. Consola 1 — preparar rama 04-E

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase prepare-repo --branch-name "feat/devpl-gsdlc-04-e-artifact-workbench-browser-closure" --execute
```

Debe terminar `PASS`, con HEAD predecessor `e1d9d1c722dc3fa389ce4cb7c3e18bc401d081cd` y worktree limpio.

## 4. Consola 1 — preflight read-only

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase preflight --branch-name "feat/devpl-gsdlc-04-e-artifact-workbench-browser-closure"
```

Debe terminar `PASS`, sin conflictos ni dirty paths desconocidos. La equivalencia LF/CRLF se acepta únicamente mediante Git blob + canonical-LF cuando el path está Git-clean.

## 5. Consola 1 — converger source 04-E

Ejecute una sola vez:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase converge-source --branch-name "feat/devpl-gsdlc-04-e-artifact-workbench-browser-closure" --execute
```

Debe terminar `PASS` y luego mostrar `pending=[]`, `conflicts=[]`.

## 6. Consola 1 — repo-review previo

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase repo-review
```

Debe terminar `PASS`, `diff_check=PASS`, sin paths inesperados.

## 7. Consola 1 — provision-check

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --step provision-check
```

Debe indicar `.venv` disponible, npm disponible y `node_modules_exists=true`. No instale dependencias ni use red si el gate ya da PASS.

## 8. Consola 1 — gates baratos + Contract Reconciliation antes del browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase validate
```

Debe terminar `PASS`. Esta fase ejecuta focal E, acumulativa A→E, UOC-004/UOC-005, RBAC, **Test Impact v2 sobre el source delta exacto**, Project State, Source Registry, TCR v1/v2, Documentation Governance, API/UI registries, UI static y build. **No ejecuta full regression.** El archivo de changed paths usado por Test Impact se genera automáticamente desde `SOURCE_DELTA_MANIFEST.json`; el operador no debe construirlo manualmente.

## 9. Consola 1 — preparar fixture browser 04-E

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER" --browser-input-root "D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs" --step prepare-browser
```

Debe terminar `PASS`. Se crea/reutiliza únicamente el fixture 04-E y un usuario sintético `viewer04e.local`. La contraseña temporal se guarda **solo** en:

`D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs\VIEWER_LOGIN_DO_NOT_ATTACH.txt`

No adjunte ese archivo como evidencia y no lo fotografíe.

## 10. Consola 1 — browser-preflight

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER" --browser-input-root "D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs" --step browser-preflight
```

Debe terminar `PASS`, con fixture Git-clean y baselines Git-equivalentes.

## 11. Consola 2 — levantar API y dejar abierta

Abra una segunda PowerShell y ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_runtime_console.py" --role api --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER"
```

Debe terminar la inicialización en `PASS` y quedar abierta.

## 12. Consola 3 — levantar UI y dejar abierta

Abra una tercera PowerShell y ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_runtime_console.py" --role ui --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER"
```

Debe quedar `PASS` y abierta.

## 13. Consola 1 — runtime-status

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER" --step runtime-status
```

Debe devolver API+UI READY y binding exacto al fixture 04-E.

# Browser acceptance — 18 escenarios

Las capturas van en:

`D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E\browser`

Cada screenshot debe mostrar el resultado, pero no secretos. No cambie los nombres.

## 14. Browser B00 — abrir fixture por journey normal

1. Abra `http://127.0.0.1:5173/`.
2. Inicie sesión como `owner.local` con sus credenciales locales habituales.
3. En Project Home elija **Abrir proyecto existente / Open Existing**.
4. Use Project ID `gsdlc04e-browser`, nombre `GSDLC 04-E browser fixture` y ruta `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER`.
5. Genere dry-run, revalide preimage, solicite approval si se exige, apruebe únicamente el ID exacto en Approval Center, verifique y ejecute el plan.
6. Entre a Estado del proyecto → **Documentos**.
7. Confirme visibles: `Artifact Workbench · autoría manual`, `Artifact Workbench · importar fuente externa`, `Artifact Review · validate, approve, apply & freeze` y el panel de reconciliación cuando exista un review elegible.
8. Capture `00_project_active_workbench.png`.

## 15. Browser B01 — route guard sin project context

1. Abra **una pestaña nueva** escribiendo directamente `http://127.0.0.1:5173/workspace/documents`.
2. Como `sessionStorage` de contexto no se comparte a una pestaña nueva, la ruta debe quedar protegida/redirect y no debe mostrar el workbench como superficie autorizada.
3. Capture `01_project_context_guard.png` mostrando el guard/redirect.
4. Cierre esa pestaña y vuelva a la principal. No borre el contexto de la pestaña principal.

## 16. Browser B02 — MANUAL Markdown DRAFT

1. En Documentos seleccione `docs/manual_authoring.md`.
2. En `Artifact Workbench · autoría manual` escriba al final una línea inocua: `Edición manual browser 04-E.`
3. Espere autosave o pulse **Guardar draft** una sola vez.
4. Confirme estado de draft guardado y que no se ha sobrescrito todavía el source aprobado.
5. Capture `02_manual_markdown_draft.png`.

## 17. Browser B03 — autosave/restart recovery

1. Con el draft anterior guardado, pulse `Ctrl+R` una sola vez.
2. Si el refresh devuelve a Login/Project Home, inicie sesión y reabra **el mismo fixture** por el journey normal; no use comandos.
3. Vuelva a `docs/manual_authoring.md`.
4. Confirme que el DRAFT se recuperó y conserva la línea `Edición manual browser 04-E.`.
5. Capture `03_manual_autosave_recovery.png` mostrando el draft recuperado/version history.

## 18. Browser B04 — JSON DRAFT + hints

1. Seleccione `docs/manual_authoring.json`.
2. Cambie temporalmente el contenido del DRAFT para introducir un JSON incompleto, por ejemplo eliminando una llave de cierre en el editor **sin aplicar al source**.
3. Confirme que `Hints` muestra el problema y que Preview no ejecuta contenido.
4. Capture `04_json_hints.png`.
5. Use **Descartar draft** para volver al source base.

## 19. Browser B05 — PASTE provenance

1. En `Artifact Workbench · importar fuente externa` elija modo PASTE.
2. Destino: `docs/gsdlc04e_paste.md`.
3. Source label: `Browser 04-E paste provenance`.
4. Pegue un Markdown corto y no secreto.
5. Pulse **Generar preview** y luego **Crear DRAFT**.
6. Confirme `Origen=PASTE`, hashes, `Workspace writes=false`, `Network=false`.
7. Capture `05_paste_provenance.png`.

## 20. Browser B06 — UPLOAD/IMPORT soportado

1. Elija UPLOAD o IMPORT.
2. Seleccione `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs\upload_source.md` y use destino `docs/gsdlc04e_upload.md`.
3. Genere preview y DRAFT; confirme provenance/hashes.
4. Repita con `import_source.json` hacia `docs/gsdlc04e_import.json` si la UI permite ambos modos en la misma sesión.
5. Capture `06_upload_import.png` mostrando al menos un import soportado y su provenance.

## 21. Browser B07 — upload negativo

1. Seleccione `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs\unsupported_payload.exe` o use un destino traversal como `../escape.md`.
2. Intente generar preview **una sola vez**.
3. Debe quedar BLOCK/fail-closed; no debe crearse DRAFT ni source write.
4. Capture `07_upload_negative.png`.

## 22. Browser B08 — validate/findings/navigation

1. Importe `invalid_review_source.md` hacia `docs/gsdlc04e_invalid.md` como DRAFT.
2. En Artifact Review pulse **Validar DRAFT**.
3. Debe quedar `FINDINGS`, no `APPROVAL_REQUIRED`.
4. Pulse **Ir al hallazgo** en un finding navegable y confirme que el editor posiciona/identifica la sección o línea.
5. Capture `08_findings_navigation.png`.
6. No aplique ni congele este artefacto.

## 23. Browser B11 — wrong-role approval denied

Este escenario se realiza **antes** de la aprobación owner final para no contaminar el approval válido.

1. Cierre sesión owner.
2. Abra con Notepad, fuera del navegador, `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs\VIEWER_LOGIN_DO_NOT_ATTACH.txt` y lea las credenciales sintéticas. **No tome captura mientras el password esté visible.**
3. Inicie sesión en DevPilot como `viewer04e.local`.
4. Reabra el mismo fixture por Open Existing si el route guard lo exige.
5. Intente acceder al flujo de approval/review. Debe quedar denegado por RBAC/authority; el viewer no debe poder aprobar/aplicar/congelar.
6. Cierre cualquier diálogo con credenciales y capture `11_wrong_role_denied.png` mostrando únicamente la denegación UI/API y la identidad viewer, nunca el password.
7. Cierre sesión viewer.
8. Vuelva a iniciar sesión como `owner.local` y reabra el fixture por el journey normal.

## 24. Browser B13 — stale preimage invalida plan/approval

1. Importe `valid_review_source.md` hacia `docs/gsdlc04e_stale_target.md` y cree DRAFT.
2. Valide hasta `APPROVAL_REQUIRED`.
3. Solicite approval, abra Approval Center dirigido, apruebe exactamente ese ID, vuelva y verifique approval.
4. **Antes de pulsar Aplicar**, abra Notepad y cree manualmente `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER\docs\gsdlc04e_stale_target.md` con texto `External stale preimage.` y guarde.
5. Vuelva al browser y pulse **Aplicar cambio aprobado** una sola vez.
6. Debe BLOCK por stale preimage; el approval/plan no puede aplicarse sobre contenido cambiado.
7. Capture `13_stale_preimage.png` mostrando el BLOCK sin secretos.
8. Con File Explorer elimine únicamente `docs\gsdlc04e_stale_target.md`. No use PowerShell/Git para limpiarlo.

## 25. Browser B09 — plan/diff final para el artefacto que sí se promoverá

1. Importe `valid_review_source.md` hacia `docs/gsdlc04e_review_candidate.md`.
2. Source label: `Browser 04-E governed close`.
3. Preview → Crear DRAFT → Validar DRAFT.
4. Debe quedar `APPROVAL_REQUIRED`.
5. Confirme target, Plan hash, Base hash, Content hash y diff completo.
6. Capture `09_plan_diff.png`.

## 26. Browser B10 — approval exacto owner

1. En Motivo escriba: `Promover artefacto 04-E para cierre gobernado y reconciliación externa.`
2. Pulse **Solicitar approval** una vez.
3. Abra **Approval Center ↗**; debe abrir el ID exacto, sin route-guard incorrecto.
4. Apruebe únicamente ese ID como owner.
5. Capture `10_owner_approval.png` mostrando ID exacto y estado `approved`.
6. Cierre esa pestaña y vuelva al Workbench.

## 27. Browser B12 — apply + freeze

1. Pulse **Verificar approval** y espere PASS.
2. Pulse **Aplicar cambio aprobado** una sola vez; espere `atomic apply verificado` y execution ID.
3. Pulse **Freeze hash aprobado** una sola vez.
4. Confirme estado `FROZEN` y approved hash visible.
5. Capture `12_apply_freeze.png`.

## 28. Browser B14 — edición externa FROZEN → REVALIDATION_REQUIRED

1. Sin cerrar el browser, abra con Notepad o VS Code el archivo `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER\docs\gsdlc04e_review_candidate.md`.
2. Al final agregue exactamente una línea: `External editor drift 04-E.` y guarde.
3. No use Git revert, no deshaga el cambio y no cree commits en el fixture.
4. Vuelva al Artifact Review y pulse **Detectar cambio externo**.
5. Debe quedar `REVALIDATION_REQUIRED`, `approval_valid=false` y debe mostrarse source provenance `EXTERNAL_EDITOR`, hash previo/actual y Git diff.
6. No debe aparecer auto-revert ni hidden merge.
7. Capture `14_external_revalidation.png` mostrando estado, provenance y diff.

## 29. Browser B15 — rollback/recovery gobernado

1. Seleccione `docs/baseline.md`.
2. En autoría manual cree un DRAFT añadiendo `Temporary rollback proof 04-E.`.
3. En `Edición documental gobernada` genere el plan inmutable desde ese DRAFT y revalide hash base.
4. Solicite approval de apply, apruebe exactamente el ID correspondiente y aplique.
5. Después solicite approval de rollback, apruebe exactamente ese ID y pulse **Revertir cambio aprobado**.
6. Confirme que `docs/baseline.md` vuelve al contenido/hash inicial y que no quedan writes parciales.
7. Capture `15_rollback_recovery.png` mostrando rollback PASS/restored preimage.

## 30. Browser B16 — API-down/timeout recovery

1. Mantenga abierta la UI.
2. En Consola 1 ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --step runtime-stop-api
```

3. En browser provoque una lectura inocua, por ejemplo recargar una vista/documento. La UI debe mostrar un error/recovery comprensible, no pantalla en blanco ni loop.
4. Capture `16_api_down_recovery.png`.
5. En Consola 2 vuelva a ejecutar el mismo comando de API del paso 11. El runtime console acepta el fixture con los dirty paths browser previstos.
6. En Consola 1 vuelva a ejecutar `runtime-status` del paso 13 y confirme PASS.
7. Vuelva al browser y confirme recuperación normal sin editar source.

## 31. Browser B17 — keyboard/focus/labels/accessibility

1. En la pantalla de Documentos use solo `Tab` y `Shift+Tab` durante varios controles del manual editor, import y review.
2. Confirme foco visible y orden razonable.
3. Confirme que textarea/input importantes tienen label/aria-label y que los mensajes de estado se anuncian mediante región de estado/alert.
4. Compruebe que los botones deshabilitados no se ejecutan con teclado.
5. Capture `17_accessibility.png` con un control enfocado y labels visibles.

## 32. Consola 1 — state/file/Git parity después del browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER" --step state-file-git-parity
```

Debe terminar `PASS` y generar `18_state_file_git_parity.json`, demostrando que el único drift final esperado del fixture es `docs/gsdlc04e_review_candidate.md`, el review está `REVALIDATION_REQUIRED`, approval invalidado, Git diff presente, provenance externo visible y sin auto-revert/hidden merge.

## 33. Consola 1 — cerrar API/UI

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --step runtime-stop
```

Debe terminar `PASS`, `ports_free=true`.

## 34. Completar observaciones manuales

Abra:

`D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E\DEVPL_GSDLC_04_E_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md`

Complete identidad real, las 18 filas, resumen y decisión. Cada fila debe tener `PASS/BLOCK` y una observación no vacía.

En `ZIP de implementación SHA-256` copie exactamente `package_sha256` mostrado por el bootstrap.

Si todos los escenarios anteriores fueron realmente PASS, el resumen debe quedar exactamente:

```text
- `browser_acceptance`: PASS
- `S0_open`: 0
- `S1_open`: 0
- `secrets_exposed`: false
- `network_runtime_used`: false
- `external_api_used`: false
- `pilot_workspace_accessed`: false
- `normal_user_powershell_required`: 0
- `external_operator_project_writes`: 0
- `full_regression_runs_before_browser`: 0
```

Decisión: `PASS-CANDIDATE`.

Justificación sugerida **solo si coincide con lo observado**:

`Authoring MANUAL y PASTE/UPLOAD/IMPORT, autosave/recovery, JSON hints, validation/findings, plan/diff, approval exacto owner, wrong-role deny, stale-preimage deny, atomic apply/freeze, rollback, API-down recovery, accesibilidad y reconciliación de edición externa quedaron demostrados en fixture aislado; el cambio externo movió FROZEN a REVALIDATION_REQUIRED, invalidó approval y mostró Git diff/provenance sin auto-revert/hidden merge; S0/S1=0, normal-user PowerShell=0, operator project writes=0 y full regression todavía=0.`

## 35. Consola 1 — validar evidencia browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --step browser-evidence-validate
```

Debe terminar `PASS` con 18 casos, 0 BLOCK, 0 observaciones vacías, 0 screenshots faltantes, parity PASS y `full_regression_runs_before_browser=0`.

# FULL REGRESSION — EXACTAMENTE UNA VEZ

## 36. Consola 1 — crear marker durable PREPARED

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --step pre-full-marker
```

Debe terminar `PASS`, marker `PREPARED`, `full_regression_runs=0`.

## 37. Consola 1 — ejecutar la única full regression

**ATENCIÓN: EJECUTE EL SIGUIENTE COMANDO UNA SOLA VEZ.**

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --step full-regression-once
```

- Si termina `PASS`, continúe al paso 38.
- Si termina `BLOCK` o reporta tests FAIL/ERROR: **DETÉNGASE. NO REPITA EL COMANDO.** El marker queda consumido (`full_regression_runs=1`) y el log/JUnit se preservan. Devuelva toda la evidencia para root-cause + exact failed-nodeids + bounded impacted retest + Historical Regression Guard. Una segunda full está prohibida.

## 38. Consola 1 — repo-review final

Solo si la full terminó PASS, ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase repo-review
```

Debe terminar `PASS` y no incorporar runtime/browser fixture al repo de producto.

## 39. Consola 1 — commit 04-E

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --phase git-commit --commit-message "feat(gsdlc-04-e): close governed artifact workbench" --execute
```

Debe terminar `PASS`, `worktree_clean=true`. Conserve el commit SHA.

## 40. Consola 1 — generar candidate Windows desde Git HEAD

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --phase package-git-head --execute
```

Debe generar:

`D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\gsdlc_04_e\repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`

y su `.sha256`.

## 41. Consola 1 — sellar evidencia Windows

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0\scripts\devpl_gsdlc_04_e_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_e\DEVPL_GSDLC_04_E_IMPLEMENTATION_PACKAGE_v1_0_0" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --step package-evidence
```

Debe generar:

- `D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\evidence\DEVPL_GSDLC_04_E_WINDOWS_EVIDENCE_v1_0_0.zip`;
- su `.sha256`.

## 42. Evidencia que debe devolver para owner adjudication y cierre de GSDLC-04

Adjunte:

1. captura/log completo de Consola 1 desde bootstrap hasta package-evidence;
2. `DEVPL_GSDLC_04_E_WINDOWS_EVIDENCE_v1_0_0.zip`;
3. su `.sha256`;
4. `repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`;
5. su `.sha256`.

Estado esperado si todo fue PASS:

`GSDLC-04-E = PASS-CANDIDATE / WINDOWS-VALIDATED / FULL-REGRESSION-1-PASS / OWNER-ADJUDICATION-PENDING`

No declare todavía GSDLC-04 ni GSDLC-05 autorizados: la adjudicación owner se realiza después de auditar esos entregables.
