---
doc_id: "DEVPL-GSDLC-04-C-UNIQUE-WINDOWS-GUIDE"
title: "DEVPL-GSDLC-04-C — Guía única de implementación, validación y evidencia Windows"
status: "ready-for-windows"
version: "1.0.3"
owner: "Ordóñez"
updated: "2026-08-21"
approval: "pending_windows_execution"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-C"
predecessor_repo: "repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip"
predecessor_commit: "b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f"
predecessor_sha256: "3cfe97a376ee269b6c6fb3465e9549c2eea1e2160ecf5ff4848fd351a776ad92"
full_regression_allowed: false
three_console_runtime_required: true
---

# DEVPL-GSDLC-04-C — Guía única Windows

Esta es la **única instrucción operativa autoritativa** para instalar, validar y producir evidencia de `GSDLC-04-C — Paste, upload and external-source import`.

## 0. Reglas de ejecución

1. El bundle se descarga y extrae exactamente en `C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_C_READY_FOR_WINDOWS_BUNDLE_v1_0_3`.
2. Use **tres PowerShell separadas** durante browser acceptance:
   - Consola 1 — CONTROL: comandos generales, validación, hashes, cierre y empaquetado.
   - Consola 2 — API: solo API; permanecerá ocupada mientras API esté activa.
   - Consola 3 — UI: solo Vite; permanecerá ocupada mientras UI esté activa.
3. No use `reset --hard`, `git clean`, rebase, force push ni comandos Git genéricos para “arreglar” un BLOCK.
4. No acceda a `D:\Projects\DevPilot_Workspaces\inventory-sales-local`.
5. No ejecute full regression. GSDLC-04-C debe terminar con `full regression = 0`; la única full del backlog está reservada para 04-E.
6. **Cada comando Python termina con una última línea verde `PASS` o roja `BLOCK`.** Si la última línea es `BLOCK`, deténgase. No ejecute el paso siguiente.
7. Las diferencias físicas LF/CRLF no son autoridad de fallo. El preflight usa SHA físico primero y, solo para paths Git-clean, exige equivalencia canonical-LF simultánea del working tree y del blob inmutable del predecessor. Un cambio real sigue bloqueando.
8. No borre ni sobrescriba evidencia ya generada. Los scripts crean checkpoints adicionales cuando corresponde.

---

# 1. Consola 1 — instalar/verificar el corrective v1.0.3

Abra una PowerShell nueva. Será **Consola 1 — CONTROL** durante toda la ejecución.

Ejecute exactamente:

```powershell
python "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_C_READY_FOR_WINDOWS_BUNDLE_v1_0_3\DEVPL_GSDLC_04_C_BOOTSTRAP_v1_0_3.py" --bundle-root "C:\Users\Pedro\Downloads\DEVPL_GSDLC_04_C_READY_FOR_WINDOWS_BUNDLE_v1_0_3"
```

Debe terminar en una línea verde `PASS`. Este bootstrap valida integridad 4/4 y materializa el package v1.0.3; **no modifica source ni Git**.

## 1.1 Estado exacto que se recupera

Esta guía continúa desde la ejecución v1.0.2 que llegó a `validate` y bloqueó únicamente en `ui-static-04c` con una ruta `D:\D:\Projects\...`. No haga rollback, `reset`, `git clean`, rebase ni reaplique 04-C desde cero. La evidencia ya demostró:

- `recovery-preflight-002 = PASS`;
- `converge-source v1.0.2 = PASS`;
- `repo-review = PASS`;
- `provision-check = PASS`;
- focal, acumulativo, Test Impact, Project State, TCR, schemas, Documentation Governance, API contract/security y UI route enforcement = PASS en esa misma corrida;
- el primer fallo fue el smoke UI por conversión incorrecta `file:// -> Windows path`;
- full regression = `0`.

Recovery-003 corrige **la clase completa** del defecto: escanea todos los scripts `ui/web/scripts` para impedir `new URL(import.meta.url).pathname` y exige `fileURLToPath(import.meta.url)` o uso directo seguro de `URL`.

# 2. Consola 1 — recovery-preflight-003 read-only

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --phase recovery-preflight-003 --branch-name "feat/devpl-gsdlc-04-c-artifact-import"
```

Debe terminar `PASS`. El checkpoint exige HEAD predecessor `b095bf5b...`, rama 04-C, `repo-review` v1.0.2 PASS, el BLOCK `D:\D:\...` exacto y cero paths dirty fuera del delta 04-C conocido. **No escribe source.**

# 3. Consola 1 — converger solamente Recovery-003

Ejecute una sola vez:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --phase converge-source --branch-name "feat/devpl-gsdlc-04-c-artifact-import" --execute
```

Resultado esperado: `PASS`, `pending=[]`, `conflicts=[]`. El operador sustituye solo los postimages superseded reconocidos y elimina exclusivamente la guía v1.0.2 reemplazada.

# 4. Consola 1 — repo-review correctivo

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --phase repo-review
```

Debe terminar `PASS`, con `diff_check=PASS`, cero paths inesperados y cero runtime/cache tracked.

# 5. Consola 1 — provision-check

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --step provision-check
```

Debe confirmar `.venv`, `npm` y `ui/web/node_modules`; no instala nada y no usa red.

# 6. Consola 1 — validación correctiva y forward-scan

No repita 20/77/47 ni los gates backend que ya quedaron PASS antes del fallo. Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --phase validate-corrective-003
```

Este gate ejecuta únicamente:

1. `windows-path-portability-audit` sobre **todos** los `.mjs/.js` de `ui/web/scripts`;
2. Source Registry + Documentation Contract Reconciliation Policy;
3. Documentation Governance;
4. `ui-static-04c`;
5. Vite build.

Debe terminar `PASS`. Si cualquiera bloquea, deténgase y preserve evidencia. Full regression permanece en `0`.

# 7. Consola 1 — preparar fixture e inputs browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER" --browser-input-root "D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs" --step prepare-browser
```

El harness crea/reutiliza solamente:

- fixture Git: `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER`;
- inputs externos controlados: `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs`;
- observaciones: `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C\DEVPL_GSDLC_04_C_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md`.

No toca el workspace piloto.

---

# 8. Consola 1 — browser-preflight

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER" --browser-input-root "D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs" --step browser-preflight
```

Debe comprobar antes de abrir UI: puertos libres, fixture Git clean, source hash baseline, PathGuard, dry-run Project Entry y binding del workspace exacto. Si falla, no levante API/UI.

---

# 9. Abrir Consola 2 — API

Abra **otra PowerShell**. Esta será exclusivamente Consola 2.

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_runtime_console.py" --role api --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER"
```

Espere la última línea verde `PASS — API lista ...`. **Deje esta consola abierta.** Los requests HTTP se guardan en `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C\runtime\api_console.log`; la consola queda silenciosa por diseño.

---

# 10. Abrir Consola 3 — UI

Abra una tercera PowerShell.

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_runtime_console.py" --role ui --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER"
```

Espere `PASS — UI lista ...` y deje Consola 3 abierta.

---

# 11. Consola 1 — confirmar readiness conjunto

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER" --step runtime-status
```

Debe terminar `PASS` con API+UI READY y binding exacto al fixture 04-C.

---

# 12. Browser — abrir el fixture por el journey normal

1. Abra `http://127.0.0.1:5173/`.
2. Inicie sesión con las credenciales locales habituales de `owner.local`.
3. En **Project Home**, pulse **Open existing project**.
4. En la pantalla **Crear / Abrir / Importar**, configure exactamente:
   - **Modo de entrada:** `Abrir existente`.
   - **Project ID:** `gsdlc04c-browser`.
   - **Nombre:** `GSDLC 04-C browser fixture`.
   - **Ruta destino / workspace:** `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER`.
5. Pulse **Generar dry-run** una sola vez.
6. Compruebe que aparece PASS y que la UI muestra `OPEN_EXISTING`, `Writes ejecutados=false` y `Network usada=false`.
7. Pulse **Revalidar preimage** y espere PASS.
8. En **Motivo de aprobación**, escriba: `Abrir fixture GSDLC 04-C para browser acceptance.`
9. Pulse **Solicitar approval** y anote el Approval ID mostrado.
10. Pulse el enlace **Abrir Approval Center ↗**. Apruebe exactamente ese Approval ID.
11. Vuelva a la pestaña de Project Entry.
12. Pulse **Verificar approval** y espere PASS.
13. Pulse **Ejecutar plan aprobado** una sola vez.
14. Debe aparecer `PASS: bootstrap approval-bound completado y verificado.` y la tarjeta **Workspace listo**.
15. Pulse **Continuar a Estado del proyecto →** y después **Documentos**.
16. Debe llegar a `http://127.0.0.1:5173/workspace/documents` y ver `Artifact Workbench · importar fuente externa`.
17. Guarde la captura `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C\browser\00_project_entry_fixture_open.png`.

### Cómo guardar cada captura

Use el mismo procedimiento para todas las capturas de esta guía: presione `Win+Shift+S`, capture el área de DevPilot que muestra el criterio, abra la notificación de Recortes, pulse `Ctrl+S` y guarde el PNG con **el nombre exacto** indicado bajo `D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C\browser`. Antes de guardar, revise la imagen completa y confirme que no contiene passwords, cookies, tokens, API keys ni secretos.

---

# 13. C1 — PASTE preview

En `Artifact Workbench · importar fuente externa`:

1. En **Origen**, seleccione `Pegar texto`.
2. En **Destino relativo (.md/.json)** escriba `docs/paste_candidate.md`.
3. En **Source label (opcional)** escriba `Browser PASTE`.
4. En **URL / reference (metadata, no fetch)** escriba `https://example.invalid/reference-only`.
5. En **Contenido pegado** escriba dos líneas simples, por ejemplo un título Markdown y `Browser paste acceptance.`. No incluya secretos.
6. Pulse **Generar preview**.
7. Debe verse `Preview PASS · sin writes · sin network`.
8. En `Preview / diff antes de persistir` confirme:
   - Origen `PASTE`;
   - SHA original presente;
   - SHA normalizado presente;
   - Preview SHA presente;
   - `Secret warning=false`;
   - preview y diff visibles.
9. Guarde `01_paste_preview.png`.

Si la UI no muestra preview/hashes o muestra un BLOCK inesperado, registre BLOCK y deténgase.

---

# 14. C2 — PASTE DRAFT + provenance

Sin cambiar los campos del caso anterior:

1. Pulse **Crear DRAFT** una sola vez.
2. Debe aparecer `PASS · importación persistida como DRAFT runtime; source/workspace sin writes.`.
3. En **Artifact provenance · DRAFT** confirme:
   - Estado `DRAFT`;
   - Origen `PASTE`;
   - Source label `Browser PASTE`;
   - Source reference visible;
   - SHA original y SHA normalizado;
   - `Workspace writes=false`;
   - `Network=false`.
4. Guarde `02_paste_draft_provenance.png`.

El DRAFT no debe crear `docs/paste_candidate.md` dentro del fixture.

---

# 15. C3 — UPLOAD Markdown

1. Cambie **Origen** a `Upload local`.
2. En destino escriba `docs/upload_candidate.md`.
3. Source label: `Browser upload Markdown`.
4. En **Archivo local**, seleccione exactamente `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs\upload_source.md`.
5. Espere el mensaje `Archivo cargado solo en memoria del navegador...`.
6. Pulse **Generar preview**.
7. Compruebe preview PASS, hashes y diff.
8. Pulse **Crear DRAFT**.
9. Compruebe `Artifact provenance · DRAFT`, Origen `UPLOAD`, `Workspace writes=false`, `Network=false`.
10. Guarde `03_upload_draft_provenance.png`.

No abra ni modifique el archivo input manualmente.

---

# 16. C4 — IMPORT JSON con encoding normalizado

1. Cambie **Origen** a `Importar archivo externo`.
2. En destino escriba `docs/import_candidate.json`.
3. Source label: `Browser import JSON`.
4. En **Archivo de fuente externa**, seleccione exactamente `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs\import_source.json`.
5. Pulse **Generar preview**.
6. En preview confirme:
   - Origen `IMPORT`;
   - destino `.json`;
   - Encoding `utf-16-le-bom`;
   - SHA original presente;
   - SHA normalizado presente;
   - ambos hashes son distintos, porque el original contiene BOM/UTF-16 y el normalizado es UTF-8/LF;
   - `Secret warning=false`.
7. Pulse **Crear DRAFT**.
8. Confirme `Artifact provenance · DRAFT`, hashes, `Workspace writes=false` y `Network=false`.
9. Guarde `04_import_json_provenance.png` procurando que hashes y provenance queden visibles.

Esta captura también prueba la fila `Original/normalized hashes + provenance`.

---

# 17. C5 — warning/redaction de secreto sintético

Este caso usa un archivo sintético generado por el harness. **No contiene ninguna credencial real.**

1. Seleccione `Importar archivo externo`.
2. Destino: `docs/secret_warning_candidate.md`.
3. Seleccione `D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs\secret_warning_source.md`.
4. Pulse **Generar preview**.
5. Debe aparecer un WARNING indicando secreto detectado y que persistir DRAFT está bloqueado.
6. En preview confirme `Secret warning=true` y que el valor sensible está reemplazado por contenido redactado (`REDACTED` o equivalente). **El valor original no debe verse.**
7. El botón **Crear DRAFT** debe estar deshabilitado.
8. No intente persistir ese input.
9. Revise muy cuidadosamente la pantalla y guarde `05_secret_warning_redacted.png` solo si no aparece el valor original.

Si el valor original es visible en pantalla, es `BLOCK/S0`: no conserve la captura y detenga la ejecución.

---

# 18. C6 — Project route guard

No cierre la pestaña principal todavía.

1. Abra **una pestaña nueva** del navegador.
2. En esa pestaña nueva escriba `http://127.0.0.1:5173/workspace/documents`.
3. Como `sessionStorage` project-scoped no se comparte con una pestaña nueva, DevPilot debe impedir entrar directamente al workbench y devolverlo a Project Home/flujo de proyecto.
4. Guarde `06_project_guard.png` mostrando claramente que la ruta project-scoped no quedó accesible sin journey activo en esa pestaña.
5. Cierre únicamente esa pestaña nueva y vuelva a la pestaña principal.

---

# 19. C7 — Sesión/RBAC

1. En la pestaña principal pulse **Cerrar sesión**.
2. Navegue a `http://127.0.0.1:5173/workspace/documents`.
3. Debe aparecer Login; el Artifact Workbench y sus botones preview/DRAFT no deben estar disponibles.
4. Esta observación es obligatoria. La captura `07_session_rbac.png` es opcional. Si decide tomarla, guárdela en el directorio browser y no incluya credenciales.

Después de este punto ya no necesita iniciar sesión nuevamente.

---

# 20. Consola 1 — comprobar que el workspace/source no cambió

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --browser-fixture-root "D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER" --step source-hash --label after
```

El resultado debe ser `PASS`, `all_workspace_sources_unchanged=true` y autoridad `git-blob+canonical-lf`. Diferencias físicas LF/CRLF por sí solas no bloquean.

---

# 21. Consola 1 — cerrar API y UI

Aunque Ctrl+C no responda en Consola 2 o 3, no interactúe con ellas. Desde Consola 1 ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --step runtime-stop
```

Debe terminar `PASS` y `ports_free=true`. Solo termina los árboles de procesos registrados por los launchers 04-C; nunca mata `python.exe` o `node.exe` por nombre.

---

# 22. Completar observaciones manuales

Abra con un editor de texto:

`D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C\DEVPL_GSDLC_04_C_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md`

Complete:

- Fecha/hora real de la aceptación.
- Operador.
- Browser/versión real.
- En cada fila, `PASS` o `BLOCK` y una frase breve de lo observado.
- `ZIP de implementación SHA-256`: copie exactamente `package_sha256` del primer bootstrap.

Si todos los casos anteriores fueron PASS, el bloque `BEGIN_BROWSER_SUMMARY` debe quedar exactamente:

```text
- `browser_acceptance`: PASS
- `S0_open`: 0
- `S1_open`: 0
- `secrets_exposed`: false
- `network_runtime_used`: false
- `external_api_used`: false
- `pilot_workspace_accessed`: false
```

En **Decisión** escriba `PASS-CANDIDATE`, no `PASS`, porque todavía faltan commit/candidate/evidence package y owner adjudication.

Ejemplo de justificación final si todos los casos fueron PASS: `PASTE, UPLOAD e IMPORT quedaron demostrados como preview-first y DRAFT; provenance/hashes visibles, secret warning redactado, source/workspace sin cambios, project/session guards PASS, S0/S1=0.`

---

# 23. Consola 1 — validar evidencia browser

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --step browser-evidence-validate
```

Debe devolver `PASS`, sin casos faltantes, sin filas BLOCK y sin screenshots obligatorios faltantes.

---

# 24. Consola 1 — repo-review final

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --phase repo-review
```

Debe terminar PASS y no listar dirty paths fuera del source delta 04-C.

---

# 25. Consola 1 — commit 04-C

El operador stagea únicamente los paths dirty autorizados por el manifest. Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --phase git-commit --commit-message "feat(gsdlc-04-c): add governed paste and artifact import" --execute
```

Debe terminar PASS y `worktree_clean=true`. Conserve el commit SHA mostrado.

---

# 26. Consola 1 — generar candidate Windows desde Git HEAD

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_operator.py" --repo-root "D:\Projects\DevPilot_Local" --package-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --phase package-git-head --execute
```

El resultado esperado es:

`D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\gsdlc_04_c\repo_DevPilot_Local_367_DEVPL_GSDLC_04_C_EXTERNAL_SOURCE_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip`

más su `.sha256`. El ZIP se genera con `git archive` y excluye naturalmente `.git`, `.venv`, node_modules, outputs y runtime DBs no trackeados.

---

# 27. Consola 1 — sellar evidencia Windows

Ejecute:

```powershell
python "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\integration\gsdlc_04_c\DEVPL_GSDLC_04_C_IMPLEMENTATION_PACKAGE_v1_0_3\scripts\devpl_gsdlc_04_c_windows_harness.py" --repo-root "D:\Projects\DevPilot_Local" --evidence-dir "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C" --artifacts-root "D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002" --step package-evidence
```

Debe generar:

- `D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\evidence\DEVPL_GSDLC_04_C_WINDOWS_EVIDENCE_v1_0_0.zip`;
- su `.sha256`.

El harness ejecuta un redaction scan antes de sellar. Si detecta un patrón de secreto, BLOCK y preserve evidencia; no intente ocultarlo borrando logs.

---

# 28. Evidencia que debe devolver para owner adjudication

Adjunte en el siguiente prompt:

1. captura manual completa de Consola 1 de esta ejecución;
2. `DEVPL_GSDLC_04_C_WINDOWS_EVIDENCE_v1_0_0.zip`;
3. `DEVPL_GSDLC_04_C_WINDOWS_EVIDENCE_v1_0_0.zip.sha256`;
4. `repo_DevPilot_Local_367_DEVPL_GSDLC_04_C_EXTERNAL_SOURCE_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip`;
5. su `.sha256`.

No necesita adjuntar `.venv`, `node_modules`, `outputs`, runtime DBs ni el fixture completo por separado: la evidencia sellada ya contiene los checkpoints/hashes y screenshots necesarios.

---

# 29. Resultado esperado

Si todos los pasos terminan PASS, el estado correcto es:

`GSDLC-04-C = PASS-CANDIDATE / WINDOWS-VALIDATED / OWNER-ADJUDICATION-PENDING`

No declare todavía `CLOSED/PASS`. GSDLC-04-D permanece bloqueado hasta que el owner adjudique la evidencia y el candidate 04-C.
