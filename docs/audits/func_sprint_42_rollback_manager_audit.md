---
title: "Auditoría FUNC-SPRINT-42 — RollbackManager y backup local controlado"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-42-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-12"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-42 — RollbackManager y backup local controlado

## 1. Propósito

Validar que `FUNC-SPRINT-42` incorpora una primera capacidad local de rollback y backup a partir de `ChangeSet` generados por sandbox, sin habilitar restauración automática ni mutación libre del workspace productivo.

## 2. Estado

Estado: `implemented-initial`.

La capacidad queda implementada como `RollbackManager`, modelos `RollbackPlan`, `RollbackPoint` y `RollbackOperation`, y comandos CLI `rollback plan`, `rollback list`, `rollback show` y `rollback execute`. `rollback execute` existe como frontera gated y no-mutating en esta versión inicial.

## 3. Funcionamiento técnico

El flujo ejecuta:

1. lectura local de un `ChangeSet` JSON;
2. validación estructural mínima;
3. validación de rutas dentro del workspace;
4. cálculo de operaciones de rollback por archivo;
5. backup local controlado bajo `.devpilot/rollback/backups/<rollback_id>/`;
6. bloqueo de backup cuando `SecretGuard` detecta secretos;
7. persistencia de rollback point bajo `.devpilot/rollback/points/<rollback_id>.json`;
8. listado y consulta read-only de rollback points;
9. bloqueo de `rollback execute` sin aprobación y sin restauración real en Sprint 42.

## 4. Integración con DevPilot

La implementación se integra con:

- `ChangeSet` generado por `PatchSandboxManager`;
- `PolicyEngine` para lectura y ejecución gated;
- `SecretGuard` para evitar backup de secretos detectables;
- `LocalStore` mediante eventos best-effort;
- `ReportEngine` para evidencia con `--write-report`;
- MIASI Tool Registry y Policy Matrix.

## 5. Rol dentro de DevPilot

`RollbackManager` prepara el paso de sandbox hacia flujos futuros de refactor/patch controlados. Su rol es proporcionar evidencia previa, puntos de recuperación y metadata auditable antes de cualquier ejecución real.

## 6. Criterios PASS

- `rollback plan --changeset-file ... --json` genera `CommandResult` parseable.
- Los planes son serializables y auditables.
- Los backups se guardan solo bajo `.devpilot/rollback/`.
- `rollback list` y `rollback show` son read-only.
- `rollback execute` no ejecuta restauración real sin aprobación ni semántica futura.
- `.devpilot/rollback/` está excluido de Git/release ZIPs.
- MIASI declara tools y policy rules de rollback.

## 7. Criterios BLOCK

- El changeset apunta fuera del workspace.
- El backup intenta copiar secretos detectables.
- El backup intenta operar sobre rutas runtime/cache bloqueadas.
- `rollback execute` se invoca sin aprobación válida.
- Se habilita restauración automática, Git write, deploy o refactor execution fuera del alcance del sprint.

## 8. Riesgos

- El rollback inicial es metadata/backup local, no rollback transaccional completo.
- Los backups pueden ocupar espacio local.
- Los archivos con secretos detectables se bloquean y requieren revisión humana.
- La restauración ejecutable queda para evolución futura con pruebas y aprobación estricta.

## 9. Veredicto

`FUNC-SPRINT-42` puede considerarse implementado como primera versión controlada de rollback/backup local. No debe interpretarse como rollback productivo completo ni como autorización para aplicar cambios reales al workspace productivo.
