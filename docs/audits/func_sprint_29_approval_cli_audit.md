---
title: "Auditoría FUNC-SPRINT-29 — CLI de aprobación local"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-29-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-B-SEGURIDAD-OPERACIONAL"
sprint: "FUNC-SPRINT-29"
---

# Auditoría FUNC-SPRINT-29 — CLI de aprobación local

## 1. Propósito

Documentar la implementación de `FUNC-SPRINT-29 — CLI de aprobación: request, list, show, approve, deny y revoke`.

El sprint convierte el dominio de aprobación humana creado en Sprint 28 en una interfaz CLI operable, local, auditable y no destructiva. La implementación es **implemented-initial**: permite gestionar registros de aprobación, pero no autoriza todavía ejecución de herramientas críticas.

## 2. Estado

`FUNC-SPRINT-29` queda implementado como primera versión del workflow CLI de aprobaciones humanas.

Estado técnico: `implemented-initial`.

Siguiente sprint: `FUNC-SPRINT-30 — Binding de aprobaciones con PolicyEngine y MIASI`.

## 3. Funcionamiento técnico

El sprint agrega `ApprovalService` como frontera de aplicación entre `cli.py` y `ApprovalStore`.

Flujo principal:

```text
CLI approval request
  -> ApprovalService
  -> ApprovalRequest
  -> ApprovalStore
  -> LocalStore SQLite approvals
  -> EventLogger JSONL + SQLite events
  -> CommandResult
```

Los comandos implementados son:

```powershell
python -m devpilot_core approval request --tool tests.run --action execute --subject pytest --reason "Validar cambios" --actor owner --json
python -m devpilot_core approval list --status requested --json
python -m devpilot_core approval show <approval_id> --json
python -m devpilot_core approval approve <approval_id> --actor owner --reason "Revisión OK" --json
python -m devpilot_core approval deny <approval_id> --actor owner --reason "Riesgo no mitigado" --json
python -m devpilot_core approval revoke <approval_id> --actor owner --reason "Ya no aplica" --json
```

`approval request` deriva un scope mínimo desde `tool`, `action` y `subject`. Si se entrega `--scope`, debe ser JSON object. Si no se entrega `--expires-at`, se usa `--ttl-minutes`, por defecto 60 minutos.

## 4. Integración con DevPilot

Archivos principales:

- `src/devpilot_core/approval/service.py`: servicio CLI-facing.
- `src/devpilot_core/approval/store.py`: reglas de transición y persistencia.
- `src/devpilot_core/cli.py`: comandos `approval ...`.
- `src/devpilot_core/store/local_store.py`: persistencia SQLite existente.
- `docs/devpilot_backlog_fase_B_seguridad_operacional.md`: continuidad Fase B.

El sprint no modifica MIASI Tool Registry ni Policy Matrix porque no cambia aún autorización de tools. Esa sincronización corresponde a Sprint 30.

## 5. Comandos de uso

Verificación general:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q
python -m devpilot_core validate all --json
python -m devpilot_core miasi validate --json
```

Verificación específica:

```powershell
python -m devpilot_core approval request --tool tests.run --action execute --subject pytest --reason "Validar cambios" --actor owner --json
python -m devpilot_core approval list --status requested --json
python -m devpilot_core approval show <approval_id> --json
python -m devpilot_core approval approve <approval_id> --actor owner --reason "Revisión OK" --json
python -m devpilot_core approval deny <approval_id> --actor owner --reason "Riesgo no mitigado" --json
python -m devpilot_core approval revoke <approval_id> --actor owner --reason "Ya no aplica" --json
python -m pytest tests/test_approval_cli.py -q
```

## 6. Criterios PASS

```text
Todos los comandos approval devuelven CommandResult.
approval request crea ApprovalRecord en estado requested.
approval list filtra por status/tool/action.
approval show consulta por approval_id.
approval approve/deny/revoke exige actor y reason.
No se aprueban approvals expiradas.
No se reabren approvals denied/revoked/expired.
Se generan eventos JSONL/SQLite y reportes opcionales.
La salida CLI redacciona secretos sintéticos.
pytest -q pasa.
```

## 7. Criterios BLOCK

```text
Una approval se aprueba sin razón.
Una approval expirada se aprueba.
Una approval denied/revoked/expired se reabre.
La CLI imprime secretos crudos.
La CLI se presenta como autorización automática de ejecución.
```

## 8. Riesgos

- `actor` es local/declarativo y no autentica identidad real.
- `approval_id` todavía no participa en decisiones de `PolicyEngine`.
- No hay RBAC ni Approval Center visual.
- No se ejecutan acciones críticas.
- Las decisiones quedan persistidas localmente; privacidad y retención avanzada quedan para fases posteriores.

## 9. Veredicto

`FUNC-SPRINT-29` queda aprobado como primera versión operativa del CLI de aprobaciones humanas.

La capacidad habilita operación local del workflow de approvals, pero no debe usarse como bypass de política ni como autorización final hasta que `FUNC-SPRINT-30` integre `approval_id` con `PolicyEngine` y MIASI.
