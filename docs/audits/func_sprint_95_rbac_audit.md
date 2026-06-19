---
title: "Auditoría FUNC-SPRINT-95 — RBAC local y modelo de identidad"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-95"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-19"
sprint: "FUNC-SPRINT-95"
phase: "FASE-H-CAPACIDADES-AVANZADAS"
approval: "implemented_initial_local_rbac"
---

# Auditoría FUNC-SPRINT-95 — RBAC local y modelo de identidad

## Estado

`implemented-initial`. El sprint crea un modelo local de identidad/RBAC sin SaaS, sin autenticación remota, sin sesiones persistentes, sin passwords, sin tokens y sin proveedor externo de identidad.

## Propósito

Agregar una capa local de actores, roles y permisos para que DevPilot no dependa únicamente de comandos o aprobaciones anónimas cuando evalúa acciones sensibles. La capacidad está orientada a proteger UI/API futura, PolicyEngine, Approval Workflow y operaciones multiworkspace.

## Alcance implementado

- Identity Registry local en `.devpilot/identity/identity_registry.json`.
- Schema formal `SCHEMA-DEVPL-IDENTITY-REGISTRY-V1`.
- Roles mínimos: `owner`, `architect`, `developer`, `reviewer`, `operator`, `agent-supervisor`.
- Actor local activo `local-owner` y alias compatible `owner`.
- CLI `identity current`, `identity roles`, `identity check`.
- Integración RBAC con `PolicyEngine` para acciones sensibles y approval-gated.
- Integración con `ApprovalService` para bloquear aprobaciones críticas sin actor autorizado.
- Suite safety `identity-rbac` consumida por `quality-gate ci`.

## Funcionamiento

`IdentityRegistry` carga el registry local, valida schema y roles obligatorios, resuelve el actor activo y calcula permisos. `PolicyEngine` consulta RBAC cuando una acción es sensible o requiere aprobación. `ApprovalService` consulta RBAC antes de aprobar, denegar o revocar registros de aprobación.

## Integración

La integración pasa por:

```text
IdentityRegistry → RBAC → PolicyEngine → ApprovalPolicyChecker → ApprovalService → MIASI → EvalRunner → QualityGate
```

No se integra con OAuth, SSO, LDAP, cloud identity ni auth remota. Esa evolución requiere ADR futura.

## Criterios PASS

- `identity current` retorna actor local activo.
- `identity roles` contiene los seis roles mínimos.
- `identity check` permite al owner y bloquea actores desconocidos o sin permiso.
- `PolicyEngine` incluye decisión RBAC en acciones sensibles.
- `ApprovalService` bloquea aprobación crítica si el actor no tiene permiso.
- `identity-rbac` alcanza `safety_score >= 90` sin falsos negativos.
- MIASI declara tools y políticas de identidad/RBAC.

## Criterios BLOCK

- Roles decorativos sin enforcement.
- Aprobaciones críticas sin actor.
- Actor desconocido autorizado.
- Auth remota habilitada.
- Credenciales almacenadas en registry.
- Quality Gate no consume suite `identity-rbac`.

## Riesgos

- Es una primera versión local y determinística, no un IAM completo.
- No hay sesiones, expiración de sesión, MFA, SSO ni multiusuario real.
- El alias `owner` se conserva por compatibilidad con pruebas y aprobaciones históricas.
- Los permisos son coarse-grained; RBAC granular por workspace/API/UI debe evolucionar en sprints posteriores.

## Comandos de verificación

```powershell
python -m devpilot_core identity current --json
python -m devpilot_core identity roles --json
python -m devpilot_core identity check --actor local-owner --action execute --tool tests.run --subject pytest --json
python -m devpilot_core eval run --suite identity-rbac --json
python -m devpilot_core quality-gate run --profile ci --json
```

## Veredicto

Sprint 95 queda implementado como primera versión gobernada de identidad local y RBAC. Es suficiente para bloquear aprobaciones críticas sin actor y para preparar UI/API futura, pero debe evolucionar antes de colaboración real o uso multiusuario.
