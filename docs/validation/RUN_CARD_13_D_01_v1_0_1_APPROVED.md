---
doc_id: "DEVPL-GSDLC-13-D-01-RUN-CARD"
title: "Run Card 13-D-01 — First Story activation/context + implementation route"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-30"
approval: "approved_by_owner_for_13_d_01"
checkpoint_id: "13-D-01"
authority_record: ".devpilot/gsdlc/gsdlc13_d_preflight_authority.json"
lineage_record: ".devpilot/gsdlc/gsdlc13_pilot_a_deterministic_lineage.json"
full_regression_runs_allowed: 0
operator_project_writes_allowed: false
background_processes_allowed: false
---

# Run Card `13-D-01`

## 1. Objetivo

Demostrar, en el **primer intento real del Owner**, que DevPilot puede pasar desde Planning ya
FROZEN/`IMPLEMENTING_READY` a una `StoryExecution` activa y comprensible, sin ayuda externa que escriba,
prepare o preconfigure el proyecto greenfield.

El checkpoint termina **antes** de construir o ejecutar el Change Plan de `13-D-02`.

## 2. Reglas operativas obligatorias

Estas reglas aplican durante todo el checkpoint:

- trabajar con **tres consolas foreground**: auditoría, API y UI;
- no background jobs;
- no cuarta consola para "arreglar" el proyecto;
- `operator_project_writes=0`;
- `normal_user_terminal_escapes=0`;
- no editar el workspace greenfield desde PowerShell, VS Code u otro editor externo;
- no llamar endpoints manualmente para crear `StoryExecution`;
- no sembrar JSON/runtime state;
- no ejecutar Full Regression;
- no Git destructivo (`reset --hard`, force, auto-rebase);
- no comparar CRLF/LF como criterio funcional;
- Manual sigue siendo first-class;
- E1/E2/E3 no se adoptan en Pilot A;
- el first-attempt se preserva: si aparece un BLOCK, no reiniciar ni probar atajos antes de capturarlo.

## 3. Autoridad

Baseline funcional inmutable de Pilot A:

```text
repo: repo451_C04_BR_108_WINDOWS_VALIDATED_CANDIDATE.zip
commit: bb06260ce94298bf1e9dbb798e057d7ad07ea459
lineage: DETERMINISTIC/PRE-MULTIPROVIDER
workspace: D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield
```

El HEAD real de DevPilot debe ser:

- el baseline anterior; o
- un descendiente que contenga **únicamente** el overlay PRE-13D aprobado.

Si hay cualquier delta runtime/API/UI fuera del allowlist PRE, registra `BLOCK/AUTHORITY-MISMATCH`.

## 4. Preparación de las tres consolas

### Consola 1 — Auditoría

Abre PowerShell y ejecuta:

```powershell
Set-Location "D:\Projects\DevPilot_Local"
```

Activa el entorno Python estándar de DevPilot:

```powershell
. .\.venv\Scripts\Activate.ps1
```

Audita la autoridad sin modificar nada:

```powershell
$Base="bb06260ce94298bf1e9dbb798e057d7ad07ea459"; try { git merge-base --is-ancestor $Base HEAD; if($LASTEXITCODE-ne0){throw "el baseline no es ancestro del HEAD"}; $Dirty=@(git status --porcelain); if($Dirty.Count-ne0){throw "worktree DevPilot no está limpio"}; Write-Host "HEAD actual:" (git rev-parse HEAD); Write-Host "Delta PRE desde baseline:"; git diff --name-only "$Base..HEAD"; Write-Host "PASS: autoridad Git lista para 13-D-01" -ForegroundColor Green } catch { Write-Host "BLOCK: autoridad Git inválida — $($_.Exception.Message)" -ForegroundColor Red; throw }
```

Audita la gobernanza con el CLI estándar de DevPilot:

```powershell
try { python -m devpilot_core docs-governance validate --json; if($LASTEXITCODE-ne0){throw "docs-governance validate falló"}; Write-Host "PASS: gobernanza documental válida" -ForegroundColor Green } catch { Write-Host "BLOCK: gobernanza documental inválida — $($_.Exception.Message)" -ForegroundColor Red; throw }
```

**Después de estas verificaciones deja esta consola abierta.** Úsala solamente para auditoría/captura durante D01.

### Consola 2 — API

Abre una segunda PowerShell:

```powershell
Set-Location "D:\Projects\DevPilot_Local"
. .\.venv\Scripts\Activate.ps1
```

Primero ejecuta el dry-run estándar:

```powershell
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json
```

Si el dry-run devuelve error, **no levantes la API**; registra BLOCK.

Genera el token con el comando estándar:

```powershell
python -m devpilot_core api token --json
```

El comando devuelve un campo `powershell`. **Copia y ejecuta exactamente ese comando en esta misma Consola 2.**
No escribas el token en capturas, documentos, Run Packet ni chat.

Luego levanta la API foreground:

```powershell
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute
```

Esta consola debe quedar ocupada por la API durante el checkpoint.

### Consola 3 — UI

Abre una tercera PowerShell:

```powershell
Set-Location "D:\Projects\DevPilot_Local\ui\web"
```

Levanta el frontend con el comando estándar:

```powershell
npm run dev
```

Esta consola debe quedar ocupada por Vite durante el checkpoint.

Abre en el navegador:

```text
http://127.0.0.1:5173
```

Si la UI solicita el token local, pega el **mismo token** generado en Consola 2.
No lo captures ni lo incluyas en evidencia.

## 5. Start state que debes confirmar en la UI

Antes de iniciar la Story confirma:

- proyecto activo = `inventory-sales-local-greenfield`;
- Project Status no está en `EMPTY`/`UNKNOWN`;
- Roadmap, Backlog y Sprint están FROZEN;
- Planning está `IMPLEMENTING_READY` o muestra un equivalente inequívoco;
- existe al menos una Story READY del Sprint;
- no has creado manualmente `StoryExecution`, `StoryContextPack` ni archivos del proyecto.

Si no puedes confirmar alguno de estos puntos mediante el producto normal, captura el estado y detente.

## 6. Misión de usuario normal

### A. Llegar a Story Code

Desde **Project Status**, utiliza la acción principal que DevPilot ofrece para continuar.

No escribas rutas internas a mano para saltarte la navegación normal.

Esperado: llegar a **Story Code Workbench** o una superficie inequívocamente equivalente.

### B. Activar la primera Story READY

Observa el **primer estado real** que presenta DevPilot al entrar.

Si DevPilot:

- identifica una Story READY y ofrece preparar/iniciar/continuar → usa esa acción;
- muestra un selector normal de Stories READY → selecciona la siguiente válida que el producto presente.

No inventes Story IDs.

DevPilot debe ser capaz de conducir por su propia ruta a:

1. evaluación DoR;
2. `StoryContextPack`;
3. `StoryExecution` `PLANNED`;
4. transición normal a `IN_PROGRESS`.

### C. Revisar el contexto

Antes de elegir cómo implementar, comprueba que puedes entender suficientemente:

- Story;
- objetivo;
- acceptance criteria;
- requirements relacionados;
- architecture/constraints;
- test intent o pruebas esperadas;
- provenance/context hash o referencias de autoridad.

No es necesario que todo esté en una sola tarjeta, pero debe poder inspeccionarse mediante la UI/producto,
sin terminal ni lectura directa de archivos internos.

### D. Revisar la ruta de implementación

Para Pilot A:

- Manual debe seguir disponible y ser first-class;
- Agent-assisted mock/fake-local es opcional;
- Ollama/LM Studio reales no son requisito;
- external API no es requisito;
- si aparece provider/model, registra únicamente identificadores no sensibles y su route/provenance;
- elegir modelo nunca debe conceder automáticamente autoridad de tools/source/apply/approval.

**No ejecutes todavía Change Plan.**

## 7. Prohibido

- project writes desde Consola 1;
- endpoints manuales de story/runtime;
- scripts temporales para crear/forzar estado;
- editar JSON bajo `.devpilot`/`outputs`;
- modificar Git del workspace Pilot A;
- ejecutar tests del proyecto en D01;
- ejecutar Full Regression;
- instalar/adoptar E1/E2/E3;
- usar provider real solo para fabricar PASS;
- ocultar el first-attempt fallido.

## 8. BLOCK inmediato

Detente y conserva evidencia si ocurre cualquiera:

1. `no active story` y no existe una acción normal para activar una Story READY;
2. hace falta terminal/API/operator para preparar o iniciar la Story;
3. Planning está READY/FROZEN pero DevPilot no identifica una Story ejecutable;
4. Project Context cae a `EMPTY`/`UNKNOWN`;
5. Owner debe decidir sin contexto/provenance suficiente;
6. model route concede tool/source/apply/approval authority;
7. aparece un S0/S1 reproducible;
8. autoridad DevPilot no coincide con PRE-13D.

No corrijas el producto en esta Run Card.

## 9. Stop point de PASS

Detente cuando tengas simultáneamente:

- Story identificada;
- DoR PASS/READY;
- `StoryContextPack` materializado/provenanced;
- `StoryExecution` `IN_PROGRESS`;
- contexto suficientemente revisable;
- ruta de implementación comprendida/seleccionada;
- **Change Plan D02 todavía no ejecutado**.

## 10. Evidencia que debes entregar

Un único Run Packet incremental:

1. Project Status inicial;
2. Planning/Sprint FROZEN/READY si no queda visible en Project Status;
3. primer estado al entrar a Story Code;
4. selector/acción de activación, si existe;
5. Story activa (`PLANNED` o `IN_PROGRESS`);
6. contexto Story/AC/requirements/architecture/tests;
7. ruta Manual/Agent-assisted y provider/model si aplica;
8. Consola 1 con auditoría de HEAD/start-state, **sin tokens**;
9. receipts/exports que DevPilot produzca para DoR/context/story execution;
10. observaciones:
   - `first_attempt`: PASS/BLOCK;
   - `operator_project_writes`: 0;
   - `normal_user_terminal_escapes`: 0;
   - momentos de confusión;
   - confianza Owner 1–5.

No captures cada clic: captura estados decisivos.

## 11. Resultado

- `PASS` / `PASS+FINDING` → adjudicar y preparar `13-D-02`;
- `BLOCK` → preservar evidencia y volver a ChatGPT para corrective bounded exacto.
