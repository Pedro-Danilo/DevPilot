---
title: "Auditoría FUNC-SPRINT-41 — PatchSandbox y ChangeSet model"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-41-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-41 — PatchSandbox y ChangeSet model

## 1. Propósito

Validar que `FUNC-SPRINT-41` agrega una zona controlada para probar patches fuera del workspace productivo y representar los cambios resultantes como un `ChangeSet` auditable.

## 2. Estado

Estado: `implemented-initial`.

La capacidad queda implementada como `PatchSandboxManager`, paquete `changes` y comando CLI `patch sandbox`. No habilita aplicación real de patches en el workspace productivo, rollback ejecutable, Git write, refactor execution ni deploy.

## 3. Funcionamiento técnico

El flujo ejecuta:

1. validación de path y lectura del patch file;
2. preflight mediante `PatchPreflightEngine`;
3. validación de política para sandbox runtime;
4. copia del workspace a `outputs/sandbox/<sandbox_id>/workspace` excluyendo `.git`, outputs, caches, virtualenvs y datos runtime;
5. aplicación del patch solo en sandbox mediante `SafeSubprocessRunner` y allowlist runtime;
6. cálculo de hashes antes/después para archivos afectados;
7. generación de `ChangeSet` serializable;
8. verificación de que el workspace productivo permanece sin cambios;
9. ejecución opcional de pruebas de sandbox solo si existe aprobación `tests.run` válida.

## 4. Integración con DevPilot

La implementación se integra con:

- `PatchPreflightEngine`;
- `PatchReviewEngine`;
- `PolicyEngine`;
- `PathGuard`;
- `SecretGuard`;
- `SafeSubprocessRunner`;
- `ReportEngine`;
- `ApprovalPolicyChecker` para pruebas opcionales;
- MIASI Tool Registry y Policy Matrix.

## 5. Rol dentro de DevPilot

`patch sandbox` es la transición entre preflight dry-run y futuros flujos de rollback/refactor controlado. Su rol es validar cambios en una copia local aislada y producir evidencia verificable antes de tocar el repositorio real.

## 6. Criterios PASS

- `patch sandbox --patch-file ... --json` devuelve `CommandResult` parseable.
- El patch se aplica únicamente dentro de `outputs/sandbox`.
- El workspace productivo permanece intacto.
- Se genera `ChangeSet` con archivos, acciones, hashes y tamaños.
- `ChangeSet` no contiene contenido crudo de patch ni secretos.
- `--write-report` genera evidencia JSON/Markdown.
- `--cleanup` remueve el sandbox runtime.
- MIASI declara `patch.sandbox` y `PATCH_SANDBOX_RUNTIME_ALLOW`.

## 7. Criterios BLOCK

- El sandbox modifica archivos productivos.
- Se omite `PatchPreflightEngine`.
- Se intenta ejecutar pruebas sin aprobación `tests.run`.
- El patch no produce `ChangeSet`.
- Se escribe fuera de `outputs/sandbox`.
- Se habilita rollback ejecutable, Git write, refactor execution o deploy.

## 8. Riesgos

- El sandbox es una copia local y puede excluir archivos runtime necesarios para ciertas pruebas.
- Patches grandes pueden consumir espacio local.
- La aplicación exitosa en sandbox no certifica corrección semántica.
- El rollback ejecutable no existe todavía; solo se emite preview preliminar.

## 9. Veredicto

`FUNC-SPRINT-41` queda aprobado como primera versión de PatchSandbox y ChangeSet. La capacidad es local-first, controlada y preliminar; deberá evolucionar en `FUNC-SPRINT-42` hacia RollbackManager y backup local controlado sin romper la regla de no modificar el workspace productivo sin cadena completa de política, aprobación, sandbox, tests y rollback.
