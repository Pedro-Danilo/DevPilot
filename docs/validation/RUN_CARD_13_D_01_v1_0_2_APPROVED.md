---
doc_id: "DEVPL-GSDLC-13-D-01-RUN-CARD"
title: "Run Card 13-D-01 — First Story activation/context + implementation route"
status: "approved"
version: "1.0.2"
owner: "Ordóñez"
updated: "2026-09-30"
approval: "approved_by_owner_for_13_d_01"
checkpoint_id: "13-D-01"
predecessor: "RUN_CARD_13_D_01_v1_0_1_APPROVED.md"
pre_baseline_commit: "da301c29118b81cbb2896925178c58ef983bcda7"
full_regression_runs_allowed: 0
operator_project_writes_allowed: false
background_processes_allowed: false
---

# Run Card `13-D-01` — v1.0.2

## 1. Objetivo

Validar mediante **first-attempt browser real** que DevPilot puede conducir desde Planning
`FROZEN / IMPLEMENTING_READY` hasta una Story activa y un contexto suficientemente revisable,
sin que el operador escriba el proyecto ni cree runtime state manualmente.

El checkpoint termina antes del Change Plan de `13-D-02`.

## 2. Corrección operativa respecto de v1.0.1

La v1.0.1 dependía de que cada nueva PowerShell conservara correctamente la activación de `.venv`.
La v1.0.2 elimina esa fragilidad.

**Todas las operaciones Python de D01 usan explícitamente:**

```text
D:\Projects\DevPilot_Local\.venv\Scripts\python.exe
```

No se usa `python` ambiguo del `PATH`.

D01 **no instala dependencias**. Si el `.venv` canónico no puede importar `fastapi`/`uvicorn`,
se clasifica `BLOCK/ENVIRONMENT-DEPENDENCY-DRIFT` y se detiene.

## 3. Evidencia obligatoria

Raíz única:

```text
D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01
```

Debe contener al finalizar:

```text
audit_13_D_01.txt
api_13_D_01.txt
ui_13_D_01.txt
START_STATE_13_D_01.json
MANUAL_OBSERVATIONS_13_D_01.md
screenshots\
```

Capturas browser obligatorias de PASS:

```text
01_project_status_initial.png
02_planning_frozen_implementing_ready.png
03_story_code_first_attempt.png
04_story_ready_activation_action.png
05_story_execution_planned_or_in_progress.png
06_story_context_reviewability.png
07_implementation_route_provenance.png
08_stop_before_change_plan.png
```

Si el checkpoint bloquea antes, guarda todas las capturas alcanzadas y además:

```text
99_block_state.png
```

No se exige fabricar las capturas posteriores al punto de BLOCK.

## 4. Reglas

- exactamente tres consolas foreground: Auditoría, API, UI;
- no background;
- `operator_project_writes=0`;
- `normal_user_terminal_escapes=0`;
- no editar Pilot A desde terminal/editor externo;
- no endpoint manual para crear StoryExecution;
- no JSON/runtime seed;
- no Full Regression;
- no E1/E2/E3;
- no Git destructivo;
- no instalar paquetes durante D01;
- preservar first-attempt;
- capturas browser son evidencia central, no opcional.

---

# 5. Consola 1 — Auditoría y evidencia

Abre PowerShell.

Ejecuta este bloque una sola vez:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01"; $S=Join-Path $E "screenshots"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { New-Item -ItemType Directory -Force -Path $E,$S | Out-Null; Start-Transcript -Path (Join-Path $E "audit_13_D_01.txt") -Force; if(!(Test-Path -LiteralPath $Py)){throw "no existe $Py"}; $Head=(git -C $R rev-parse HEAD).Trim(); $Dirty=@(git -C $R status --porcelain); if($LASTEXITCODE-ne0){throw "Git no disponible"}; if($Dirty.Count-ne0){throw "DevPilot worktree no está limpio"}; & $Py -c "import sys; print(sys.executable)"; if($LASTEXITCODE-ne0){throw "Python .venv no ejecuta"}; $State=[ordered]@{checkpoint="13-D-01";captured_at=(Get-Date).ToString("o");devpilot_head=$Head;repo_clean=$true;workspace="D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield";operator_project_writes=0;normal_user_terminal_escapes=0;full_regression_runs=0}; $State | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $E "START_STATE_13_D_01.json") -Encoding UTF8; @"
# MANUAL OBSERVATIONS — 13-D-01

- first_attempt: PENDING
- checkpoint_result: PENDING
- active_project:
- initial_project_status:
- planning_state:
- first_story_code_state:
- selected_story:
- dor_result:
- story_execution_state:
- context_reviewability:
- implementation_route:
- provider_model_if_any:
- provenance_visible:
- operator_project_writes: 0
- normal_user_terminal_escapes: 0
- full_regression_runs: 0
- moments_of_confusion:
- ux_findings:
- owner_confidence_1_to_5:
- block_reason_if_any:
- notes:
"@ | Set-Content -LiteralPath (Join-Path $E "MANUAL_OBSERVATIONS_13_D_01.md") -Encoding UTF8; Copy-Item -LiteralPath (Join-Path $R ".devpilot\gsdlc\gsdlc13_d_preflight_authority.json") -Destination (Join-Path $E "authority_start.json") -Force; Copy-Item -LiteralPath (Join-Path $R ".devpilot\gsdlc\gsdlc13_pilot_a_deterministic_lineage.json") -Destination (Join-Path $E "pilot_a_lineage_start.json") -Force; Write-Host "PASS — D01 audit/evidence inicializada; HEAD=$Head" -ForegroundColor Green } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — D01 audit init: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Mantén esta consola abierta. No la uses para escribir Pilot A.

---

# 6. Consola 2 — API

Abre una segunda PowerShell.

Ejecuta **exactamente** este bloque; no actives `.venv` manualmente y no uses `python` del PATH:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { New-Item -ItemType Directory -Force -Path $E | Out-Null; Start-Transcript -Path (Join-Path $E "api_13_D_01.txt") -Force; if(!(Test-Path -LiteralPath $Py)){throw "Python .venv no encontrado"}; & $Py -c "import fastapi,uvicorn,sys; print('venv='+sys.executable); print('fastapi='+fastapi.__version__); print('uvicorn='+uvicorn.__version__)"; if($LASTEXITCODE-ne0){throw "ENVIRONMENT-DEPENDENCY-DRIFT: fastapi/uvicorn no disponibles en .venv"}; Set-Location $R; $Dry=& $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json; if($LASTEXITCODE-ne0){throw "api dry-run falló"}; $Dry | Set-Content -LiteralPath (Join-Path $E "api_dry_run_13_D_01.json") -Encoding UTF8; $Raw=& $Py -m devpilot_core api token --json; if($LASTEXITCODE-ne0){throw "api token falló"}; $P=($Raw -join "`n") | ConvertFrom-Json; $Token=[string]$P.data.token; if([string]::IsNullOrWhiteSpace($Token)){throw "token vacío"}; $env:DEVPILOT_API_TOKEN=$Token; Set-Clipboard -Value $Token; $env:PYTHONPATH="src"; Write-Host "PASS — API D01 preparada con .venv canónico; token copiado al portapapeles; servidor foreground inicia ahora." -ForegroundColor Green; & $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-eq0){Write-Host "PASS — API D01 detenida ordenadamente." -ForegroundColor Green}else{Write-Host "BLOCK — API D01 terminó con código $RC." -ForegroundColor Red; exit 1} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — API D01: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

Esta consola queda ocupada por Uvicorn durante D01.

**No pegues el token en evidencia ni chat.**

Si aparece `BLOCK/ENVIRONMENT-DEPENDENCY-DRIFT`, no instales nada y detente.

---

# 7. Consola 3 — UI

Abre una tercera PowerShell.

Ejecuta:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01"; try { New-Item -ItemType Directory -Force -Path $E | Out-Null; Start-Transcript -Path (Join-Path $E "ui_13_D_01.txt") -Force; Set-Location $R; & npm.cmd --version; if($LASTEXITCODE-ne0){throw "npm no disponible"}; Write-Host "PASS — UI D01 foreground inicia ahora." -ForegroundColor Green; & npm.cmd --prefix ui/web run dev; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-eq0){Write-Host "PASS — UI D01 detenida ordenadamente." -ForegroundColor Green}else{Write-Host "BLOCK — UI D01 terminó con código $RC." -ForegroundColor Red; exit 1} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — UI D01: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

Abre:

```text
http://127.0.0.1:5173
```

Si DevPilot solicita `DEVPILOT_API_TOKEN`, pega con `Ctrl+V` el token que la Consola 2 dejó en el portapapeles.

---

# 8. Procedimiento obligatorio de capturas browser

Para cada estado indicado:

1. deja visible la superficie completa de DevPilot;
2. evita que aparezcan tokens, contraseñas o datos sensibles;
3. pulsa `Win + Shift + S`;
4. elige **Rectangular**;
5. captura toda la ventana útil del navegador, incluyendo título/superficie y estado relevante;
6. abre la notificación de Recortes;
7. usa **Guardar como**;
8. guarda en:

```text
D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01\screenshots
```

9. usa exactamente el nombre indicado por esta Run Card.

No reemplaces una captura requerida con una descripción textual.

---

# 9. First-attempt browser

## 9.1 Project Status

Entra a DevPilot y confirma el proyecto activo.

Captura obligatoria:

```text
01_project_status_initial.png
```

Debe permitir identificar:

- proyecto activo;
- etapa/estado;
- next action.

## 9.2 Planning

Confirma Roadmap/Backlog/Sprint FROZEN y `IMPLEMENTING_READY` o equivalente inequívoco.

Captura:

```text
02_planning_frozen_implementing_ready.png
```

## 9.3 Story Code — primer estado

Desde **Project Status**, usa la acción principal normal para continuar.

No escribas `/story/code` manualmente para saltar navegación.

Al llegar, **antes de tocar nada**, captura:

```text
03_story_code_first_attempt.png
```

Este screenshot es crítico para determinar si `CAP-13D01-STORY-ACTIVATION-002` existe realmente.

## 9.4 Activación de Story READY

Si DevPilot presenta selector/acción normal para una Story READY, captura antes de usarla:

```text
04_story_ready_activation_action.png
```

Luego usa exclusivamente esa acción normal.

No inventes Story ID.

No uses terminal/API/manual JSON.

Esperado:

```text
DoR
→ StoryContextPack
→ StoryExecution PLANNED
→ StoryExecution IN_PROGRESS
```

Cuando se materialice, captura:

```text
05_story_execution_planned_or_in_progress.png
```

## 9.5 Context reviewability

Inspecciona mediante UI, sin filesystem:

- story/objetivo;
- acceptance criteria;
- requirements;
- architecture/constraints;
- test intent;
- provenance/context hash/source refs.

Captura la superficie más informativa:

```text
06_story_context_reviewability.png
```

## 9.6 Implementation route

Comprueba:

- Manual first-class;
- agent-assisted mock/fake-local opcional;
- real local/external no requerido;
- provider/model/provenance visibles si aplica;
- model route no concede source/tool/apply/approval authority.

Captura:

```text
07_implementation_route_provenance.png
```

## 9.7 Stop antes de D02

No ejecutes Change Plan.

Captura el estado final D01:

```text
08_stop_before_change_plan.png
```

---

# 10. BLOCK inmediato

Detente en el primer punto donde ocurra cualquiera:

- `no active story` sin acción normal para activar READY story;
- Story activation requiere terminal/API/operator;
- Project Context `EMPTY/UNKNOWN`;
- no existe Story READY pese a Planning ejecutable;
- Owner debe decidir sin contexto/provenance suficiente;
- model route concede autoridad indebida;
- S0/S1 reproducible;
- `.venv` canónico no puede importar FastAPI/Uvicorn;
- API/UI no arrancan mediante sus entrypoints estándar.

Antes de detenerte:

1. toma `99_block_state.png`;
2. actualiza `MANUAL_OBSERVATIONS_13_D_01.md`;
3. no pruebes workarounds;
4. conserva API/UI/audit transcripts.

---

# 11. Completar observaciones manuales

En Consola 1 abre:

```powershell
notepad "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01\MANUAL_OBSERVATIONS_13_D_01.md"
```

Completa todos los campos observables.

No inventes datos que DevPilot no mostró.

Guarda y cierra Notepad.

---

# 12. Cierre de servicios y transcript

Primero, en **Consola 3**, pulsa `Ctrl+C` para detener Vite.

Después, en **Consola 2**, pulsa `Ctrl+C` para detener Uvicorn.

Por último, en **Consola 1**, ejecuta:

```powershell
try { Set-Clipboard -Value ""; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_01"; $Required=@("START_STATE_13_D_01.json","MANUAL_OBSERVATIONS_13_D_01.md","audit_13_D_01.txt","api_13_D_01.txt","ui_13_D_01.txt"); $Missing=@($Required | Where-Object { !(Test-Path -LiteralPath (Join-Path $E $_)) }); if($Missing.Count-ne0){throw "faltan artefactos: $($Missing -join ', ')"}; $Shots=@(Get-ChildItem -LiteralPath (Join-Path $E "screenshots") -Filter "*.png" -ErrorAction SilentlyContinue); if($Shots.Count-lt1){throw "no hay capturas browser"}; Write-Host "PASS — evidencia D01 mínima presente; screenshots=$($Shots.Count)" -ForegroundColor Green; Stop-Transcript | Out-Null } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — cierre evidencia D01: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

---

# 13. Construir Run Packet

Abre **una PowerShell nueva solo después de cerrar las tres consolas anteriores**.

Ejecuta:

```powershell
$Root="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01"; $Run=Join-Path $Root "RUN_01"; $Out=Join-Path $Root "RUN_PACKET_13_D_01_RUN_01.zip"; try { if(!(Test-Path -LiteralPath $Run)){throw "RUN_01 no existe"}; if(Test-Path -LiteralPath $Out){Remove-Item -LiteralPath $Out -Force}; Compress-Archive -Path (Join-Path $Run "*") -DestinationPath $Out -CompressionLevel Optimal; if(!(Test-Path -LiteralPath $Out)){throw "Run Packet no fue creado"}; $H=(Get-FileHash -Algorithm SHA256 -LiteralPath $Out).Hash.ToLowerInvariant(); Set-Content -LiteralPath ($Out+".sha256") -Value "$H  $(Split-Path $Out -Leaf)" -Encoding ASCII; Write-Host "PASS — Run Packet D01 creado: $Out" -ForegroundColor Green } catch { Write-Host ("BLOCK — Run Packet D01: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Adjunta para adjudicación:

- `RUN_PACKET_13_D_01_RUN_01.zip`;
- `RUN_PACKET_13_D_01_RUN_01.zip.sha256`;
- la salida de consola consolidada si la mantienes como evidencia externa adicional.

---

# 14. PASS / BLOCK

`PASS` o `PASS+FINDING` solo si:

- API/UI arrancaron por entrypoints estándar;
- first Story se activó por UI normal;
- StoryExecution llegó a `PLANNED/IN_PROGRESS`;
- contexto es suficientemente revisable;
- route/provenance es gobernada;
- capturas obligatorias alcanzadas están presentes;
- `operator_project_writes=0`;
- `normal_user_terminal_escapes=0`;
- Full Regression=0;
- D02 todavía no se ejecutó.

Si no, `BLOCK` con first-attempt preservado.
