---
title: "ADR-0007 — Persistencia local con filesystem, SQLite y JSONL"
doc_id: "DEVPL-ADR-0007"
status: "accepted"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-08"
approval: "approved_by_owner_direction"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0007 — Persistencia local con filesystem, SQLite y JSONL

## Estado

Accepted. Implementación inicial SQLite realizada en `FUNC-SPRINT-10`.

## Contexto

DevPilot necesita conservar documentos versionables, reportes, estado de workspaces, resultados de gates, ejecuciones, hallazgos, aprobaciones, trazas, uso de herramientas y eventos de costo. Guardarlo todo solo como Markdown sería insuficiente para operación, consultas y dashboards futuros.

## Decisión

Adoptar una arquitectura de persistencia local mixta: Markdown/YAML/JSON para artefactos versionables, SQLite para estado operativo consultable y JSONL para eventos/trazas append-only.

## Consecuencias positivas

- Mantiene local-first.
- Facilita consultas históricas.
- Prepara dashboards desktop/web.
- Permite auditoría y trazabilidad.
- SQLite no requiere servidor externo.

## Consecuencias negativas / riesgos

- Requiere migraciones de schema.
- Puede generar archivos locales no versionables.
- Necesita política clara de retención y redacción.

## Controles obligatorios

- No almacenar secretos en claro.
- Separar fuente versionable de estado generado.
- Mantener backups/migraciones.
- Definir política `.gitignore` para DB/traces cuando aplique.

## Criterios de aceptación

- Existe descriptor de workspace.
- Existe modelo lógico de DB.
- Reportes y runs quedan correlacionados.
- Trazas pueden exportarse sin secretos.


## Implementación inicial en FUNC-SPRINT-10

`FUNC-SPRINT-10` materializa la parte SQLite de esta ADR mediante `LocalStore`, con base runtime en `.devpilot/devpilot.db`.

### Alcance implementado

```text
schema_migrations
runs
findings
gates
events
approvals
cost_events
```

### Decisiones de implementación

- La base SQLite es local y generada en runtime.
- La base no se versiona y queda excluida por `.gitignore`.
- `state init` es idempotente y no borra historial.
- Los gates/validadores persisten `CommandResult` de forma best-effort para no romper comandos previos ante fallos temporales de SQLite.
- `history list` consulta runs recientes.

### Límites de esta versión

- No hay cifrado todavía.
- No hay política de retención ni backup/restore formal.
- No hay locking multi-proceso explícito más allá de SQLite.
- `events`, `approvals` y `cost_events` quedan como tablas base para sprints posteriores.

### Criterio de evolución

Si se agregan migraciones destructivas, cifrado, sincronización remota, RBAC/IAM, retención obligatoria o uso de SQLite para datos sensibles, esta ADR deberá actualizarse nuevamente o dividirse en una ADR específica de almacenamiento seguro.
