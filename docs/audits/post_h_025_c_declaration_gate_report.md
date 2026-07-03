---
doc_id: "POST-H-025-C-DECLARATION-GATE-REPORT"
title: "POST-H-025-C — Declaration gate CLI/API"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-03"
approval: "approved_by_owner"
created_by: "POST-H-025-C"
phase: "POST-FASE-H"
local_first: true
dry_run: true
read_only: true
---

# POST-H-025-C — Declaration gate CLI/API

## Resultado

POST-H-025-C queda implementado como `implemented-initial / declaration-gate-cli-api`.

## Implementacion

Se agrega `ProductionReadyDeclarationGate` en `src/devpilot_core/industrial/production_ready.py`. El gate consume `ProductionReadyEvidenceAggregator`, transforma el modelo intermedio `PASS_CANDIDATE`/`BLOCK_CANDIDATE` en una decision formal de gate `PASS` o `BLOCK`, valida el payload contra `ProductionReadyLocalReport` y expone la operacion por CLI y por `ApplicationService`.

Comando principal:

```powershell
python -m devpilot_core industrial-readiness production-ready-local --json
```

Evidencia runtime opcional:

```powershell
python -m devpilot_core industrial-readiness production-ready-local --json --write-report
```

El reporte se escribe bajo:

```text
outputs/reports/production_ready_local_report.json
outputs/reports/production_ready_local_report.md
```

## Criterio industrial aplicado

El gate es conservador. `PASS` solo ocurre cuando:

```text
blocking_gaps_total=0
score >= minimum_score
passed_hitos_total == required_hitos_total
no_go_gates_passed=true
```

Si falta evidencia requerida blocker, la salida es `BLOCK`, `exit_code=2`, `claims.production_ready_local=false` y cada gap incluye una accion concreta de remediacion.

## Seguridad

POST-H-025-C no llama red, no usa APIs externas, no habilita remote execution, no habilita connector write, no habilita plugin execution y no muta fuentes versionables. La escritura de reportes es opt-in y queda limitada a `outputs/reports`.

El gate mantiene deshabilitados los claims:

```text
enterprise_ready=false
remote_ready=false
compliance_certified=false
saas_ready=false
```

## Limitaciones

Esta primera version no valida claims documentales en README, runbook, changelog ni reportes; esa responsabilidad queda para POST-H-025-D. Tampoco emite el artefacto formal final de declaracion/auditoria; esa responsabilidad queda para POST-H-025-E.
