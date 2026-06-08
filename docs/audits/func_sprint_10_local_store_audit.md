---
title: "FUNC-SPRINT-10 — Local SQLite Store Audit"
doc_id: "DEVPL-AUDIT-FUNC-010"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-08"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-10 — Local SQLite Store Audit

## 1. Propósito

Este artefacto registra la implementación de `FUNC-SPRINT-10 — Persistencia local SQLite y estado operativo`. El sprint convierte a DevPilot Local en una herramienta con memoria operacional mínima: puede crear una base SQLite local, registrar resultados de comandos/gates, consultar estado de la base y listar ejecuciones recientes.

## 2. Funcionamiento

La persistencia se implementa con `sqlite3` de la biblioteca estándar de Python. No se agregan dependencias, no se usan servicios externos, no se requieren API keys y no se ejecutan llamadas de red.

La base por defecto es:

```text
.devpilot/devpilot.db
```

La base es runtime y no debe versionarse. El repo incluye el código y el schema, no el archivo `.db` generado.

## 3. Integración

El sprint agrega el paquete:

```text
src/devpilot_core/store/
```

La CLI incorpora:

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m devpilot_core history list --json --limit 10
```

Los comandos que producen `CommandResult` persisten una proyección operacional de forma best-effort. Esto evita que una falla temporal de SQLite rompa validadores previos, manteniendo compatibilidad con los sprints 01–09.

## 4. Rol dentro de DevPilot

`LocalStore` es la base para:

- auditoría local de runs;
- trazabilidad de gates;
- consulta de findings históricos;
- approvals persistentes futuros;
- cost events futuros;
- evaluación continua;
- AgentOps local;
- eventual interfaz desktop/web sobre estado operacional.

## 5. Scripts, módulos y artefactos creados

```text
src/devpilot_core/store/local_store.py
src/devpilot_core/store/__init__.py
tests/test_local_store.py
docs/audits/func_sprint_10_local_store_audit.md
docs/functional_sprint_10_manifest.json
```

## 6. Archivos modificados

```text
.gitignore
.devpilot/project.yaml
src/devpilot_core/cli.py
src/devpilot_core/validators/artifact.py
src/devpilot_core/workspace/manager.py
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
docs/02_architecture/adrs/ADR-0007-persistencia-local-filesystem-sqlite-jsonl.md
```

## 7. Schema SQLite v0

```text
schema_migrations
runs
findings
gates
events
approvals
cost_events
```

### runs

Registra ejecuciones de comandos/gates con `run_id`, comando, estado, exit code, mensaje, subject, timestamps, metadata y payload JSON completo.

### findings

Registra findings normalizados asociados a un `run_id`.

### gates

Registra una proyección de gate por comando, con estado `PASS`, `FAIL`, `BLOCK` o `ERROR`.

### events

Tabla preparada para eventos operativos. En esta versión no replica automáticamente cada línea JSONL; queda lista para endurecimiento posterior.

### approvals

Tabla estructural para aprobaciones humanas futuras. No implementa aún flujo de aprobación persistente.

### cost_events

Tabla estructural para auditoría de costos futura. No mide aún consumo real de proveedores.

## 8. Comandos de uso

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m devpilot_core state status --json --write-report
python -m devpilot_core history list --json --limit 10
python -m devpilot_core history list --json --limit 10 --write-report
```

## 9. Criterios PASS

```text
state init crea .devpilot/devpilot.db.
La migración es idempotente.
state status muestra schema_version, tablas y conteos.
history list muestra runs recientes o lista vacía si no hay historial.
La DB no puede ubicarse fuera del project root.
pytest -q queda en PASS.
```

## 10. Criterios BLOCK

```text
DB fuera del workspace.
Schema incompleto.
Migración que borra historial.
Persistencia que rompe comandos previos.
Runtime DB incluida en el ZIP o repo.
Rutas de evidencia inconsistentes Windows/Linux.
```

## 11. Riesgos

```text
No hay cifrado de base local.
No hay política de retención.
No hay backup/restore formal.
No hay locking multi-proceso explícito.
Approvals y cost_events son tablas iniciales sin flujo completo.
EventLog JSONL aún no se sincroniza completamente con SQLite.
```

## 12. Corrección adicional incluida

Se normalizó `_display_path()` en `validate-artifact` para emitir rutas POSIX (`docs/...`) igual que `validate-frontmatter`. Esto evita inconsistencias de evidencia entre Windows y Linux y previene futuros fallos similares al hotfix de Sprint 09.

## 13. Pruebas aplicadas

```text
tests/test_local_store.py
```

Cobertura nueva:

```text
LocalStore initialize idempotente.
Registro de CommandResult y findings.
Rechazo de DB fuera del root.
history list sin DB.
CLI state init/status/history.
Persistencia de readiness-check.
Normalización POSIX en validate-artifact.
```

Resultado esperado:

```text
pytest -q -> 71 passed
```

## 14. Naturaleza de la implementación

Esta es una primera versión funcional. Es suficiente para entrenamiento, trazabilidad local y preparación de AgentOps, pero no equivale todavía a un subsistema industrial de persistencia. Para producción se requerirá cifrado, retención, backup/restore, migraciones versionadas más formales, control de concurrencia, integridad reforzada, auditoría avanzada y políticas de privacidad.

## 15. ADR actualizada

Se actualizó `docs/02_architecture/adrs/ADR-0007-persistencia-local-filesystem-sqlite-jsonl.md` porque el sprint materializa una decisión de persistencia previamente aceptada: SQLite local para estado operativo consultable. No se abrió una ADR nueva porque la decisión ya existía; se añadió trazabilidad de implementación y límites de la versión v0.
