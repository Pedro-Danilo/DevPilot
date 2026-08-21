---
doc_id: "DEVPL-GSDLC-04-B-UNIQUE-WINDOWS-GUIDE"
title: "DEVPL-GSDLC-04-B — Guía única Recovery-010 para cerrar browser acceptance y Windows candidate"
status: "ready-for-windows"
version: "1.0.10"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "pending_windows_execution"
---

# DEVPL-GSDLC-04-B — Guía única v1.0.10

## 0. Punto exacto de reanudación

Esta guía **sustituye por completo** la guía v1.0.9. No use ambas.

La evidencia `DEVPL-GSDLC-04-B-09` demuestra que la ejecución Windows ya llegó hasta el antiguo paso **13. Hash final del fixture**. No repita B1→B9 ni vuelva a modificar el fixture manualmente.

Estado que debe conservarse:

- source 04-B ya aplicado en `D:\Projects\DevPilot_Local`;
- rama `feat/devpl-gsdlc-04-b-manual-editor` todavía sin commit 04-B;
- B3 restart recovery ya ejecutado y captura `03_restart_recovery.png` presente;
- `04_version_history.png`, `05_discard_recover.png`, `06_json_hint.png`, `07_conflict_banner.png` y `08_project_guard.png` presentes;
- las capturas `00`, `01` y `02` previas también se conservan;
- `fixture-restore` v1.0.9 terminó PASS;
- API/UI v1.0.9 continúan levantadas al momento del último BLOCK;
- el único BLOCK actual es el hash final del fixture;
- no existe todavía commit 04-B ni Windows candidate;
- full regression sigue en `0`.

### RCA Recovery-010

El `fixture-restore` ejecutó correctamente `git restore -- docs/manual_authoring.md`. El contenido lógico restaurado es el mismo blob Git baseline, pero Windows materializó el Markdown con finales de línea **CRLF**.

Por eso:

- baseline físico LF: `1f79747c99fcba3f81d43086adacbf1ce20d82c2b0bae25f05d820e933da0038`;
- archivo restaurado físico CRLF: `fe5e3a19387f8afbd27b3468f4caf1d3cffa3b2533d8110b5418fb5d8460317e`;
- contenido canonical-LF: sigue siendo exactamente el blob baseline;
- Git no detecta cambio semántico del source restaurado.

v1.0.9 comparaba SHA-256 de bytes físicos antes/después. Esa comparación no es autoridad válida en un checkout Windows con normalización LF/CRLF.

v1.0.10 usa como autoridad conjunta:

1. blob Git baseline;
2. SHA-256 canonical-LF;
3. `git diff --quiet` y `git diff --cached --quiet` para el path;
4. SHA físico únicamente como diagnóstico.

Una diferencia **solo LF/CRLF** produce PASS. Un cambio real de contenido continúa produciendo BLOCK.

### Regla visual

- última línea verde `PASS`: continúe;
- última línea roja `BLOCK`: deténgase y preserve evidencia.

### Regla de seguridad

No use `git clean`, `git reset --hard`, rebase, force, ni edite manualmente los archivos del fixture para intentar obtener verde.

---

# 1. Descargar y extraer bundle v1.0.10

Descargue el bundle en `C:\Users\Pedro\Downloads` y extráigalo sin cambiar el nombre.

Debe existir exactamente:

`C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_B_CORRECTIVE_READY_FOR_WINDOWS_BUNDLE_v1_0_10`

Use **Consola 1 — CONTROL** para todos los pasos siguientes.

---

# 2. Bootstrap correctivo v1.0.10

En Consola 1 ejecute una sola línea:

```powershell
python "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_B_CORRECTIVE_READY_FOR_WINDOWS_BUNDLE_v1_0_10\DEVPL_GSDLC_04_B_RECOVERY_BOOTSTRAP_v1_0_10.py" --bundle-root "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_B_CORRECTIVE_READY_FOR_WINDOWS_BUNDLE_v1_0_10"
```

Continúe únicamente si la última línea es verde y dice que la integridad 4/4 es consistente.

---

# 3. Cerrar API/UI v1.0.9 que siguen levantadas

No use Ctrl+C en Consola 2 o Consola 3.

Desde Consola 1:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --step runtime-stop
```

PASS exige puertos 8787 y 5173 libres. Después de PASS, Consolas 2 y 3 pueden cerrarse.

---

# 4. Converger únicamente el correctivo Recovery-010

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10" --phase converge-source --branch-name "feat/devpl-gsdlc-04-b-manual-editor" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --execute
```

Este paso no reinicia 04-B. Debe aplicar únicamente los archivos correctivos v1.0.10 que todavía no estén en el repo.

Continúe solo con PASS.

---

# 5. Validación correctiva mínima

No ejecute full regression.

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10" --phase validate-corrective --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B"
```

La validación v1.0.10 se limita a la superficie impactada por Recovery-010: focal 04-B, Source Registry y Documentation Governance.

---

# 6. Repetir SOLO el hash final del fixture

No ejecute `fixture-restore` otra vez. Ya terminó PASS en la ejecución anterior.

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER" --step fixture-hash --label after
```

## Cómo interpretar el resultado

El resultado correcto puede mostrar simultáneamente:

- `all_fixture_sources_restored: true`;
- `eol_only_representation_paths` conteniendo `docs/manual_authoring.md`;
- SHA físico del Markdown diferente al SHA físico inicial;
- `canonical_lf_sha256` igual al `expected_git_blob_sha256`;
- `git_content_equivalent_to_head: true`.

Eso es **PASS**, no una anomalía.

Si aparece un cambio real de contenido, Git diff no equivalente o canonical hash distinto del blob, el harness debe producir BLOCK.

---

# 7. Completar las observaciones manuales — obligatorio

Continúe usando el mismo archivo de la ejecución browser iniciada bajo v1.0.8:

`D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B\DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_v1_0_8.md`

No cree otro archivo.

Abra el archivo con un editor de texto y complete únicamente las columnas **Resultado PASS/BLOCK** y **Observación**, además de la identidad, resumen y decisión final.

Use `PASS` solamente si corresponde exactamente a lo que observó.

Guía para cada fila:

- **Open Existing / PathGuard fixture:** PASS si el Open Existing terminó correctamente y existe `00_project_entry_fixture_open.png`.
- **Editor Markdown carga:** PASS si `docs/manual_authoring.md` abrió en Artifact Workbench; evidencia `01_editor_markdown_loaded.png`.
- **Autosave:** PASS si el draft se guardó automáticamente; evidencia `02_autosave_saved.png`.
- **Recovery tras restart:** PASS si el draft reapareció después del restart sin volver a escribir su contenido; evidencia `03_restart_recovery.png`. Si cerró la pestaña y reconstruyó el contexto UX mediante un nuevo Open Existing, indíquelo en la observación.
- **Version history:** PASS si observó varias revisiones recuperables; evidencia `04_version_history.png`.
- **Discard + recover:** PASS si pudo descartar y recuperar manteniendo historial; evidencia `05_discard_recover.png`.
- **JSON hints:** PASS si `06_json_hint.png` muestra el mensaje `JSON inválido:` durante el JSON temporalmente roto y luego restauró el JSON válido.
- **Conflict/stale preimage:** PASS si `07_conflict_banner.png` muestra el conflicto/BLOCK y el cambio externo no fue sobrescrito.
- **Project route guard:** PASS si `08_project_guard.png` demuestra que una sesión sin journey project-scoped activo fue devuelta a Project Home.
- **Source no cambia al guardar draft:** PASS si `12_markdown_source_hash_during_draft.json` indica `markdown_source_unchanged=true`.
- **Sesión/RBAC:** escriba PASS únicamente si comprobó que al cerrar sesión `/workspace/documents` exige Login y el editor/save/history no quedan disponibles. La captura `09_session_rbac.png` sigue siendo opcional; la observación es obligatoria.

## Resumen final

Solo si todas las filas anteriores son PASS, complete exactamente:

- `browser_acceptance`: `PASS`
- `S0_open`: `0`
- `S1_open`: `0`
- `secrets_exposed`: `false`
- `network_runtime_used`: `false`
- `external_api_used`: `false`
- `pilot_workspace_accessed`: `false`

En **Decisión** escriba `PASS-CANDIDATE` únicamente si todo lo anterior es verdadero.

---

# 8. Validar evidencia browser

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --step browser-evidence-validate
```

Continúe únicamente con PASS verde.

---

# 9. Repo-review final

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10" --phase repo-review --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B"
```

Continúe únicamente con PASS.

---

# 10. Commit controlado

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --step git-commit --commit-message "feat(gsdlc-04-b): add governed manual artifact authoring"
```

No haga push.

---

# 11. Generar Windows candidate

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10" --phase package-git-head --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --execute
```

Debe producir:

`D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\gsdlc_04_b\repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip`

y su `.sha256`.

---

# 12. Empaquetar evidencia Windows

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_b\DEVPL_GSDLC_04_B_IMPLEMENTATION_PACKAGE_v1_0_10\scripts\devpl_gsdlc_04_b_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --step package-evidence
```

Debe producir:

`DEVPL_GSDLC_04_B_WINDOWS_EVIDENCE_v1_0_10.zip`

y su `.sha256`.

---

# 13. Entregables a devolver para adjudicación owner

Devuelva conjuntamente:

1. log final de Consola 1;
2. `DEVPL_GSDLC_04_B_WINDOWS_EVIDENCE_v1_0_10.zip` + `.sha256`;
3. `repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip` + `.sha256`;
4. `DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_v1_0_8.md` completado;
5. capturas `00`→`08` y opcional `09_session_rbac.png`.

No autorice GSDLC-04-C. La autorización corresponde a la adjudicación owner posterior.

## PASS-CANDIDATE

Solo existe si el hash final v1.0.10 termina PASS con autoridad Git/canonical-LF, la evidencia browser valida, runtime queda cerrado, repo-review pasa, commit/candidate/evidence ZIP se generan, S0/S1=0 y full regression permanece en 0.
