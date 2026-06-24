---
title: "POST-H-004-C — Approval/RBAC/security guards semantic report"
doc_id: "POST-H-004-C-AUDIT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
sprint: "POST-H-004-C"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# POST-H-004-C — Approval/RBAC/security guards semantic report

## 1. Propósito

Documentar la implementación de `POST-H-004-C`, que amplía `miasi semantic-validate` con reglas declarativas para aprobación humana local, RBAC, identidad y security guards sobre herramientas y reglas MIASI sensibles.

## 2. Estado

`implemented-initial`.

La entrega es una primera versión de hardening semántico. No declara madurez `production-ready-local` y no sustituye `PolicyEngine` ni el flujo real de aprobación en runtime.

## 3. Alcance implementado

```text
- Cruce de tools sensibles con approval metadata.
- Bloqueo de approvals genéricos en herramientas sensibles.
- Validación de Identity Registry local.
- Validación de deny_unknown_actor y RBAC enforced para acciones sensibles.
- Validación de actor local activo y roles conocidos.
- Validación de permisos RBAC de aprobación/acciones críticas.
- Validación de CostGuard/NoExternalAPI/NoNetwork/LocalhostOnly para network_cost.
- Validación de guards locales para write-capable tools.
- Validación de no-go guards para remote/plugin/connector write o execute.
```

## 4. Funcionamiento

El comando sigue siendo:

```powershell
python -m devpilot_core miasi semantic-validate --json
```

La ejecución es local, dry-run y read-only. El validador carga los registros declarativos MIASI y, adicionalmente, `.devpilot/identity/identity_registry.json` para revisar RBAC e identidad local. Después emite un `MiasiSemanticReport` validable por `SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1`.

## 5. Criterios PASS

```text
PASS si el bundle MIASI vigente no tiene findings error/block.
PASS si el reporte conserva dry_run=true y flags de red/API/mutación en false.
PASS si fixtures inseguros fallan con BLOCK.
PASS si Identity Registry existe y aplica RBAC/deny_unknown_actor.
PASS si no-go paths remote/plugin/connector write/execute no quedan allow prematuros.
```

## 6. Criterios BLOCK

```text
BLOCK si falta Identity Registry.
BLOCK si RBAC para acciones sensibles está desactivado.
BLOCK si unknown actor no está denegado.
BLOCK si approval requerido se expresa como aprobación genérica sin tool/action/subject o checker concreto.
BLOCK si network_cost carece de CostGuard/NoExternalAPI/NoNetwork/LocalhostOnly.
BLOCK si connector.write/plugin.execute/remote.execute queda allow sin futuro ADR/sandbox/test-contract guard.
```

## 7. Riesgos residuales

```text
- Las warnings actuales sobre controlled_write high-risk son deuda técnica semántica, no autorización de producción.
- No se cruzan todavía observability, evals ni test contracts.
- No hay integración de semantic-validate como subgate de quality-gate hasta POST-H-004-E.
```

## 8. No-go gates conservados

```text
No se ejecutan agentes.
No se ejecutan tools.
No se ejecuta pytest desde JSON.
No se habilita remote execution.
No se habilita connector write.
No se habilita plugin execution.
No se llama red ni APIs externas.
No se mutan fuentes.
```

## 9. Validación recomendada

```powershell
python -m pytest tests/test_miasi_semantic_validator.py tests/test_miasi_semantic_validator_fixtures.py tests/test_miasi_semantic_report_model.py tests/test_miasi_registry.py tests/test_schema_registry.py -q
python -m devpilot_core miasi semantic-validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Próximo paso

`POST-H-004-D — Observability, evals y test contracts` debe cruzar las capacidades high-risk con observability, red-team fixtures, safety evals y Test Contract Registry v1/v2.
