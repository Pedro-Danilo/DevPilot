---
doc_id: "DEVPL-GSDLC-13-D-01-RUN-CARD"
title: "Run Card 13-D-01 — First Story activation/context + implementation route"
status: "approved"
version: "1.0.3"
owner: "Ordóñez"
updated: "2026-09-30"
approval: "approved_by_owner_for_13_d_01_retest"
checkpoint_id: "13-D-01"
predecessor: "RUN_CARD_13_D_01_v1_0_2_APPROVED.md"
first_attempt: "BLOCK/CAP-13D01-STORY-ACTIVATION-002"
full_regression_runs_allowed: 0
operator_project_writes_allowed: false
background_processes_allowed: false
---

# Run Card `13-D-01` — v1.0.3 — retest funcional

## 1. Objetivo exacto

Demostrar por navegador normal que el corrective cerró `CAP-13D01-STORY-ACTIVATION-002` y que DevPilot
puede transformar una Story READY del Sprint FROZEN en una `StoryExecution IN_PROGRESS`, mostrando al
Owner DoR, StoryContextPack y route/provenance antes de cualquier SourceChangePlan.

Esta ejecución es **RUN_02**. `RUN_01` permanece inmutable como first-attempt BLOCK.

## 2. Qué debe demostrarse, en una frase

`Planning FROZEN → READY story visible → Preparar contexto → DoR PASS → ContextPack visible → PLANNED → Iniciar → IN_PROGRESS → route/provenance visible → STOP antes de D02`.

No basta con que la API responda 200. Debe existir una ruta de usuario normal y comprensible.

## 3. Evidencia RUN_02

Raíz:

```text
D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02
```

Capturas obligatorias de PASS:

```text
01_project_status_initial.png
02_planning_frozen_implementing_ready.png
03_story_code_activation_panel_ready.png
04_ready_story_before_prepare.png
05_dor_context_pack_planned.png
06_story_execution_in_progress.png
07_context_reviewability.png
08_implementation_route_provenance.png
09_stop_before_d02.png
```

Ante BLOCK: guarda lo alcanzado y `99_block_state.png`.

## 4. Reglas

- tres consolas foreground: Auditoría, API, UI;
- Python siempre desde `D:\Projects\DevPilot_Local\.venv\Scripts\python.exe`;
- no background;
- no terminal/API manual para activar Story;
- no editar runtime JSON;
- no project writes del operador;
- no Full Regression;
- no E1/E2/E3;
- no source mutation antes de D02;
- no instalar paquetes;
- preservar RUN_02 first-attempt del corrective.

## 5. Consola 1 — inicializar auditoría RUN_02

Abre PowerShell y ejecuta:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; $S=Join-Path $E "screenshots"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { New-Item -ItemType Directory -Force -Path $E,$S | Out-Null; Start-Transcript -Path (Join-Path $E "audit_13_D_01_RUN_02.txt") -Force; $Head=(git -C $R rev-parse HEAD).Trim(); $Dirty=@(git -C $R status --porcelain); if($Dirty.Count-ne0){throw "DevPilot worktree no está limpio"}; if(!(Test-Path -LiteralPath (Join-Path $R "docs\validation\RUN_CARD_13_D_01_v1_0_3_APPROVED.md"))){throw "Run Card v1.0.3 no instalada"}; & $Py -c "import sys; print(sys.executable)"; if($LASTEXITCODE-ne0){throw "Python .venv no ejecuta"}; [ordered]@{checkpoint="13-D-01";run="RUN_02";captured_at=(Get-Date).ToString("o");devpilot_head=$Head;repo_clean=$true;workspace="D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield";operator_project_writes=0;normal_user_terminal_escapes=0;full_regression_runs=0} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $E "START_STATE_13_D_01_RUN_02.json") -Encoding UTF8; @"
# MANUAL OBSERVATIONS — 13-D-01 RUN_02

- checkpoint_result: PENDING
- active_project:
- planning_state:
- activation_panel_state:
- ready_candidates_seen:
- selected_story_id:
- selected_story_title:
- dor_status:
- dor_checks_visible:
- context_pack_id:
- context_pack_hash_visible:
- story_execution_planned_seen:
- story_execution_in_progress_seen:
- context_fragments_reviewed:
- implementation_route_manual_first_class:
- agent_route_if_any:
- provider_model_if_any:
- provenance_visible:
- source_mutation_observed_before_d02: false
- operator_project_writes: 0
- normal_user_terminal_escapes: 0
- full_regression_runs: 0
- moments_of_confusion:
- ux_findings:
- owner_confidence_1_to_5:
- block_reason_if_any:
- notes:
"@ | Set-Content -LiteralPath (Join-Path $E "MANUAL_OBSERVATIONS_13_D_01_RUN_02.md") -Encoding UTF8; Write-Host "PASS — D01 RUN_02 audit/evidence inicializada; HEAD=$Head" -ForegroundColor Green } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — D01 RUN_02 audit init: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Mantén abierta esta consola.

## 6. Consola 2 — API estándar

Abre otra PowerShell:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { Start-Transcript -Path (Join-Path $E "api_13_D_01_RUN_02.txt") -Force; & $Py -c "import fastapi,uvicorn,sys; print('venv='+sys.executable); print('fastapi='+fastapi.__version__); print('uvicorn='+uvicorn.__version__)"; if($LASTEXITCODE-ne0){throw "FastAPI/Uvicorn no disponibles"}; Set-Location $R; $Dry=& $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json; if($LASTEXITCODE-ne0){throw "api dry-run falló"}; $Dry | Set-Content -LiteralPath (Join-Path $E "api_dry_run_RUN_02.json") -Encoding UTF8; $Raw=& $Py -m devpilot_core api token --json; if($LASTEXITCODE-ne0){throw "api token falló"}; $P=($Raw -join "`n")|ConvertFrom-Json; $Token=[string]$P.data.token; if([string]::IsNullOrWhiteSpace($Token)){throw "token vacío"}; $env:DEVPILOT_API_TOKEN=$Token; Set-Clipboard -Value $Token; $env:PYTHONPATH="src"; Write-Host "PASS — API RUN_02 preparada; servidor foreground inicia ahora" -ForegroundColor Green; & $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-eq0){Write-Host "PASS — API RUN_02 detenida ordenadamente" -ForegroundColor Green}else{Write-Host "BLOCK — API RUN_02 terminó con código $RC" -ForegroundColor Red; exit 1} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — API RUN_02: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

No copies el token a evidencia.

## 7. Consola 3 — UI estándar

Abre otra PowerShell:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; try { Start-Transcript -Path (Join-Path $E "ui_13_D_01_RUN_02.txt") -Force; Set-Location $R; & npm.cmd --version; if($LASTEXITCODE-ne0){throw "npm no disponible"}; Write-Host "PASS — UI RUN_02 inicia foreground" -ForegroundColor Green; & npm.cmd --prefix ui/web run dev; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-eq0){Write-Host "PASS — UI RUN_02 detenida ordenadamente" -ForegroundColor Green}else{Write-Host "BLOCK — UI RUN_02 terminó con código $RC" -ForegroundColor Red; exit 1} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — UI RUN_02: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

Abre `http://127.0.0.1:5173` y autentícate normalmente.

## 8. Capturas

Para cada captura: muestra toda la superficie útil, oculta secretos, `Win+Shift+S`, guarda PNG en
`RUN_02\screenshots` con el nombre exacto. La captura debe demostrar el criterio indicado, no solo que
la página cargó.

## 9. Validación browser detallada

### 9.1 Project Status

**Acción:** abre Project Status del Pilot A.

**Debes demostrar:**
- proyecto `inventory-sales-local-greenfield` activo;
- estado operacional no `EMPTY/UNKNOWN`;
- next action dirige a Story Code/implementación.

**Captura:** `01_project_status_initial.png`.

**BLOCK:** proyecto incorrecto, context UNKNOWN o next action contradictoria.

### 9.2 Planning FROZEN

**Acción:** abre Planning mediante UI normal.

**Debes demostrar:** Roadmap/Backlog/Sprint ya cerrados y Planning `FROZEN / IMPLEMENTING_READY` o
equivalente inequívoco. No edites ni thaw Planning.

**Captura:** `02_planning_frozen_implementing_ready.png`.

### 9.3 Story Code — corrective visible

**Acción:** vuelve a Project Status y usa su acción normal para entrar a Story Code.

**Debes demostrar:** en la parte superior aparece **`Story activation & context`** y ya no dependes de
`Story sin story · UNKNOWN` sin salida. La superficie debe indicar Sprint FROZEN y estado de activación.

**Captura:** `03_story_code_activation_panel_ready.png`.

**BLOCK:** panel ausente; error de carga; no hay vía de activación.

### 9.4 Story READY antes de preparar

**Acción:** sin pulsar aún `Preparar contexto`, inspecciona la lista del panel.

**Debes demostrar:**
- al menos una Story READY;
- Story ID y título visibles;
- acceptance criteria count/contenido suficientemente identificable;
- una acción normal **`Preparar contexto`** asociada a la Story;
- no se te pide escribir Story ID a mano.

**Captura:** `04_ready_story_before_prepare.png`.

**BLOCK:** `ready_candidates=0` pese a Planning READY, selector vacío, o requiere terminal/API manual.

### 9.5 Preparar contexto → DoR + PLANNED

**Acción:** pulsa **una sola vez** `Preparar contexto` sobre la primera/recomendada Story READY.

**Debes demostrar después:**
- DoR = PASS/READY;
- checks DoR visibles o inspeccionables;
- StoryContextPack materializado con ID/hash;
- fragments/references de requirement, ADR, risk, test-intent y AC;
- StoryExecution = `PLANNED`;
- Planning/source no fueron modificados;
- botón `Iniciar story preparada` habilitado.

**Captura:** `05_dor_context_pack_planned.png`.

**BLOCK:** DoR falla sin causa explicable, ContextPack ausente, Story sigue UNKNOWN, o aparece source mutation.

### 9.6 Iniciar Story

**Acción:** pulsa **`Iniciar story preparada`** una sola vez.

**Debes demostrar:** StoryExecution pasa de `PLANNED` a `IN_PROGRESS`; la misma Story permanece activa.
No debe existir cambio implícito de Story.

**Captura:** `06_story_execution_in_progress.png`.

### 9.7 Reviewability del contexto

**Acción:** inspecciona DoR/ContextPack en la UI.

**Debes demostrar que un Owner puede decidir con contexto suficiente:**
- objetivo/título Story;
- AC;
- requirement;
- architecture/ADR;
- risk/security;
- test intent;
- ContextPack ID/hash y source/provenance refs.

No abras archivos internos por terminal para completar lo que la UI no muestre.

**Captura:** `07_context_reviewability.png`.

**BLOCK:** el backend tiene datos pero la UI no permite comprenderlos suficientemente.

### 9.8 Implementation route / provenance

**Acción:** inspecciona la sección de route/provenance. No generes todavía SourceChangePlan.

**Debes demostrar:**
- Manual = first-class;
- mock/fake-local proposal-only puede existir como opción, pero no es requisito;
- real local/external API no requerida en Pilot A;
- si hay provider/model/access route, se ve provenance;
- la route no concede tool/source/apply/approval/Git authority.

**Captura:** `08_implementation_route_provenance.png`.

### 9.9 STOP antes de D02

**Acción:** no guardes draft, no crees plan y no pulses apply.

**Debes demostrar:** Story sigue `IN_PROGRESS`; D01 está completo; no existe SourceChangePlan creado por
esta ejecución.

**Captura:** `09_stop_before_d02.png`.

## 10. BLOCK inmediato

Ante primer BLOCK:
1. no intentes workaround;
2. toma `99_block_state.png`;
3. completa observaciones hasta ese punto;
4. detén UI/API ordenadamente;
5. empaqueta RUN_02;
6. vuelve para adjudicación.

## 11. Completar observaciones

En Consola 1:

```powershell
notepad "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02\MANUAL_OBSERVATIONS_13_D_01_RUN_02.md"
```

Completa solo lo observado; no infieras estados invisibles.

## 12. Cerrar servicios

Primero `Ctrl+C` en UI, luego `Ctrl+C` en API. Finalmente en Consola 1:

```powershell
try { Set-Clipboard -Value ""; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; $Req=@("START_STATE_13_D_01_RUN_02.json","MANUAL_OBSERVATIONS_13_D_01_RUN_02.md","audit_13_D_01_RUN_02.txt","api_13_D_01_RUN_02.txt","ui_13_D_01_RUN_02.txt"); $Missing=@($Req|Where-Object{!(Test-Path -LiteralPath (Join-Path $E $_))}); if($Missing.Count-ne0){throw "faltan: $($Missing -join ', ')"}; $Shots=@(Get-ChildItem -LiteralPath (Join-Path $E "screenshots") -Filter "*.png" -ErrorAction SilentlyContinue); if($Shots.Count-lt1){throw "sin screenshots"}; Write-Host "PASS — evidencia RUN_02 lista; screenshots=$($Shots.Count)" -ForegroundColor Green; Stop-Transcript|Out-Null } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — cierre RUN_02: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

## 13. Run Packet

En una PowerShell nueva después de cerrar las tres anteriores:

```powershell
$Root="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01"; $Run=Join-Path $Root "RUN_02"; $Out=Join-Path $Root "RUN_PACKET_13_D_01_RUN_02.zip"; try { if(Test-Path $Out){Remove-Item $Out -Force}; Compress-Archive -Path (Join-Path $Run "*") -DestinationPath $Out -CompressionLevel Optimal; $H=(Get-FileHash -Algorithm SHA256 -LiteralPath $Out).Hash.ToLowerInvariant(); Set-Content -LiteralPath ($Out+".sha256") -Value "$H  $(Split-Path $Out -Leaf)" -Encoding ASCII; Write-Host "PASS — Run Packet D01 RUN_02 creado: $Out" -ForegroundColor Green } catch { Write-Host ("BLOCK — Run Packet RUN_02: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Adjunta ZIP + SHA + salida consolidada si existe.

## 14. PASS

Solo PASS/PASS+FINDING si los pasos 9.1–9.9 quedaron demostrados, `operator_project_writes=0`,
`normal_user_terminal_escapes=0`, Full=0 y D02 no se inició.
