---
title: "Auditoría FUNC-SPRINT-30 — Binding de aprobaciones con PolicyEngine y MIASI"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-30-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-30"
updated: "2026-06-11"
approval: "approved_by_owner"
---

# Auditoría FUNC-SPRINT-30 — Binding de aprobaciones con PolicyEngine y MIASI

## 1. Propósito

Documentar la implementación del binding inicial entre el workflow local de aprobaciones humanas, `PolicyEngine` y los contratos MIASI. El objetivo es que una acción approval-gated pueda evaluarse con `approval_id` válido sin convertir la aprobación en un bypass global.

## 2. Estado

Estado: `implemented-initial`.

El sprint implementa evaluación de política y simulación. No ejecuta herramientas, no corre tests, no aplica patches, no realiza refactor execution, no hace deploy y no habilita Git write.

## 3. Funcionamiento técnico

`PolicyRequest` ahora acepta `approval_id`, `tool_id` y `subject`. `ApprovalPolicyChecker` carga la approval desde `ApprovalStore`, verifica que exista, que esté en estado `approved`, que no esté expirada y que su scope cubra `tool_id`, `action` y `subject`.

`PolicyEngine` conserva `PathGuard`, `SecretGuard` y `CostGuard`. Una approval válida solo satisface el gate humano del scope autorizado; no desactiva otras guardas.

## 4. Integración con DevPilot

Archivos principales:

- `src/devpilot_core/approval/policy.py`;
- `src/devpilot_core/policy/engine.py`;
- `src/devpilot_core/policy/decisions.py`;
- `src/devpilot_core/cli.py`;
- `.devpilot/miasi/policy_matrix.json`;
- `docs/06_miasi/policy_matrix.md`.

El comando `policy simulate` permite validar casos con y sin approval antes de implementar ejecución controlada.

## 5. Comandos de uso

```powershell
$env:PYTHONPATH="src"
$approval = python -m devpilot_core approval request --tool tests.run --action execute --subject pytest --reason "Validar cambios" --actor owner --json | ConvertFrom-Json
$approvalId = $approval.data.approval.approval_id
python -m devpilot_core approval approve $approvalId --actor owner --reason "Revisión OK" --json
python -m devpilot_core policy check execute --path . --tool tests.run --subject pytest --approval-id $approvalId --json
python -m devpilot_core policy simulate --tool tests.run --action execute --subject pytest --approval-id $approvalId --json --write-report
python -m pytest tests/test_approval_policy_binding.py -q
```

## 6. Criterios PASS

```text
Acción approval-gated sin approval_id produce BLOCK.
Approval expirada produce BLOCK.
Approval no aprobada produce BLOCK.
Approval de otra tool/action/subject produce BLOCK.
Approval válida solo habilita el scope declarado.
MIASI validate sigue en PASS.
pytest -q pasa.
```

## 7. Criterios BLOCK

```text
Approval funciona como bypass global.
Una approval válida para tests.run permite patch apply o deploy.
PolicyEngine ignora expiración.
MIASI queda desincronizado.
Se ejecuta una herramienta real desde este sprint.
```

## 8. Riesgos

- `actor` sigue siendo declarativo/local, sin RBAC.
- El binding es determinístico y local; no sustituye revisión humana real en equipos.
- Las simulaciones no ejecutan comandos; SafeSubprocessRunner queda para `FUNC-SPRINT-31`.
- `tests.run` queda pendiente hasta `FUNC-SPRINT-32`.

## 9. Veredicto

`FUNC-SPRINT-30` queda listo para validación como primera versión del binding Approval Workflow + PolicyEngine + MIASI. La evolución natural es `FUNC-SPRINT-31 — SafeSubprocessRunner y allowlist de ejecución controlada`.
