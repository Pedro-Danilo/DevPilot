---
title: "Reporte de cierre Fase B — Seguridad operacional"
doc_id: "DEVPL-AUDIT-PHASE-B-CLOSURE-001"
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

# Reporte de cierre Fase B — Seguridad operacional

## 1. Propósito

Cerrar formalmente la Fase B de DevPilot Local, consolidando las capacidades de seguridad operacional implementadas entre `FUNC-SPRINT-28` y `FUNC-SPRINT-34`.

## 2. Estado

Estado: `approved`.

La Fase B queda cerrada como **baseline local-first de seguridad operacional implemented-initial**. Es suficiente para avanzar hacia Fase C, pero no debe presentarse como seguridad industrial completa.

## 3. Alcance consolidado

| Sprint | Capacidad | Estado |
|---|---|---|
| FUNC-SPRINT-28 | Modelo de aprobación humana y persistencia operacional | Implementado |
| FUNC-SPRINT-29 | CLI approval request/list/show/approve/deny/revoke | Implementado |
| FUNC-SPRINT-30 | Binding de approvals con `PolicyEngine` y MIASI | Implementado |
| FUNC-SPRINT-31 | `SafeSubprocessRunner` y allowlist | Implementado |
| FUNC-SPRINT-32 | `tests.run` como herramienta MIASI controlada | Implementado-initial |
| FUNC-SPRINT-33 | Hardening de SecretGuard y prompt/tool injection guards | Implementado-initial |
| FUNC-SPRINT-34 | Security readiness y cierre Fase B | Implementado-initial |

## 4. Funcionamiento técnico

El cierre de Fase B queda gobernado por esta cadena:

```text
approval request/approve
→ ApprovalStore SQLite
→ ApprovalPolicyChecker
→ PolicyEngine
→ SafeSubprocessRunner
→ tests.run
→ SecretGuard / PromptInjectionGuard / ToolInjectionGuard
→ EventLogger / ReportEngine / LocalStore
→ security readiness
```

`security readiness` usa un workspace temporal aislado para verificar approval workflow, policy binding y smoke execution sin mutar la base de datos del proyecto. Los reportes del comando sí se escriben bajo `outputs/reports/` cuando se solicita `--write-report`.

## 5. Evidencia esperada

Comandos de cierre:

```powershell
python -m devpilot_core security readiness --json --write-report
python -m devpilot_core policy simulate --matrix standard --json --write-report
python -m devpilot_core miasi validate --json
python -m devpilot_core validate all --json
python -m pytest -q
```

Evidencia documental:

- `docs/checklists/checklist_phase_b_exit.md`;
- `docs/audits/phase_b_operational_security_closure_report.md`;
- `docs/functional_sprint_34_manifest.json`;
- `docs/devpilot_backlog_fase_B_seguridad_operacional.md` actualizado;
- `README.md` y `docs/05_operations/runbook.md` sincronizados.

## 6. Criterios PASS

- Approval Workflow funcional.
- Approval binding válido con scope y expiración.
- Missing/wrong/expired approvals bloquean.
- `tests.run` ejecuta solo perfiles allowlisted con approval válida.
- Secret/prompt/tool injection guards bloquean payloads sintéticos.
- MIASI y contratos validan.
- No hay patch apply/refactor execution/Git write/deploy habilitados.
- `pytest -q` en PASS.

## 7. Criterios BLOCK

- `tests.run` ejecuta sin approval válida.
- Se permite comando arbitrario o `shell=True`.
- Se expone secreto crudo en evidencias.
- Faltan checklist, closure report o manifest.
- Algún gate de `security readiness` falla.
- Se habilita una acción destructiva antes de sandbox/rollback.

## 8. Riesgos y límites

La Fase B no reemplaza:

- sandbox real;
- rollback automático;
- SAST/SCA industrial;
- secret scanning profesional;
- RBAC/autenticación;
- observabilidad distribuida;
- CI/CD formal;
- aprobación humana multiusuario.

## 9. Próxima fase

La continuidad recomendada es Fase C: ingeniería de repositorio y sandbox controlado. Antes de permitir `patch apply`, refactor execution o Git write, DevPilot debe implementar sandbox/rollback, policy gates más estrictos y trazabilidad operacional v2.

## 10. Veredicto

Fase B puede cerrarse si `FUNC-SPRINT-34` mantiene en PASS `security readiness`, `policy simulate --matrix standard`, MIASI, `validate all` y la regresión completa.

## Nota de hardening FUNC-SPRINT-34

Durante el cierre se agregó un control defensivo en `SafeSubprocessRunner`: cuando el comando allowlisted corresponde a pytest, el subprocess se ejecuta con `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` y `PYTHONNOUSERSITE=1`. Este ajuste no cambia el contrato funcional de `tests.run`, pero evita que plugins externos instalados en el host se comporten como dependencias implícitas no gobernadas.
