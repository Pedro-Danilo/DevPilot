---
title: "Checklist de salida Fase B — Seguridad operacional"
doc_id: "DEVPL-CHECKLIST-PHASE-B-EXIT-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-B-SEGURIDAD-OPERACIONAL"
sprint: "FUNC-SPRINT-34"
approval: "approved_by_owner_direction"
---

# Checklist de salida Fase B — Seguridad operacional

## 1. Propósito

Formalizar el cierre operativo de la Fase B de DevPilot Local. Este checklist verifica que las capacidades de seguridad local implementadas entre `FUNC-SPRINT-28` y `FUNC-SPRINT-34` existen, están probadas y quedan limitadas explícitamente antes de avanzar a Fase C.

## 2. Estado

Estado: `approved`.

La Fase B queda cerrada como **baseline de seguridad operacional local implemented-initial**. No equivale a certificación de seguridad industrial completa ni habilita ejecución destructiva.

## 3. Checklist PASS/BLOCK

| ID | Control | Evidencia esperada | Estado |
|---|---|---|---|
| FB-EXIT-001 | Approval domain model y persistencia SQLite | `ApprovalStore`, tabla `approvals`, tests Sprint 28 | PASS |
| FB-EXIT-002 | CLI approval request/list/show/approve/deny/revoke | `ApprovalService`, comandos Sprint 29 | PASS |
| FB-EXIT-003 | Binding `approval_id` con `PolicyEngine` y MIASI | `ApprovalPolicyChecker`, Sprint 30 | PASS |
| FB-EXIT-004 | Ejecución local controlada | `SafeSubprocessRunner`, allowlist, no shell, timeout | PASS |
| FB-EXIT-005 | `tests.run` como herramienta MIASI controlada | perfiles `smoke/unit/all`, approval-gated | PASS |
| FB-EXIT-006 | Hardening textual de seguridad | `SecretGuard`, `PromptInjectionGuard`, `ToolInjectionGuard` | PASS |
| FB-EXIT-007 | Security readiness operativo | `python -m devpilot_core security readiness --json --write-report` | PASS |
| FB-EXIT-008 | Policy simulation matrix | `python -m devpilot_core policy simulate --matrix standard --json --write-report` | PASS |
| FB-EXIT-009 | Reporte de cierre Fase B | `docs/audits/phase_b_operational_security_closure_report.md` | PASS |
| FB-EXIT-010 | Regresión completa | `python -m pytest -q` | PASS |

## 4. Criterios BLOCK

La Fase B no puede cerrarse si ocurre cualquiera de estos casos:

- una acción approval-gated pasa sin approval válida;
- `tests.run` permite comandos arbitrarios o shell strings;
- aparece un secreto crudo en reportes, trazas o metadata;
- `PromptInjectionGuard` o `ToolInjectionGuard` dejan payloads obvios sin finding;
- MIASI no valida;
- falta este checklist o el closure report;
- se habilita `patch apply`, refactor execution, Git write o deploy.

## 5. Comandos de verificación

```powershell
python -m devpilot_core security readiness --json --write-report
python -m devpilot_core policy simulate --matrix standard --json --write-report
python -m devpilot_core miasi validate --json
python -m pytest -q
```

## 6. Límites explícitos

Fase B cierra seguridad operacional local inicial, pero todavía quedan pendientes para producción industrial:

- no hay sandbox real de ejecución;
- no hay rollback automático;
- no hay patch apply ni refactor execution;
- no hay RBAC/autenticación;
- no hay observabilidad v2 con correlación de runs/tool calls;
- no hay SAST/SCA/secret scanning industrial;
- no hay UI Approval Center;
- hardening multiworkspace.

## 7. Veredicto

`FUNC-SPRINT-34` puede cerrar Fase B si `security readiness`, `policy simulate --matrix standard`, MIASI, manifest Sprint 34, auditoría y `pytest -q` permanecen en PASS.

- [x] `SafeSubprocessRunner` aplica controles de entorno para pytest controlado: desactiva autoload de plugins externos y user site en subprocess.
