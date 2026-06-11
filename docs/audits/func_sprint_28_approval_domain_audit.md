---
title: "Auditoría FUNC-SPRINT-28 — Modelo de aprobación humana y persistencia operacional"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-28-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-10"
approval: "approved_by_owner_direction"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-28"
---

# Auditoría FUNC-SPRINT-28 — Modelo de aprobación humana y persistencia operacional

## 1. Propósito

Este documento audita la implementación de `FUNC-SPRINT-28 — Modelo de aprobación humana y persistencia operacional`, primer sprint de la Fase B de seguridad operacional.

El objetivo del sprint es crear el dominio de aprobaciones humanas y fortalecer la persistencia local de approvals como flujo operativo. Esta versión es `implemented-initial`: modela y persiste approvals, pero no autoriza todavía acciones críticas ni integra `approval_id` con `PolicyEngine`.

## 2. Estado

Veredicto: `implemented-initial`.

Fase: `FASE-B-SEGURIDAD-OPERACIONAL`.

Siguiente sprint: `FUNC-SPRINT-29 — CLI de aprobación: request, list, show, approve, deny y revoke`.

## 3. Funcionamiento técnico

El sprint introduce el paquete `src/devpilot_core/approval/` con tres modelos principales:

- `ApprovalRequest`: entrada validada para solicitar aprobación local;
- `ApprovalRecord`: registro persistido con ID, subject, tool/action, estado, actor, razón, scope, timestamps y expiración;
- `ApprovalDecision`: transición controlada de estado.

La persistencia se implementa mediante `ApprovalStore`, que opera sobre `LocalStore`. `LocalStore` migra la tabla `approvals` a `0002_approval_operational_v1` de forma idempotente y compatible con la tabla antigua creada en Sprint 10.

## 4. Integración con DevPilot

La integración se limita a persistencia y eventos:

- `LocalStore` crea, lista, obtiene y actualiza approvals;
- `ApprovalStore` emite eventos JSONL y eventos SQLite best-effort para `approval.requested`, `approval.approved` y `approval.denied`;
- `state init` y `state status` siguen siendo los comandos operativos del sprint.

No se agregó CLI `approval` en este sprint porque el backlog lo asigna a `FUNC-SPRINT-29`.

## 5. Comandos de uso

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m pytest tests/test_approval_store.py -q
python -m pytest -q
```

## 6. Criterios PASS

- `ApprovalRecord` tiene ID único, subject, tool_id, action, status, actor, reason, scope, created_at, updated_at y expires_at.
- `ApprovalRequest` bloquea scope vacío y expiración inválida o pasada.
- `ApprovalDecision` valida estados permitidos.
- `LocalStore` persiste approvals de forma idempotente.
- La migración de `approvals` preserva filas antiguas.
- Una approval aprobada, denegada, revocada o expirada no se sobrescribe mediante transición implícita.
- Las pruebas específicas y la regresión completa pasan.

## 7. Criterios BLOCK

- Una approval se crea sin scope.
- Una approval se crea sin expiración.
- Una approval puede sobrescribirse sin transición controlada.
- La tabla `approvals` rompe una base SQLite existente.
- La implementación habilita ejecución crítica sin policy binding.

## 8. Riesgos

- El actor es declarativo/local; no existe RBAC ni autenticación real.
- Los eventos de approval son best-effort; el endurecimiento de auditoría pertenece a sprints posteriores.
- El approval workflow aún no está conectado con `PolicyEngine`.
- No existe CLI de aprobación hasta `FUNC-SPRINT-29`.

## 9. Veredicto

`FUNC-SPRINT-28` cumple el objetivo de modelar y persistir approvals de forma local, auditada e idempotente. La implementación respeta local-first, no usa red, no requiere API keys, no ejecuta comandos externos y no habilita acciones destructivas.
