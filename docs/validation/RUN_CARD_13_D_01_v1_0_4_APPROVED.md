---
doc_id: "DEVPL-GSDLC-13-D-01-RUN-CARD"
title: "Run Card 13-D-01 — RUN_02 continuation after context reviewability corrective"
status: "approved"
version: "1.0.4"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "approved_by_owner_for_run_02_continuation"
checkpoint_id: "13-D-01"
predecessor: "RUN_CARD_13_D_01_v1_0_3_APPROVED.md"
continuation_from: "9.7"
first_attempt: "BLOCK/CAP-13D01-STORY-ACTIVATION-002"
run_02_partial_finding: "BLOCK/CAP-13D01-CONTEXT-REVIEWABILITY-003"
full_regression_runs_allowed: 0
operator_project_writes_allowed: false
background_processes_allowed: false
---

# Run Card `13-D-01` — v1.0.4 — continuación de `RUN_02`

## 1. Propósito

Continuar el `RUN_02` ya ejecutado correctamente hasta 9.6 después de instalar el corrective de reviewability. Esta Run Card **no repite 9.1–9.6**, no reinicia StoryExecution y no invalida las capturas previas.

Estado esperado al reanudar:

```text
Project/Planning authority = unchanged
Story = story-rf-001
StoryExecution = IN_PROGRESS
SourceChangePlan created by RUN_02 = false
Full Regression = 0
```

**Nota de continuidad:** v1.0.3 ordenó 9.6 (`Iniciar Story`) antes de 9.7 (`Reviewability`). Por eso este RUN_02 ya está `IN_PROGRESS` y no se debe fabricar un rollback/restart de Story para recrear `PLANNED`. La continuación valida sobre el mismo ContextPack que la nueva representación humana es suficiente y que habría estado disponible desde `PLANNED`; en la siguiente Story/repetición, el Owner deberá efectuar esta revisión humana antes de pulsar `Iniciar story preparada`. Esta limitación de secuencia se conserva como finding de continuidad, no se oculta.

## 2. Evidencia previa que se reutiliza

Dentro de la misma raíz `RUN_02` deben existir y conservarse sin sobrescribir:

```text
01_project_status_initial.png
02_planning_frozen_implementing_ready.png
03_story_code_activation_panel_ready.png
04_ready_story_before_prepare.png
05_dor_context_pack_planned.png
06_story_execution_in_progress.png
```

No vuelvas a pulsar `Preparar contexto` ni `Iniciar story preparada`.

## 3. Reglas

- tres consolas foreground: Auditoría, API, UI;
- no background;
- no terminal/API manual para modificar StoryExecution;
- no editar runtime JSON;
- no project writes del operador;
- no Full Regression;
- no source mutation;
- no SourceChangePlan, draft, apply ni Git;
- no borrar ni renombrar evidencia 01–06;
- cualquier inconsistencia = STOP + `99_block_state.png`.

## 4. Reiniciar servicios sin tocar runtime

Detén cualquier API/UI previa si sigue abierta. **No reutilices con `-Force` los transcript originales de v1.0.3**, porque forman parte de la evidencia 9.1–9.6 y no deben sobrescribirse. No borres `outputs/` del workspace.

### 4.1 Consola 1 — auditoría de continuación

Abre PowerShell y ejecuta esta única línea:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; $S=Join-Path $E "screenshots"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { Start-Transcript -Path (Join-Path $E "audit_13_D_01_RUN_02_CONTINUATION.txt") -Force; $Head=(git -C $R rev-parse HEAD).Trim(); $Dirty=@(git -C $R status --porcelain); if($Dirty.Count-ne0){throw "DevPilot worktree no está limpio"}; $Req=@("START_STATE_13_D_01_RUN_02.json","MANUAL_OBSERVATIONS_13_D_01_RUN_02.md","screenshots\01_project_status_initial.png","screenshots\02_planning_frozen_implementing_ready.png","screenshots\03_story_code_activation_panel_ready.png","screenshots\04_ready_story_before_prepare.png","screenshots\05_dor_context_pack_planned.png","screenshots\06_story_execution_in_progress.png"); $Missing=@($Req|Where-Object{!(Test-Path -LiteralPath (Join-Path $E $_))}); if($Missing.Count-ne0){throw "Falta evidencia previa: $($Missing -join ', ')"}; & $Py -c "import sys; print(sys.executable)"; if($LASTEXITCODE-ne0){throw "Python .venv no ejecuta"}; Write-Host "PASS — continuación RUN_02 inicializada sin sobrescribir evidencia previa; HEAD=$Head" -ForegroundColor Green } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — continuación audit: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Mantén esta consola abierta.

### 4.2 Consola 2 — API foreground

Abre otra PowerShell y ejecuta esta única línea:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { Start-Transcript -Path (Join-Path $E "api_13_D_01_RUN_02_CONTINUATION.txt") -Force; & $Py -c "import fastapi,uvicorn,sys; print('venv='+sys.executable); print('fastapi='+fastapi.__version__); print('uvicorn='+uvicorn.__version__)"; if($LASTEXITCODE-ne0){throw "FastAPI/Uvicorn no disponibles"}; Set-Location $R; $Dry=& $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json; if($LASTEXITCODE-ne0){throw "api dry-run falló"}; $Raw=& $Py -m devpilot_core api token --json; if($LASTEXITCODE-ne0){throw "api token falló"}; $P=($Raw -join "`n")|ConvertFrom-Json; $Token=[string]$P.data.token; if([string]::IsNullOrWhiteSpace($Token)){throw "token vacío"}; $env:DEVPILOT_API_TOKEN=$Token; Set-Clipboard -Value $Token; $env:PYTHONPATH="src"; Write-Host "PASS — API continuación preparada; servidor foreground inicia ahora" -ForegroundColor Green; & $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-eq0){Write-Host "PASS — API continuación detenida ordenadamente" -ForegroundColor Green}else{Write-Host "BLOCK — API continuación terminó con código $RC" -ForegroundColor Red; exit 1} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — API continuación: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

No copies el token a evidencia.

### 4.3 Consola 3 — UI foreground

Abre otra PowerShell y ejecuta esta única línea:

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; try { Start-Transcript -Path (Join-Path $E "ui_13_D_01_RUN_02_CONTINUATION.txt") -Force; Set-Location $R; & npm.cmd --version; if($LASTEXITCODE-ne0){throw "npm no disponible"}; Write-Host "PASS — UI continuación inicia foreground" -ForegroundColor Green; & npm.cmd --prefix ui/web run dev; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-eq0){Write-Host "PASS — UI continuación detenida ordenadamente" -ForegroundColor Green}else{Write-Host "BLOCK — UI continuación terminó con código $RC" -ForegroundColor Red; exit 1} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — UI continuación: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

Abre `http://127.0.0.1:5173/story/code` y autentícate normalmente.

## 5. Checkpoint de reanudación

Antes de continuar, confirma visualmente:

- Story `story-rf-001` o la misma Story previamente iniciada;
- StoryExecution `IN_PROGRESS`;
- panel `Owner context review` visible;
- no se creó SourceChangePlan;
- botones de preparación/inicio no se usan de nuevo.

Si no se conserva `IN_PROGRESS`, toma `99_block_state.png` y STOP.

## 6. Paso 9.7 — Reviewability del contexto

**Acción:** revisa exclusivamente el panel `Owner context review`.

**Debe ser comprensible sin leer JSON crudo como mecanismo principal:**

1. `Story y Acceptance Criteria`: ID, título, versión y AC completos;
2. `Definition of Ready`: estado y checks con código/mensaje;
3. `Requirement`: target, source ref y contenido pertinente;
4. `Architecture / ADR`: target, source ref y restricción/decisión pertinente;
5. `Risk / security`: target, source ref y contenido pertinente;
6. `Test intent`: target, source ref y contenido pertinente;
7. `ContextPack / StoryExecution / safety`: IDs, hashes, estado y confirmación de no mutación;
8. `Implementation route / authority`: ruta Manual first-class, agent proposal-only y límites de authority.

En la parte superior debe existir una decisión explícita y coherente con el estado actual. Para esta continuación `IN_PROGRESS`:

```text
CONTINUAR = contexto revisable y suficiente → cerrar D01 sin reiniciar la Story
DETENER = inconsistencia o contexto insuficiente → BLOCK, no iniciar D02
```

En una Story futura todavía `PLANNED`, `CONTINUAR` debe indicar que el Owner puede pulsar `Iniciar story preparada`; `DETENER` debe impedir el inicio.

Esta decisión **no es** approval de source/apply. Es una decisión de suficiencia de contexto.

La sección `Evidencia técnica expandible` puede contener JSON completo para provenance, pero no debe ser necesaria para entender los ocho puntos anteriores.

**Captura:** `07_context_reviewability.png`.

**BLOCK:** faltan AC/DoR/requirement/ADR/risk/test-intent; solo se puede entender leyendo JSON crudo; source refs/provenance no son visibles; o la UI no explica qué decide el Owner.

## 7. Paso 9.8 — Implementation route / provenance

**Acción:** dentro del mismo panel revisa `Implementation route / authority` y, si deseas corroborar campos completos, expande la evidencia técnica.

**Debes demostrar:**

- Manual = available / first-class;
- source write = approval-gated;
- terminal required = false;
- agent-assisted = mock/fake-local, proposal-only;
- real local model = no requerido en Pilot A;
- external API = no requerida;
- model route no concede tool/apply/approval authority;
- no existe source mutation por esta revisión.

**Captura:** `08_implementation_route_provenance.png`.

## 8. Paso 9.9 — STOP antes de D02

No uses `Guardar draft`, `Generar propuesta`, `Crear SourceChangePlan`, `Dry-run`, approvals, apply, validación, jobs ni Git.

Demuestra:

- Story sigue `IN_PROGRESS`;
- contexto fue revisado;
- Owner eligió `CONTINUAR` para cerrar D01;
- no existe SourceChangePlan creado por RUN_02;
- `operator_project_writes=0`;
- `normal_user_terminal_escapes=0`;
- `full_regression_runs=0`.

**Captura:** `09_stop_before_d02.png`.

## 9. Completar observaciones

Abre el `MANUAL_OBSERVATIONS_13_D_01_RUN_02.md` existente y completa solo lo observado. Para esta continuación registra como mínimo:

```text
checkpoint_result: PASS | PASS+FINDING | BLOCK
active_project:
planning_state:
activation_panel_state:
ready_candidates_seen:
selected_story_id:
selected_story_title:
dor_status:
dor_checks_visible:
context_pack_id:
context_pack_hash_visible:
story_execution_planned_seen: true
story_execution_in_progress_seen: true
context_fragments_reviewed: requirement, adr, risk, test-intent, acceptance
implementation_route_manual_first_class:
agent_route_if_any:
provider_model_if_any:
provenance_visible:
source_mutation_observed_before_d02: false
operator_project_writes: 0
normal_user_terminal_escapes: 0
full_regression_runs: 0
moments_of_confusion:
ux_findings:
owner_confidence_1_to_5:
block_reason_if_any:
notes:
```

No infieras campos invisibles.

## 10. Cerrar y empaquetar

Cierra UI con `Ctrl+C`, luego API con `Ctrl+C`. Después, en Consola 1 ejecuta esta única línea para verificar la continuación y cerrar el transcript:

```powershell
try { Set-Clipboard -Value ""; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01\RUN_02"; $Req=@("MANUAL_OBSERVATIONS_13_D_01_RUN_02.md","audit_13_D_01_RUN_02_CONTINUATION.txt","api_13_D_01_RUN_02_CONTINUATION.txt","ui_13_D_01_RUN_02_CONTINUATION.txt","screenshots\07_context_reviewability.png","screenshots\08_implementation_route_provenance.png","screenshots\09_stop_before_d02.png"); $Missing=@($Req|Where-Object{!(Test-Path -LiteralPath (Join-Path $E $_))}); if($Missing.Count-ne0){throw "Falta evidencia de continuación: $($Missing -join ', ')"}; Write-Host "PASS — continuación RUN_02 completa; evidencia 07–09 presente" -ForegroundColor Green; Stop-Transcript|Out-Null } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — cierre continuación RUN_02: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

En una PowerShell nueva crea el Run Packet con esta única línea:

```powershell
$Root="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-01"; $Run=Join-Path $Root "RUN_02"; $Out=Join-Path $Root "RUN_PACKET_13_D_01_RUN_02.zip"; try { if(Test-Path $Out){Remove-Item $Out -Force}; Compress-Archive -Path (Join-Path $Run "*") -DestinationPath $Out -CompressionLevel Optimal; $H=(Get-FileHash -Algorithm SHA256 -LiteralPath $Out).Hash.ToLowerInvariant(); Set-Content -LiteralPath ($Out+".sha256") -Value "$H  $(Split-Path $Out -Leaf)" -Encoding ASCII; Write-Host "PASS — Run Packet D01 RUN_02 creado: $Out" -ForegroundColor Green } catch { Write-Host ("BLOCK — Run Packet RUN_02: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Se deben producir:

```text
RUN_PACKET_13_D_01_RUN_02.zip
RUN_PACKET_13_D_01_RUN_02.zip.sha256
```

El ZIP debe contener evidencia 01–09, observaciones y ambos juegos de transcripts. No debe contener secretos.

## 11. PASS

`13-D-01 RUN_02` solo puede adjudicarse PASS/PASS+FINDING cuando 9.1–9.9 estén demostrados acumulativamente, `operator_project_writes=0`, `normal_user_terminal_escapes=0`, Full=0 y D02 no se haya iniciado.
