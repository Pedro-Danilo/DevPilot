---
doc_id: "POST-H-EVAL-002-01-D-SPRINT7-IMPLEMENTATION-GUIDE"
title: "POST-H-EVAL-002-01-D — Sprint 7: recuperación v2.1.1 y reanudación de la verificación 326 → 327"
status: "approved"
version: "2.1.1"
owner: "Ordóñez"
updated: "2026-07-31"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002-01-D"
source_repo: "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE_GIT.zip"
target_repo: "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
implementation_strategy: "recovery-on-top-of-v2.1.0-patch-applied"
local_first: true
dry_run_first: true
functional_code_changed: false
remote_execution_enabled: false
connector_write_enabled: false
plugin_execution_enabled: false
---

# POST-H-EVAL-002-01-D — Sprint 7: recuperación v2.1.1 y reanudación de la verificación 326 → 327

## 1. Decisión operativa

Esta guía sustituye la etapa de recuperación posterior al bloqueo de `Validate` v2.1.0. El estado de entrada obligatorio es:

```text
Preflight v2.1.0 = PASS
Apply v2.1.0 = PASS
repo_state = PATCH_APPLIED
full pytest v2.1.0 = 1985 passed, 1 failed, 0 errors, 0 skipped
único fallo = test_closure_state_and_backlog_are_administratively_closed
```

**No vuelva a ejecutar Apply v2.1.0.** No restaure el backup y no copie manualmente el repo 327. El repositorio oficial debe conservar las 29 rutas ya aplicadas y recibir únicamente el correctivo v2.1.1.

## 2. Causa confirmada

El cierre 327 actualizó correctamente:

```text
current_phase = POST-H-EVAL-002
current_micro_sprint = POST-H-EVAL-002-02-A
next_micro_sprint = POST-H-EVAL-002-02-B
```

El contrato histórico `tests/test_post_h_034_closure_regression_reconciliation.py` todavía restringía `current_micro_sprint` a `01-A`, `01-B`, `01-C` o `01-D`. Esa aserción dejó de representar el roadmap aprobado cuando el Sprint 7 cerró backlog 01 y autorizó `02-A`.

El defecto no está en `project_state`: el contrato focal 327, Project State, evidencia 47/47 y los no-go gates validaron `02-A`. El defecto está en la sincronización del contrato histórico y en la selección focal v2.1.0, que no ejecutó ese archivo antes de la regresión completa.

## 3. Alcance exacto v2.1.1

Estado final acumulado respecto de repo 326:

```text
25 archivos modificados
5 archivos nuevos
30 rutas totales
0 archivos eliminados
0 archivos funcionales bajo src/ o ui/
```

El recovery v2.1.1 modifica solo archivos ya gobernados y el contrato histórico omitido. No cambia producto, API, UI, dependencias, schemas runtime, evidencias browser ni no-go gates.

## 4. Rutas canónicas

```text
Repo oficial: D:\Projects\DevPilot_Local
Raíz de evaluación: D:\Projects\DevPilot_E2E_Evaluation
Operador: D:\Projects\DevPilot_E2E_Evaluation\deliverables\sprint7egression_contract_recovery_v2_1_1
```

No use `D:\Projects\DevPilot_E2E_Evaluation_RUN06`.

## 5. Archivos que debe conservar antes de continuar

```text
D:\Projects\DevPilot_E2E_Evaluation\control\sprint7_direct_preflight_v210.json
D:\Projects\DevPilot_E2E_Evaluation\control\sprint7_direct_apply_v210.json
D:\Projects\DevPilot_E2E_Evaluation\control\sprint7_direct_validate_v210.json
D:\Projects\DevPilot_E2E_Evaluation\evidence\sprint7_326_327_direct_v210
_full_pytest.junit.xml
D:\Projects\DevPilot_E2E_Evaluation\evidence\sprint7_326_327_direct_v210
_full_pytest.log
```

El JUnit v2.1.0 no es necesario para corregir el archivo, pero sí es la evidencia machine-readable recomendada del bloqueo y permite auditar que el único fallo fue el contrato aquí corregido.

## 6. Extraer y autoprobar el paquete

Extraiga el ZIP en una carpeta nueva y ejecute:

```powershell
Set-Location -LiteralPath "D:\Projects\DevPilot_E2E_Evaluation\deliverables\sprint7egression_contract_recovery_v2_1_1"
```

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

```powershell
py -3 ".\Test-SPRINT7-Regression-Contract-Recovery-v2.1.1.py"; if($LASTEXITCODE -ne 0){throw "BLOCK: autoprueba recovery v2.1.1"}
```

PASS esperado:

```text
package_integrity=PASS
base_v210_state_fixture=PASS
stale_contract_detection=PASS
corrected_contract_detection=PASS
real_drift_block=PASS
```

## 7. Preflight de recuperación

```powershell
.\Invoke-SPRINT7-Regression-Contract-Recovery-v2.1.1.ps1 -Mode Preflight
```

PASS obligatorio:

```text
repo_state = PATCH_APPLIED_V210
expected_current_paths = 29
unexpected_paths = 0
recovery_files = 9
next_action = apply-recovery
```

BLOCK si una de las 29 rutas v2.1.0 no coincide, si existe una ruta Git adicional o si el contrato histórico ya fue editado manualmente.

## 8. Aplicar v2.1.1

```powershell
.\Invoke-SPRINT7-Regression-Contract-Recovery-v2.1.1.ps1 -Mode Apply
```

PASS esperado:

```text
repo_state = PATCH_APPLIED_V211
files_recovered = 9
expected_final_paths = 30
unexpected_paths = 0
backup = created
```

El operador crea backup y usa reemplazo atómico. No ejecuta `git add`, commit, push, reset ni clean.

## 9. Gate focal temprano

El modo Validate ejecuta primero el contrato que falló y el gate integrado completo:

```text
test_post_h_034_closure_regression_reconciliation.py
+ test_post_h_eval_002_01_d_governance_closure_327.py
+ test_post_h_eval_002_activation_contract.py
+ test_project_global_state.py
= 51/51 PASS
```

De esta forma un drift de estado histórico se detecta antes de iniciar la regresión general.

## 10. Validación integral

```powershell
.\Invoke-SPRINT7-Regression-Contract-Recovery-v2.1.1.ps1 -Mode Validate
```

El modo Validate debe obtener:

```text
pip check = PASS
evidence preflight = 47/47 PASS
gate focal integrado = 51/51 PASS
project-state = PASS
docs-governance = PASS
TCR v1 = PASS
TCR v2 = PASS
evidence-freshness = PASS
compatibilidad API = 21/21 PASS
collection = 1986
full pytest = 1986 passed, 0 failed, 0 errors, 0 skipped
source mirror integrity = PASS
repo 327 limpio = generado
```

Una ejecución parcial, interrumpida o sin JUnit no equivale a PASS.

## 11. Evidencia de recuperación

El operador escribe bajo:

```text
D:\Projects\DevPilot_E2E_Evaluation\control\sprint7_regression_recovery_*_v211.json
D:\Projects\DevPilot_E2E_Evaluation\evidence\sprint7_326_327_regression_recovery_v211```

Conserve transcript de PowerShell, JSON, JUnit, logs, ZIP repo 327 y sidecar SHA-256.

## 12. Verificación Git antes del commit

```powershell
Set-Location -LiteralPath "D:\Projects\DevPilot_Local"; git status --short
```

Compruebe exactamente las 30 rutas:

```powershell
$Expected=Get-Content -LiteralPath "D:\Projects\DevPilot_E2E_Evaluation\deliverables\sprint7egression_contract_recovery_v2_1_1\EXPECTED_FINAL_PATHS_v2_1_1.txt" | Sort-Object; $Actual=git status --porcelain=v1 --untracked-files=all | ForEach-Object { $_.Substring(3).Replace('','/') } | Sort-Object; $Diff=Compare-Object -ReferenceObject $Expected -DifferenceObject $Actual; if($Diff){$Diff | Format-Table | Out-String | Write-Host; throw "BLOCK: rutas Git diferentes de las 30 esperadas"}; "SPRINT7 GIT PATH SET = PASS"
```

## 13. Integración Git

Solo después de Validate PASS:

```powershell
Set-Location -LiteralPath "D:\Projects\DevPilot_Local"; git add --pathspec-from-file="D:\Projects\DevPilot_E2E_Evaluation\deliverables\sprint7egression_contract_recovery_v2_1_1\EXPECTED_FINAL_PATHS_v2_1_1.txt"; if($LASTEXITCODE -ne 0){throw "BLOCK: git add Sprint 7 v2.1.1"}
```

```powershell
$Expected=Get-Content -LiteralPath "D:\Projects\DevPilot_E2E_Evaluation\deliverables\sprint7egression_contract_recovery_v2_1_1\EXPECTED_FINAL_PATHS_v2_1_1.txt" | Sort-Object; $Actual=git diff --cached --name-only | Sort-Object; $Diff=Compare-Object -ReferenceObject $Expected -DifferenceObject $Actual; if($Diff){$Diff | Format-Table | Out-String | Write-Host; throw "BLOCK: staging no coincide con las 30 rutas"}; "SPRINT7 STAGING = PASS"
```

```powershell
git commit -m "docs(governance): close POST-H-EVAL-002-01-D and advance to 02-A"; if($LASTEXITCODE -ne 0){throw "BLOCK: commit Sprint 7"}
```

No haga push hasta verificar el commit y el ZIP limpio.

## 14. Criterios PASS

```text
Preflight recovery = PASS
Apply recovery = PASS
51/51 focal = PASS
5/5 validadores = PASS
21/21 compatibilidad = PASS
1986/1986 full regression = PASS
30/30 rutas Git exactas
functional delta = 0
S0 = 0
S1 = 0
no-go gates intactos
repo 327 ZIP y SHA-256 generados
```

## 15. Criterios BLOCK

- estado distinto de `PATCH_APPLIED_V210` antes del recovery;
- cualquier ruta Git fuera de las 29 previas o 30 finales;
- modificación manual del contrato histórico;
- gate focal distinto de 51/51;
- colección distinta de 1986;
- cualquier fallo de pytest o validador;
- inclusión de `.git`, `.venv`, `outputs`, caches, SQLite runtime, HAR bruto, token o secretos;
- activación de remote execution, connector write, plugin execution o APIs externas.

## 16. Evidencia adicional opcional para auditoría remota

Para auditar el bloqueo sin volver a interpretar el transcript, adjunte:

```text
12_full_pytest.junit.xml
12_full_pytest.log
11_collection.log
mirror_source_manifest_before.json
```

No son necesarios para diagnosticar la causa ya confirmada, pero sí fortalecen la trazabilidad machine-readable del intento v2.1.0.
