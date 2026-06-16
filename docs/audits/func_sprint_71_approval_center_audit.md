---
doc_id: "AUDIT-FUNC-SPRINT-71-APPROVAL-CENTER"
title: "Auditoría FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI"
status: approved
version: "1.0.0"
updated: "2026-06-16"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-71"
approval: "approved-for-local-mvp"
---

# Auditoría FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI

## 0. Estado

Veredicto: `PASS`.

## 1. Propósito

Exponer aprobación humana local y acciones dry-run seguras desde Web UI, sin habilitar ejecución destructiva desde frontend.

## 2. Alcance implementado

- Endpoints `/api/v1/approvals` para list/show/request/approve/deny.
- Endpoint `/api/v1/actions/dry-run` para readiness, code-review y refactor-plan.
- Approval Center visual.
- Action Launcher dry-run.
- Binding con PolicyEngine para bloquear acciones críticas.

## 3. Funcionamiento técnico

La API enruta requests hacia `ApplicationService`; los route handlers no importan engines internos. Approval Center usa `ApprovalApplicationService`, que delega en `ApprovalService`/`ApprovalStore`. Action Launcher evalúa PolicyEngine y solo ejecuta acciones read-only/dry-run.

## 4. Archivos creados

- `src/devpilot_core/application/approval_service.py`
- `src/devpilot_core/interfaces/api/routers/approvals.py`
- `ui/web/src/pages/ApprovalCenterView.ts`
- `ui/web/src/components/DryRunActionForm.ts`
- `tests/test_api_approvals_actions.py`
- `tests/test_web_ui_approval_center.py`
- `tests/test_sprint_71_documentation.py`

## 5. Archivos modificados

Se actualizaron `ApplicationService`, API security bindings, OpenAPI, Web UI, README, runbook, backlog Fase F, functional backlog y pruebas documentales acumulativas.

## 6. Criterios PASS

- UI puede ver y gestionar approvals locales.
- Acciones UI son dry-run.
- Acciones críticas quedan bloqueadas desde UI.
- API exige token y policy binding.
- No se accede al filesystem desde frontend.

## 7. Criterios BLOCK

- No cerrar si la UI ejecuta patch apply, refactor execute, rollback execute, git push o deploy.
- No cerrar si falta auditoría.
- No cerrar si se exponen tokens o secretos.

## 8. Riesgos y limitaciones

Esta es una primera versión: no hay RBAC multiusuario, sesiones por usuario, colas de aprobación colaborativas ni ejecución productiva desde frontend. Las aprobaciones son locales sobre SQLite y dependen del token local de API.

## 9. Comandos de verificación

```powershell
python -m pytest tests/test_api_approvals_actions.py tests/test_web_ui_approval_center.py tests/test_sprint_71_documentation.py -q
cd ui/web
npm test
python -m devpilot_core validate all --json
```

## 10. Conclusión

Sprint 71 queda implementado como MVP local seguro y preliminar, adecuado para avanzar a Settings UI en Sprint 72.
