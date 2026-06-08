---
title: "Auditoría FUNC-SPRINT-18 — Preparación Desktop/Web"
doc_id: "DEVPL-AUDIT-FUNC-018"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-18"
updated: "2026-06-08"
---
# Auditoría FUNC-SPRINT-18 — Preparación Desktop/Web sin implementar UI completa

## Propósito

Registrar la implementación inicial de contratos de Application Services y DTOs para que CLI, escritorio y web puedan consumir el mismo DevPilot Core.

## Componentes creados

```text
src/devpilot_core/application/dtos.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
docs/07_interfaces/internal_application_contract.md
tests/test_application_services.py
docs/functional_sprint_18_manifest.json
```

## Componentes modificados

```text
src/devpilot_core/cli.py
src/devpilot_core/workspace/manager.py
.devpilot/project.yaml
README.md
docs/05_operations/runbook.md
docs/02_architecture/adrs/ADR-0002-core-local-first-cli-ui-futura.md
docs/functional_backlog_after_precode.md
```

## Funcionamiento

`ApplicationService` centraliza operaciones de validación y contrato:

```text
validate_frontmatter
validate_artifact
checklist_pre_code
readiness
standards_status
application_contract
```

El CLI conserva su contrato `CommandResult`, reportes opcionales, eventos JSONL y persistencia SQLite best-effort, pero obtiene los resultados principales desde `ApplicationService`.

## Comandos

```powershell
python -m devpilot_core app contract --json
python -m devpilot_core app contract --json --write-report
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --json
```

## Criterios PASS

```text
DTOs serializables.
ApplicationService operativo.
CLI usa service en validadores principales.
app contract parseable.
No UI implementada.
No dependencias nuevas.
No servidor activo.
No API externa.
pytest -q PASS.
```

## Criterios BLOCK

```text
Dependencia nueva de framework UI sin ADR.
Servidor web activo en Sprint 18.
Ventana desktop o frontend real.
Duplicación de lógica de core.
DTO con secretos o API keys.
Salida JSON incompatible.
```

## Pruebas

`tests/test_application_services.py` valida:

```text
ApplicationService valida frontmatter sin CLI.
ApplicationService valida artefacto sin CLI.
Rutas fuera del workspace se rechazan.
ApplicationRequest/ApplicationResponse son JSON serializables.
app contract CLI genera JSON y reportes.
```

## Riesgos

Primera versión. No hay UI, servidor, IPC, autenticación, sesiones, RBAC, packaging, WebSocket ni schemas JSON formales. La selección tecnológica debe resolverse con ADR futura si se adopta FastAPI, Tauri, Electron u otra alternativa.

## Veredicto

`FUNC-SPRINT-18` queda implementado como preparación interna, no como UI completa.
