---
doc_id: "DEVPL-GSDLC-13-D-02-RUN-CARD"
title: "Run Card 13-D-02 — implementation proposal → Draft Set → Change Plan/apply — corrective retest"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "projected_for_owner_execution_after_corrective_windows_pass"
checkpoint_id: "13-D-02"
predecessor: "RUN_CARD_13_D_02_v1_0_0_APPROVED.md"
first_attempt: "BLOCK/FUNC-13D02-IMPLEMENTATION-BRIDGE-001"
continuation_run: "RUN_02"
continuation_from: "step-9"
authority_base_commit: "4ae933ec4c8fd448a1da1d9d46c6382044f8acd9"
authority_target: "repo456 / corrective successor"
active_story: "story-rf-001"
expected_start_story_status: "IN_PROGRESS"
full_regression_runs_allowed: 0
operator_project_writes_allowed: false
background_processes_allowed: false
---

# Run Card `13-D-02` v1.0.1 — corrective retest / RUN_02

## 1. Qué se conserva

`RUN_01` es evidencia inmutable del first-attempt y **no se repite ni se sobrescribe**. Ya demostró:

- repo455/start state válido;
- Story `story-rf-001 / IN_PROGRESS`;
- API/UI sanas;
- source tree vacío;
- bloqueo antes de crear SourceDraftBuffer.

RUN_02 continúa con la misma StoryExecution sobreviviente después de instalar/promover el corrective. No borres `outputs/story_execution`, no vuelvas a D01 y no uses terminal para crear project source.

## 2. Objetivo

Demostrar este journey normal:

```text
Story IN_PROGRESS + source-empty
→ Proponer implementación desde contexto
→ revisar tecnología / rationale / paths / contenido / provenance
→ Owner ACCEPT
→ SourceDraftBuffer Set runtime-only
→ revisar/revalidar cada draft
→ SourceChangePlan multi-file immutable
→ full diff + risk + Test Impact
→ plan recheck + dry-run
→ exact Owner approval
→ final recheck
→ atomic apply
→ ApplyManifest
→ CHANGES_READY
→ STOP antes de D03
```

## 3. Qué significa la nueva propuesta

`Proponer implementación desde contexto` **no aplica source y no llama un modelo real**. DevPilot usa StoryContextPack + Architecture FROZEN y genera un candidate local/determinístico. Debes revisar:

- Story ID/title;
- provider/model label;
- tecnología derivada de Architecture;
- rationale;
- lista completa de archivos propuestos;
- path y operación de cada archivo;
- contenido de cada archivo;
- StoryContextPack/Architecture provenance;
- safety: proposal-only, source write=false, apply/approval/Git authority=false.

`Aceptar como Draft Set` significa únicamente: “esta propuesta es suficientemente coherente para convertirla en drafts runtime-only”. **No es approval de source**.

`Manual CREATE/EDIT/RENAME` sigue disponible si el Owner rechaza la propuesta o necesita una edición puntual. No necesitas escoger `.py` por tu cuenta: la propuesta deriva las extensiones/rutas de Architecture. La UI también muestra la allowlist de extensiones de policy.

## 4. Evidencia RUN_02

Raíz:

```text
D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_02
```

Capturas obligatorias:

```text
01_d02_retest_start.png
02_implementation_proposal_review.png
03_draft_set_runtime_only.png
04_source_change_plan_multifile.png
05_plan_recheck_dry_run.png
06_apply_approval_requested.png
07_approval_center_exact_plan.png
08_pre_apply_recheck.png
09_apply_manifest_changes_ready.png
10_stop_before_d03.png
```

Ante BLOCK: `99_block_state.png` y STOP.

## 5. Reglas

- tres consolas foreground;
- no background;
- no Full Regression;
- no ChatGPT/terminal/editor externo para producir project content;
- no edición manual de runtime JSON;
- no Git stage/commit/push;
- no D03 (`Validar story`, StoryTestPlan, jobs, Quality);
- no rollback salvo adjudicación posterior;
- `operator_project_writes=0`;
- `normal_user_terminal_escapes=0`;
- source solo puede cambiar en `Aplicar plan aprobado`.

## 6. Consola 1 — auditoría RUN_02

Abre PowerShell y ejecuta una sola línea:

```powershell
$R="D:\Projects\DevPilot_Local"; $W="D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_02"; $S=Join-Path $E "screenshots"; try { New-Item -ItemType Directory -Force -Path $E,$S | Out-Null; Start-Transcript -Path (Join-Path $E "audit_13_D_02_RUN_02.txt") -Force; $Base="4ae933ec4c8fd448a1da1d9d46c6382044f8acd9"; $Head=(git -C $R rev-parse HEAD).Trim(); $Remote=(git -C $R rev-parse "@{u}").Trim(); if($Head-eq$Base){throw "Corrective D02 no está promovido: HEAD sigue en repo455/base"}; if($Head-ne$Remote){throw "HEAD/origin no coinciden"}; if(@(git -C $R status --porcelain).Count-ne0){throw "DevPilot worktree no está limpio"}; if(!(Test-Path -LiteralPath (Join-Path $R "src\devpilot_core\application\story_implementation_candidate_service.py"))){throw "Bridge de implementación no instalado"}; if(!(Test-Path -LiteralPath (Join-Path $R "docs\validation\RUN_CARD_13_D_02_v1_0_1_APPROVED.md"))){throw "Run Card v1.0.1 no instalada"}; $WBefore=@(git -C $W status --porcelain); $WBefore | Set-Content -LiteralPath (Join-Path $E "WORKSPACE_GIT_BEFORE_D02_RUN_02.txt") -Encoding UTF8; [ordered]@{checkpoint="13-D-02";run="RUN_02";captured_at=(Get-Date).ToString("o");devpilot_head=$Head;devpilot_remote=$Remote;base_commit=$Base;workspace=$W;expected_story_id="story-rf-001";expected_story_status="IN_PROGRESS";first_attempt_preserved=(Test-Path "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_01\99_block_state.png");operator_project_writes=0;normal_user_terminal_escapes=0;full_regression_runs=0} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $E "START_STATE_13_D_02_RUN_02.json") -Encoding UTF8; $Obs=@('# MANUAL OBSERVATIONS — 13-D-02 RUN_02','','- checkpoint_result: PENDING','- active_project:','- story_id:','- story_status_start:','- implementation_proposal_id:','- implementation_proposal_hash_visible:','- implementation_provider:','- implementation_model_label:','- architecture_profile_visible:','- proposal_files_reviewed:','- proposal_provenance_reviewed:','- proposal_source_mutations_false:','- owner_proposal_decision:','- draft_set_count:','- draft_paths:','- draft_source_mutations_false:','- all_draft_preimage_rechecks_pass:','- source_change_plan_id:','- source_change_plan_hash_full_visible:','- exact_path_allowlist:','- full_diff_reviewed:','- risk_level:','- test_impact_preview_reviewed:','- dry_run_pass:','- dry_run_source_mutations_false:','- apply_approval_id:','- approval_subject_plan_id_match:','- approval_plan_hash_match:','- approval_actor_role_owner:','- final_preimage_recheck_pass:','- apply_execution_id:','- apply_manifest_reviewed:','- unexpected_paths_observed:','- story_status_end:','- source_mutation_only_after_approved_apply:','- operator_project_writes: 0','- normal_user_terminal_escapes: 0','- full_regression_runs: 0','- moments_of_confusion:','- ux_findings:','- owner_confidence_1_to_5:','- block_reason_if_any:','- notes:'); $Obs | Set-Content -LiteralPath (Join-Path $E "MANUAL_OBSERVATIONS_13_D_02_RUN_02.md") -Encoding UTF8; Write-Host "PASS — D02 RUN_02 audit iniciada; HEAD=$Head" -ForegroundColor Green } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — audit RUN_02: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Mantén esta consola abierta.

## 7. Consola 2 — API

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_02"; $Py=Join-Path $R ".venv\Scripts\python.exe"; try { Start-Transcript -Path (Join-Path $E "api_13_D_02_RUN_02.txt") -Force; Set-Location $R; $Raw=& $Py -m devpilot_core api token --json; if($LASTEXITCODE-ne0){throw "api token falló"}; $P=($Raw -join "`n")|ConvertFrom-Json; $Token=[string]$P.data.token; if([string]::IsNullOrWhiteSpace($Token)){throw "token vacío"}; $env:DEVPILOT_API_TOKEN=$Token; Set-Clipboard -Value $Token; $env:PYTHONPATH="src"; & $Py -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-ne0){throw "API terminó con código $RC"} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — API RUN_02: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

## 8. Consola 3 — UI

```powershell
$R="D:\Projects\DevPilot_Local"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_02"; try { Start-Transcript -Path (Join-Path $E "ui_13_D_02_RUN_02.txt") -Force; Set-Location $R; & npm.cmd --prefix ui/web run dev; $RC=$LASTEXITCODE; try{Stop-Transcript|Out-Null}catch{}; if($RC-ne0){throw "UI terminó con código $RC"} } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — UI RUN_02: "+$_.Exception.Message) -ForegroundColor Red; exit 1 }
```

Abre `http://127.0.0.1:5173`, autentícate y entra normalmente a Story Code.

## 9. Confirmar continuidad

Demuestra:

- mismo proyecto;
- `story-rf-001`;
- Story `IN_PROGRESS`;
- source tree todavía vacío;
- panel **Implementación propuesta por DevPilot** visible;
- RUN_01 no fue borrado/reset.

**Captura:** `01_d02_retest_start.png`.

## 10. Generar y revisar ImplementationProposal

Pulsa **`Proponer implementación desde contexto`** una sola vez.

No pulses ACCEPT todavía. Revisa en la UI:

1. proposal ID/hash;
2. provider `devpilot-local`;
3. model/generator `deterministic-story-implementation-template-v1`;
4. tecnología derivada de Architecture;
5. rationale;
6. todos los archivos propuestos;
7. cada target path;
8. contenido completo de cada archivo;
9. StoryContextPack/Architecture provenance;
10. safety: proposal-only, source mutation=false, apply/approval/Git authority=false.

**Captura:** `02_implementation_proposal_review.png` mostrando el candidate suficiente para decidir.

**BLOCK:** paths/contenido no reviewables, stack no corresponde a Architecture, proposal escribe source/drafts antes de ACCEPT, o exige modelo/API externa.

## 11. Owner decision → Draft Set

Si la propuesta es coherente con Story/Architecture, pulsa **`Aceptar como Draft Set`** una sola vez. Si no lo es, pulsa REJECT, toma `99_block_state.png` y STOP: no la arregles con ChatGPT/terminal.

Después de ACCEPT debes ver:

- Draft Set con 1..N archivos;
- operación/target de cada draft;
- cada draft seleccionable;
- source real sigue vacío/sin cambios;
- mensaje explícito `runtime-only`/`source_mutations=false`.

Recorre cada draft usando la lista del Draft Set y lee su contenido. Si necesitas una corrección humana menor, edítala en el editor DevPilot y pulsa `Guardar draft`; no uses editor externo.

**Captura:** `03_draft_set_runtime_only.png`.

## 12. Revalidar preimage de cada draft

Selecciona cada draft del Draft Set, uno a uno, y pulsa **`Revalidar preimage`**. Para CREATE debe confirmar que el target sigue sin existir.

Cualquier CONFLICT/stale = `99_block_state.png` + STOP.

## 13. SourceChangePlan multi-file

Pulsa **`Crear SourceChangePlan`** una sola vez.

Debes demostrar:

- todos los drafts vigentes están incluidos;
- plan ID;
- plan hash completo/inspeccionable;
- exact path allowlist = paths del Draft Set;
- full diff **multi-file**;
- risk/reasons;
- Test Impact preview;
- required approval role Owner;
- source mutation=false.

**Captura:** `04_source_change_plan_multifile.png`.

**BLOCK:** solo incluye el draft seleccionado, allowlist inesperada, diff incompleto o plan muta source.

## 14. Plan recheck + dry-run

Pulsa en orden:

1. `Revalidar plan`;
2. `Dry-run`.

Debe conservar mismo plan/hash/allowlist y `source_mutations=false`.

**Captura:** `05_plan_recheck_dry_run.png`.

## 15. Solicitar approval Owner

Pulsa `Solicitar approval owner` una sola vez. Registra Approval ID.

**Captura:** `06_apply_approval_requested.png`.

## 16. Approval Center exacto

Abre `Abrir Approval Center dirigido`. Antes de aprobar verifica:

- Approval ID exacto;
- actor/role Owner;
- tool/action de story source apply;
- subject = plan ID;
- plan hash exacto;
- workspace;
- exact path allowlist/effect;
- estado PENDING.

Si coincide, aprueba una sola vez.

**Captura:** `07_approval_center_exact_plan.png` después de `APPROVED`.

## 17. Recheck pre-apply

Vuelve a Story Code y pulsa `Revalidar plan` otra vez.

**Captura:** `08_pre_apply_recheck.png`.

Stale/preimage change = STOP; no regeneres dentro del mismo retest.

## 18. Atomic apply

Pulsa `Aplicar plan aprobado` exactamente una vez.

Debes demostrar:

- PASS;
- execution ID;
- apply manifest;
- plan/hash/approval coinciden;
- changed paths exactamente = allowlist;
- partial residue=false/equivalente;
- Git stage/commit=false;
- network/external API=false;
- Story `IN_PROGRESS → CHANGES_READY`.

**Captura:** `09_apply_manifest_changes_ready.png`.

## 19. STOP antes de D03

No pulses `Validar story`, StoryTestPlan, jobs, Quality, rollback o Git.

Demuestra Story `CHANGES_READY`, manifest disponible y D03 no iniciado.

**Captura:** `10_stop_before_d03.png`.

## 20. Completar observaciones

```powershell
notepad "D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_02\MANUAL_OBSERVATIONS_13_D_02_RUN_02.md"
```

Solo lo observado.

## 21. Cerrar servicios y evidencia Git read-only

`Ctrl+C` UI, luego `Ctrl+C` API. Finalmente Consola 1:

```powershell
try { Set-Clipboard -Value "CLEARED-BY-DEVPL-RUN-CARD"; $W="D:\Projects\DevPilot_Workspaces\inventory-sales-local-greenfield"; $E="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02\RUN_02"; @(git -C $W status --porcelain) | Set-Content -LiteralPath (Join-Path $E "WORKSPACE_GIT_AFTER_D02_RUN_02.txt") -Encoding UTF8; $Req=@("START_STATE_13_D_02_RUN_02.json","MANUAL_OBSERVATIONS_13_D_02_RUN_02.md","WORKSPACE_GIT_BEFORE_D02_RUN_02.txt","WORKSPACE_GIT_AFTER_D02_RUN_02.txt","audit_13_D_02_RUN_02.txt","api_13_D_02_RUN_02.txt","ui_13_D_02_RUN_02.txt","screenshots\01_d02_retest_start.png","screenshots\02_implementation_proposal_review.png","screenshots\03_draft_set_runtime_only.png","screenshots\04_source_change_plan_multifile.png","screenshots\05_plan_recheck_dry_run.png","screenshots\06_apply_approval_requested.png","screenshots\07_approval_center_exact_plan.png","screenshots\08_pre_apply_recheck.png","screenshots\09_apply_manifest_changes_ready.png","screenshots\10_stop_before_d03.png"); $Missing=@($Req|Where-Object{!(Test-Path -LiteralPath (Join-Path $E $_))}); if($Missing.Count-ne0){throw "Falta evidencia: $($Missing -join ', ')"}; Write-Host "PASS — evidencia D02 RUN_02 completa" -ForegroundColor Green; Stop-Transcript|Out-Null } catch { try{Stop-Transcript|Out-Null}catch{}; Write-Host ("BLOCK — cierre RUN_02: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

## 22. Run Packet

```powershell
$Root="D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-13\13-D\13-D-02"; $Run=Join-Path $Root "RUN_02"; $Out=Join-Path $Root "RUN_PACKET_13_D_02_RUN_02.zip"; try { if(Test-Path $Out){Remove-Item $Out -Force}; Compress-Archive -Path (Join-Path $Run "*") -DestinationPath $Out -CompressionLevel Optimal; $H=(Get-FileHash -Algorithm SHA256 -LiteralPath $Out).Hash.ToLowerInvariant(); Set-Content -LiteralPath ($Out+".sha256") -Value "$H  $(Split-Path $Out -Leaf)" -Encoding ASCII; Write-Host "PASS — Run Packet RUN_02: $Out" -ForegroundColor Green } catch { Write-Host ("BLOCK — Run Packet: "+$_.Exception.Message) -ForegroundColor Red; throw }
```

Adjunta ZIP + SHA + salida consolidada.

## 23. PASS

D02 solo es PASS/PASS+FINDING si acumulativamente:

- RUN_01 first-attempt permanece preservado;
- misma Story D01 → D02;
- ImplementationProposal reviewable y architecture-grounded;
- proposal source mutations=0;
- Owner ACCEPT materializa Draft Set runtime-only;
- todos los drafts/preimages pasan recheck;
- un único SourceChangePlan incluye el Draft Set completo;
- full multi-file diff + risk + Test Impact reviewados;
- dry-run source mutations=0;
- Owner approval exacta;
- final recheck PASS;
- atomic apply exact-path;
- unexpected paths=0;
- Story `CHANGES_READY`;
- operator writes=0;
- terminal escapes=0;
- Full Regression=0;
- D03 no iniciado.
