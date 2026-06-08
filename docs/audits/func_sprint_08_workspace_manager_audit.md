---
title: "FUNC-SPRINT-08 — Workspace Manager mínimo — Auditoría de implementación"
doc_id: "DEVPL-AUDIT-FUNC-08"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-08"
updated: "2026-06-08"
approval: "implementation_audit"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# FUNC-SPRINT-08 — Workspace Manager mínimo — Auditoría de implementación

## 1. Propósito

Este artefacto documenta la implementación de `FUNC-SPRINT-08 — Workspace Manager mínimo`. El sprint introduce `.devpilot/project.yaml` como contrato local mínimo de workspace para DevPilot Local, sin depender de servicios externos, API keys, modelos LLM ni dependencias adicionales.

El propósito técnico es convertir el repositorio en una unidad operativa reconocible por DevPilot: un proyecto con raíz detectable, metadatos mínimos, estándares activos, MIASI habilitado y rutas runtime conocidas.

## 2. Alcance implementado

Se implementó una primera versión local-first del Workspace Manager con las siguientes capacidades:

- descubrimiento de raíz de proyecto por `.devpilot/project.yaml` o por marcadores de repositorio (`pyproject.toml` + `docs/`);
- generación de plan de inicialización en dry-run;
- creación explícita de `.devpilot/project.yaml` mediante `workspace init --execute`;
- bloqueo de sobrescritura por defecto si el workspace ya existe;
- consulta de estado del workspace mediante `workspace status`;
- integración con `CommandResult`, `ReportEngine` y `EventLogger`;
- pruebas unitarias y de integración CLI;
- documentación en README, runbook, backlog y manifiesto funcional.

## 3. Componentes creados

### 3.1. `.devpilot/project.yaml`

**Propósito:** registrar el contrato mínimo local del workspace DevPilot.

**Funcionamiento:** el archivo contiene `schema_version`, bloque `project`, estándares activos, activación MIASI y rutas operativas (`docs`, `docs/standards`, `outputs`, `outputs/reports`, `outputs/traces`).

**Integración:** `workspace status` lo usa para determinar si el workspace está inicializado. `WorkspaceManager.discover()` lo prioriza como marcador de raíz.

**Rol dentro de DevPilot:** será la base para futuras políticas locales, persistencia, registry de agentes, configuración de herramientas y control de entorno.

**Comandos de uso:**

```powershell
python -m devpilot_core workspace init --execute
python -m devpilot_core workspace status --json
```

**Criterios PASS:** el archivo existe, es legible y contiene los metadatos mínimos generados por DevPilot.

**Criterios BLOCK:** falta el archivo cuando se espera workspace inicializado, o se intenta sobrescribir sin política explícita futura.

**Riesgos:** versión inicial sin migraciones, locking, cifrado, multi-workspace ni perfiles por usuario.

### 3.2. `src/devpilot_core/workspace/manager.py`

**Propósito:** implementar la lógica central de workspace.

**Funcionamiento:** define `WorkspaceManager`, `WorkspacePaths`, `WorkspaceInitPlan` y `WorkspaceStatus`. El manager descubre la raíz del proyecto, crea planes de inicialización, escribe `.devpilot/project.yaml` solo cuando `execute=True` y calcula estado del workspace.

**Integración:** `cli.py` usa este módulo para los comandos `workspace init` y `workspace status`. También reemplaza el antiguo `project_root()` basado solo en `Path.cwd()` por discovery controlado.

**Rol dentro de DevPilot:** boundary operativo para futuras capacidades: Policy Engine, SecretGuard, persistencia SQLite, registries de agentes/herramientas y ejecución controlada por workspace.

**Comandos de uso:**

```powershell
python -m devpilot_core workspace init --dry-run
python -m devpilot_core workspace init --execute
python -m devpilot_core workspace status --json
```

**Criterios PASS:** dry-run no escribe, execute crea el archivo cuando no existe, status detecta docs/standards/checklist, y discovery funciona desde subdirectorios.

**Criterios BLOCK:** sobrescritura de `.devpilot/project.yaml`, rutas fuera del root, ausencia de `docs/standards` o checklist pre-code.

**Riesgos:** parser YAML mínimo no es un parser YAML general; solo interpreta el contrato que DevPilot genera. Si el contrato crece, se deberá evaluar una dependencia YAML o parser formal mediante ADR si altera configuración operativa.

### 3.3. `src/devpilot_core/workspace/__init__.py`

**Propósito:** exponer la API pública del paquete workspace.

**Funcionamiento:** reexporta `WorkspaceManager`, modelos de workspace, constantes y helpers de render/parse.

**Integración:** permite importar `WorkspaceManager` desde `devpilot_core.workspace` sin acoplar consumidores al archivo `manager.py`.

**Rol dentro de DevPilot:** boundary estable del subsistema workspace.

**Criterios PASS:** imports públicos funcionan y no generan dependencias circulares.

**Criterios BLOCK:** romper imports o exponer una API inconsistente.

**Riesgos:** API inicial; puede evolucionar cuando haya migraciones, perfiles y persistencia.

### 3.4. `tests/test_workspace_manager.py`

**Propósito:** validar automáticamente el Sprint 08.

**Funcionamiento:** prueba dry-run sin escritura, execute con escritura, bloqueo de sobrescritura, status ready, status sin inicialización, discovery desde subdirectorio, CLI JSON y generación opcional de reporte.

**Integración:** se ejecuta con `pytest` junto con toda la suite.

**Rol dentro de DevPilot:** quality gate funcional del Workspace Manager.

**Criterios PASS:** todas las pruebas pasan y la suite completa queda en PASS.

**Criterios BLOCK:** cualquier regresión en dry-run, execute, no-overwrite, JSON CLI o discovery.

**Riesgos:** pruebas iniciales no cubren concurrencia, migraciones ni múltiples workspaces.

### 3.5. `docs/functional_sprint_08_manifest.json`

**Propósito:** registrar de forma máquina-legible los componentes y decisiones del Sprint 08.

**Funcionamiento:** enumera archivos creados/modificados, comandos, criterios PASS/BLOCK, pruebas y riesgos.

**Integración:** complementa este documento de auditoría y el backlog funcional.

**Rol dentro de DevPilot:** evidencia docs-as-code trazable.

**Criterios PASS:** JSON válido y consistente con el código.

**Criterios BLOCK:** manifest inconsistente con implementación real.

**Riesgos:** debe mantenerse sincronizado si se amplía Sprint 08.

## 4. Componentes modificados

### 4.1. `src/devpilot_core/cli.py`

**Propósito del ajuste:** agregar comandos workspace y usar discovery de workspace como raíz del proyecto.

**Funcionamiento:** se agregaron `workspace init` y `workspace status`, ambos con salida humana/JSON, integración con `EventLogger` y soporte `--write-report` para evidencia JSON/Markdown.

**Integración:** mantiene compatibilidad con comandos existentes: `readiness-check`, `miasi-required`, `validate-frontmatter`, `validate-artifact`, `standards status` y `checklist-pre-code`.

**Rol dentro de DevPilot:** superficie operativa del Workspace Manager.

**Criterios PASS:** comandos anteriores no regresan y los nuevos comandos devuelven `CommandResult` normalizado.

**Criterios BLOCK:** romper salida JSON, cambiar exit codes previos o escribir workspace sin `--execute`.

**Riesgos:** `argparse` aún no registra todos los errores de parsing en EventLog; esto puede endurecerse en una fase posterior.

### 4.2. `README.md`

**Propósito del ajuste:** mantener la entrada operativa rápida sincronizada con Sprint 08.

**Funcionamiento:** actualiza último/siguiente hito, lista WorkspaceManager como implementado, agrega comandos workspace y explica `.devpilot/project.yaml`.

**Integración:** sirve como guía inicial para instalar, probar y operar DevPilot.

**Rol dentro de DevPilot:** documentación operativa de onboarding.

**Criterios PASS:** README refleja comandos y estado reales.

**Criterios BLOCK:** README apunta a un sprint anterior o no documenta comandos nuevos.

**Riesgos:** debe actualizarse en cada sprint funcional.

### 4.3. `docs/05_operations/runbook.md`

**Propósito del ajuste:** documentar operación local del Workspace Manager.

**Funcionamiento:** agrega comandos, criterios PASS/BLOCK, riesgos y resultado esperado del Sprint 08.

**Integración:** guía operativa local para ejecutar, validar y diagnosticar el workspace.

**Rol dentro de DevPilot:** procedimiento oficial de operación local.

**Criterios PASS:** incluye instalación, validación, workspace init/status y riesgos.

**Criterios BLOCK:** omitir comportamiento dry-run/no-overwrite o criterios de bloqueo.

**Riesgos:** debe evolucionar cuando haya policy engine, migraciones o persistencia.

### 4.4. `docs/functional_backlog_after_precode.md`

**Propósito del ajuste:** cerrar Sprint 08 y mover continuidad a Sprint 09.

**Funcionamiento:** actualiza `next_sprint` a `FUNC-SPRINT-09`, marca workspace local como implementación inicial, documenta archivos, comandos, criterios PASS/BLOCK y riesgos residuales.

**Integración:** conserva el backlog como contrato funcional vivo.

**Rol dentro de DevPilot:** fuente de verdad para continuidad de sprints.

**Criterios PASS:** estado del backlog coincide con código, pruebas, README y runbook.

**Criterios BLOCK:** avanzar a Sprint 09 sin reflejar Sprint 08.

**Riesgos:** cualquier ajuste futuro debe mantener trazabilidad.

## 5. Pruebas aplicadas

Se agregó `tests/test_workspace_manager.py` con 9 pruebas nuevas:

```text
test_workspace_init_dry_run_does_not_write
test_workspace_init_execute_writes_project_yaml
test_workspace_init_dry_run_reports_existing_workspace_without_overwrite
test_workspace_init_blocks_existing_project_yaml
test_workspace_status_ready_when_initialized
test_workspace_status_fails_when_not_initialized_but_docs_exist
test_workspace_discovery_from_nested_directory
test_workspace_cli_init_and_status_json_are_parseable
test_workspace_cli_dry_run_write_report
```

También se ejecutó la suite completa:

```powershell
python -m pytest -q
```

Resultado esperado:

```text
51 passed, 0 failed, 0 errors, 0 skipped
```

## 6. Comandos de verificación

```powershell
python -m devpilot_core --version
python -m devpilot_core workspace init --dry-run
python -m devpilot_core workspace status --json
python -m devpilot_core standards status --json
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
python -m pytest -q
```

## 7. Decisión ADR

No se abre nueva ADR para Sprint 08 porque:

- no hay dependencias externas nuevas;
- no hay API keys;
- no hay llamadas de red;
- no hay cambio de proveedores LLM;
- no se modifica la política de seguridad aprobada;
- no se introduce persistencia estructural nueva como SQLite;
- `.devpilot/project.yaml` ya estaba previsto como unidad operativa local en el backlog.

Si en el futuro se agregan migraciones, configuración cifrada, multi-workspace, perfiles de usuario, secretos reales, locking o persistencia estructural, deberá evaluarse una ADR nueva o una actualización de ADR existente.

## 8. Veredicto

`FUNC-SPRINT-08` queda implementado como versión inicial. Es apto para cerrar si la suite completa permanece en PASS y los comandos workspace verifican el contrato esperado.

Siguiente sprint funcional:

```text
FUNC-SPRINT-09 — Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos
```
