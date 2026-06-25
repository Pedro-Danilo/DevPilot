---
doc_id: "POST-H-006-BACKLOG"
id: "POST-H-006"
title: "POST-H-006 — CLI command registry y desacoplamiento de handlers"
status: "approved"
version: "0.6.0"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_runtime_features_added_by_backlog: false
no_remote_execution_enabled: true
implementation_status: "in-progress"
approval: "internal"
---

# POST-H-006 — CLI command registry y desacoplamiento de handlers

## 1. Objetivo

Diseñar e implementar un **Command Registry interno para el CLI de DevPilot** que reduzca el acoplamiento del archivo `src/devpilot_core/cli.py`, estabilice los contratos de comandos, facilite pruebas focales por dominio y prepare el terreno para la evolución posterior de `ApplicationService`, API local y Web UI.

El objetivo no es cambiar la semántica de los comandos, sino **hacer explícito el inventario de comandos**, sus handlers, riesgos, dominios, flags de seguridad, relación con `ApplicationService`, test contracts y comandos de validación recomendados.

## 2. Contexto y justificación

El reverse engineering post-H identificó `src/devpilot_core/cli.py` como uno de los principales **architectural hotspots**: concentra parser, dispatch, handlers, imports de muchos dominios y reglas operativas. Esa concentración permitió avanzar rápido en los sprints anteriores, pero ahora representa riesgo de mantenimiento.

Problemas actuales a resolver:

```text
- Crecimiento continuo del archivo cli.py.
- Handlers mezclados con construcción de parser.
- Difícil ownership por dominio de comando.
- Riesgo de regresiones cruzadas al modificar comandos no relacionados.
- Falta de inventario machine-readable de comandos, riesgos y pruebas asociadas.
- Dificultad para que API/UI reutilicen contratos de comando de forma homogénea.
```

Este hito implementa una transición gradual: primero registry e inventario, luego migración incremental de grupos de comandos. No debe forzar una reescritura masiva del CLI.

## 3. Alcance

Incluye:

```text
- Modelo de CommandDescriptor / CommandGroupDescriptor.
- Registry local de comandos DevPilot.
- Inventario machine-readable de comandos, dominios, riesgos y pruebas recomendadas.
- Migración inicial de grupos seguros al nuevo registry.
- Tests de paridad entre comandos legacy y comandos registrados.
- Reporte de cobertura del CLI por dominio.
- Reglas para evitar crecimiento no gobernado de cli.py.
```

No incluye:

```text
- Reescritura completa del CLI en un solo sprint.
- Cambio de nombres públicos de comandos existentes.
- Eliminación inmediata de handlers legacy.
- Nueva API pública.
- Nueva Web UI.
- Remote execution.
- Connector write.
- Plugin execution.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/cli.py
src/devpilot_core/__main__.py
src/devpilot_core/cli_models.py
src/devpilot_core/application/services.py
src/devpilot_core/application/dtos.py
.devpilot/testing/test_contract_registry.json
docs/backlogs/post_h_prioritized_roadmap.md
docs/adr/ADR-POSTH-003-cli-modularization.md
docs/02_architecture/post_h_current_architecture_map.md
docs/audits/post_h_eval_001_baseline_assessment.md
```

## 5. Entregables

```text
src/devpilot_core/cli_registry/models.py
src/devpilot_core/cli_registry/registry.py
src/devpilot_core/cli_registry/builders.py
src/devpilot_core/cli_registry/report.py
src/devpilot_core/cli_registry/__init__.py
src/devpilot_core/cli_commands/validation.py
src/devpilot_core/cli_commands/workspace.py
src/devpilot_core/cli_commands/policy.py
src/devpilot_core/cli_commands/quality.py
docs/schemas/cli_command_registry.schema.json
docs/schemas/schema_catalog.json                  # registrar schema nuevo
docs/02_architecture/cli_command_registry_map.md
tests/test_post_h_006_cli_command_registry.py
tests/test_cli_command_registry_schema.py
```

Opcional si no aumenta acoplamiento:

```text
src/devpilot_core/application/cli_registry_service.py
```

## 6. Modelo de datos mínimo

El registry debe representar al menos:

```json
{
  "schema_version": "1.0",
  "registry_id": "devpilot-cli-command-registry",
  "generated_from": "static-code-and-declarative-descriptors",
  "commands_total": 0,
  "groups": [
    {
      "group_id": "workspace",
      "domain": "workspace",
      "owner_module": "src/devpilot_core/cli_commands/workspace.py",
      "risk_level": "medium",
      "application_service_required": true,
      "commands": [
        {
          "command_id": "workspace.status",
          "public_invocation": "python -m devpilot_core workspace status --json",
          "handler": "handle_workspace_status",
          "returns": "CommandResult",
          "writes_files": false,
          "dry_run_supported": false,
          "policy_check_required": false,
          "recommended_tests": [
            "python -m pytest tests/test_workspace_manager.py -q"
          ]
        }
      ]
    }
  ],
  "safety": {
    "remote_execution_enabled": false,
    "connector_write_enabled": false,
    "plugin_execution_enabled": false
  }
}
```

## 7. Principios de diseño

```text
1. Backward compatibility: no romper comandos existentes.
2. Incremental migration: migrar grupos seguros primero.
3. Registry como inventario, no como plugin loader dinámico inseguro.
4. Handlers explícitos, no carga arbitraria de módulos por strings no controlados.
5. CommandResult sigue siendo el contrato de salida.
6. Todo comando con efectos debe declarar side effects y policy requirements.
7. El nuevo registry debe reducir acoplamiento, no ocultarlo.
```

## 8. Micro-sprints propuestos

### POST-H-006-A — Inventario estático del CLI y modelo de registry

Objetivo: levantar inventario completo de comandos existentes y definir el modelo de registry sin modificar comportamiento.

Tareas:

```text
1. Crear paquete src/devpilot_core/cli_registry/.
2. Definir CommandDescriptor, CommandGroupDescriptor, CommandRiskLevel y CommandSideEffect.
3. Crear extractor estático básico que liste grupos/subcomandos desde el parser actual.
4. Generar reporte read-only de comandos actuales.
5. Crear schema cli_command_registry.schema.json.
6. Registrar schema en schema_catalog.json.
```

Criterios PASS:

```text
PASS si el inventario detecta los grupos principales del CLI.
PASS si el registry JSON generado valida contra schema.
PASS si no cambia ningún comando público.
PASS si no aumenta el acoplamiento de cli.py salvo llamadas mínimas al extractor/registry.
```

Criterios BLOCK:

```text
BLOCK si se elimina o renombra un comando público.
BLOCK si el registry permite carga dinámica arbitraria de handlers.
BLOCK si se habilita ejecución remota, plugins o conectores write.
```

Validación:

```powershell
python -m pytest tests/test_post_h_006_cli_command_registry.py tests/test_cli_command_registry_schema.py -q
python -m devpilot_core schema validate --schema-id CliCommandRegistry --instance outputs/reports/cli_command_registry.json --json
```

### POST-H-006-B — Command registry declarativo inicial

Objetivo: crear registry declarativo para comandos de bajo riesgo.

Grupos iniciales recomendados:

```text
workspace
standards
schema
validate
project-state
test-contracts
quality-gate
industrial-readiness
```

Tareas:

```text
1. Crear descriptors para grupos de bajo riesgo.
2. Declarar dominio, owner module, policy requirements, tests y side effects.
3. Generar reporte de cobertura registry vs CLI real.
4. Marcar comandos legacy todavía no migrados.
5. Agregar test que prohíba descriptors incompletos.
```

Criterios PASS:

```text
PASS si los grupos iniciales tienen descriptor completo.
PASS si comandos con writes declaran explícitamente writes_files=true.
PASS si todos los descriptors tienen recommended_tests.
PASS si el reporte identifica legacy_unregistered_commands_total.
```

### POST-H-006-C — Migración incremental de handlers de validación/workspace

Objetivo: mover handlers seleccionados fuera de `cli.py` sin romper UX.

Tareas:

```text
1. Crear src/devpilot_core/cli_commands/workspace.py.
2. Crear src/devpilot_core/cli_commands/validation.py.
3. Mover handlers seguros de workspace/status/init dry-run/validate docs/contracts/all.
4. Mantener parser público en cli.py o builder intermedio, según menor riesgo.
5. Agregar tests de paridad salida legacy vs nueva ruta.
```

Criterios PASS:

```text
PASS si workspace status sigue devolviendo CommandResult equivalente.
PASS si validate docs/contracts/all conserva semántica.
PASS si tests existentes pasan sin modificación masiva.
```

Criterios BLOCK:

```text
BLOCK si se rompe compatibilidad de flags.
BLOCK si se cambia exit_code de comandos existentes.
BLOCK si se omite EventLogger o persistencia best-effort cuando existía.
```

### POST-H-006-D — Reporte de hotspots CLI y ownership por comando

Objetivo: hacer visible la deuda restante del CLI y asociarla a roadmap/tests.

Tareas:

```text
1. Generar outputs/reports/cli_command_registry_report.{json,md}.
2. Calcular comandos por dominio.
3. Calcular comandos con side effects.
4. Identificar comandos sin ApplicationService boundary.
5. Identificar comandos sin test contract asociado.
6. Relacionar hallazgos con POST-H-007 y POST-H-003.
```

Criterios PASS:

```text
PASS si el reporte diferencia migrated, registered_only y legacy.
PASS si comandos críticos aparecen con risk_level alto/crítico.
PASS si el reporte es read-only y no modifica fuentes.
```

### POST-H-006-E — Gate de no crecimiento monolítico

Objetivo: evitar que nuevos comandos se agreguen sin descriptor.

Tareas:

```text
1. Agregar test que falle si se agregan comandos nuevos sin registry descriptor.
2. Permitir allowlist temporal para legacy conocido.
3. Documentar proceso de alta de comando nuevo.
4. Actualizar runbook con flujo de validación.
5. Registrar contrato en test_contract_registry si corresponde.
```

Criterios PASS:

```text
PASS si un comando nuevo sin descriptor falla en test focal.
PASS si legacy actual queda registrado en allowlist explícita.
PASS si test-contracts validate sigue PASS.
```

## 9. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_006_cli_command_registry.py -q
python -m pytest tests/test_cli_command_registry_schema.py tests/test_schema_registry.py -q
python -m devpilot_core schema validate --schema-id CliCommandRegistry --instance outputs/reports/cli_command_registry.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core industrial-readiness check --json
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Reescritura masiva del CLI | Alta | Migración incremental por grupos seguros. |
| Romper compatibilidad pública | Alta | Tests de paridad y no cambio de flags. |
| Registry usado como loader inseguro | Alta | Descriptors explícitos, sin import dinámico libre. |
| Duplicar lógica parser/handler | Media-alta | Separar descriptor, parser y ejecución. |
| No reducir deuda real | Media | Métricas migrated/legacy y gate de no crecimiento. |

## 11. No-go gates

```text
NO-GO si se cambia semántica pública de comandos existentes sin ADR.
NO-GO si se habilita remote execution.
NO-GO si se habilita connector write.
NO-GO si se habilita plugin execution.
NO-GO si un comando sensible queda sin policy metadata.
NO-GO si se eliminan tests existentes para hacer pasar la migración.
```

## 12. Entregable verificable

```text
Registry de comandos validable por schema.
Reporte de comandos y hotspots CLI.
Primeros grupos migrados fuera de cli.py.
Gate que impide nuevos comandos sin descriptor.
Tests focales PASS.
Quality gate hardening PASS.
```


## 9. Avance de implementación — POST-H-006-A

Estado: `implemented-initial`.

`POST-H-006-A — Inventario estático del CLI y modelo de registry` queda implementado como baseline read-only del Command Registry. La entrega crea el paquete `src/devpilot_core/cli_registry/`, registra el schema `CliCommandRegistry`, expone el comando `python -m devpilot_core cli-registry report --json` y genera reportes opcionales bajo `outputs/reports/cli_command_registry.json` y `.md`.

Alcance implementado:

```text
- Modelo CommandDescriptor / CommandGroupDescriptor.
- Enums CommandRiskLevel y CommandSideEffect.
- Extractor AST read-only sobre src/devpilot_core/cli.py.
- Reporte schema-backed del CLI actual.
- Registro de schema en schema_catalog.json.
- Test contracts v1/v2 para POST-H-006-A.
- Documentación técnica y audit report.
```

Fuera de alcance explícito:

```text
- No se migran handlers fuera de cli.py.
- No se cambia ningún nombre público de comando.
- No se ejecutan comandos desde el registry.
- No se permite carga dinámica arbitraria de handlers.
- No se habilita remote execution, connector write ni plugin execution.
```

Comando principal:

```powershell
python -m devpilot_core cli-registry report --write-report --json
```

Criterios PASS cubiertos:

```text
PASS si el inventario detecta los grupos principales del CLI.
PASS si el registry JSON generado valida contra CliCommandRegistry.
PASS si no cambia ningún comando público.
PASS si no aumenta el acoplamiento de cli.py salvo el comando mínimo de reporte.
```

Limitación industrial explícita: esta versión es preliminar/advisory. La migración real de handlers y pruebas de paridad quedan para `POST-H-006-B/C`; no debe usarse todavía como loader dinámico ni como enforcement de runtime.

Siguiente micro-sprint posterior a B: `POST-H-006-C — Migración incremental de handlers de validación/workspace`.


## 10. Avance de implementación — POST-H-006-B

Estado: `implemented-initial`.

`POST-H-006-B — Command registry declarativo inicial` queda implementado como una capa declarativa inicial sobre el inventario AST de `POST-H-006-A`.

Alcance implementado:

```text
- `DeclarativeCliRegistryBuilder` en `src/devpilot_core/cli_registry/registry.py`.
- Descriptors declarativos para grupos: workspace, standards, schema, validate, project-state, test-contracts, quality-gate e industrial-readiness.
- Marcación `registered-declarative` para comandos cubiertos.
- Marcación `legacy-unregistered` para comandos aún no declarados.
- Métricas de cobertura: declarative_registered_commands_total y legacy_unregistered_commands_total.
- Overrides de seguridad para comandos con escritura, migración o posible ejecución de subprocess.
- Manifest, audit report, runbook, README, changelog y contratos TCR v1/v2 actualizados.
```

Fuera de alcance explícito:

```text
- No se migran handlers fuera de `cli.py`.
- No se ejecutan comandos desde el registry.
- No se habilita carga dinámica de handlers.
- No se cambia ningún comando público.
- No se habilita remote execution, connector write ni plugin execution.
```

Comando principal:

```powershell
python -m devpilot_core cli-registry report --write-report --json
```

Criterios PASS cubiertos:

```text
PASS si los grupos iniciales tienen descriptor completo.
PASS si comandos con writes declaran writes_files=true.
PASS si todos los descriptors tienen recommended_tests.
PASS si el reporte identifica legacy_unregistered_commands_total.
```

Limitación industrial explícita: esta versión es preliminar/advisory. La migración física de handlers y pruebas de paridad quedan para `POST-H-006-C`; el registry no debe usarse todavía como router runtime ni loader dinámico.

Micro-sprint posterior ejecutado: `POST-H-006-D — Reporte de hotspots CLI y ownership por comando`.


## 11. Avance de implementación — POST-H-006-C

Estado: `implemented-initial`.

`POST-H-006-C — Migración incremental de handlers de validación/workspace` implementa la primera migración real de lógica de handlers fuera de `src/devpilot_core/cli.py`, manteniendo compatibilidad pública y sin convertir el registry en router runtime.

Artefactos implementados:

```text
src/devpilot_core/cli_commands/__init__.py
src/devpilot_core/cli_commands/workspace.py
src/devpilot_core/cli_commands/validation.py
tests/test_post_h_006_c_handler_migration.py
docs/audits/post_h_006_c_handler_migration_report.md
docs/post_h_006_c_manifest.json
```

Alcance implementado:

```text
- `workspace init` delega la construcción de CommandResult a `handle_workspace_init`.
- `workspace status` delega la construcción de CommandResult a `handle_workspace_status`.
- `validate docs/contracts/all` delega a `handle_validate_scope`.
- `cli.py` conserva parser, wrappers, flags, print_result, EventLogger, persistencia y reportes opcionales.
- `CliCommandRegistry` marca comandos migrados con `handler-migrated-incremental`.
- `runtime_router_enabled=false` y `dynamic_handler_loading_enabled=false`.
```

Criterios PASS cubiertos:

```text
- `workspace status` conserva CommandResult y salida JSON equivalente.
- `workspace init --dry-run` conserva dry-run y no escribe project.yaml.
- `validate docs/contracts/all` conserva semántica de ValidationGateway.
- Tests de paridad focales PASS.
- No se renombraron comandos públicos ni flags.
- No se omitieron EventLogger ni persistencia best-effort en wrappers.
```

Limitación industrial explícita: esta versión es incremental. No elimina wrappers legacy de `cli.py`, no activa ejecución desde registry, no habilita carga dinámica de handlers y no migra comandos de mayor riesgo. La reducción completa de hotspot CLI requiere `POST-H-006-D/E` y probablemente coordinación con `POST-H-007`.

Micro-sprint posterior ejecutado: `POST-H-006-D — Reporte de hotspots CLI y ownership por comando`.


## 12. Avance de implementación — POST-H-006-D

Estado: `implemented-initial`.

`POST-H-006-D — Reporte de hotspots CLI y ownership por comando` implementa una lectura industrial de la deuda restante del CLI. El reporte se deriva del Command Registry acumulado A/B/C y del Test Contract Registry local; no ejecuta comandos, no importa handlers de dominio y no modifica fuentes.

Artefactos implementados:

```text
src/devpilot_core/cli_registry/hotspots.py
tests/test_post_h_006_d_cli_hotspot_ownership.py
docs/audits/post_h_006_d_hotspot_ownership_report.md
docs/post_h_006_d_manifest.json
outputs/reports/cli_command_registry_report.json
outputs/reports/cli_command_registry_report.md
```

Alcance implementado:

```text
- Conteo migrated / registered_only / legacy por comando.
- Conteo por dominio y owner_module.
- Conteo de comandos con side effects.
- Identificación de comandos high/critical.
- Identificación de comandos sin boundary explícito fuera de cli.py.
- Asociación inferida a Test Contract Registry desde recommended_tests.
- Ranking de top hotspots por score.
- Links explícitos a POST-H-003, POST-H-006-E y POST-H-007.
```

Criterios PASS cubiertos:

```text
- El reporte diferencia migrated, registered_only y legacy.
- Los comandos críticos aparecen con risk_level high/critical.
- El reporte es read-only y no modifica fuentes.
- Los artefactos cli_command_registry_report.json/.md solo se escriben con --write-report.
- TCR v1/v2 queda sincronizado con el contrato post-h-006-cli-hotspot-ownership.
```

Fuera de alcance explícito:

```text
- No se bloquea crecimiento del CLI todavía.
- No se migra ningún handler adicional.
- No se convierte el registry en runtime router.
- No se activa dynamic handler loading.
- No se habilita remote execution, connector write ni plugin execution.
```

Limitación industrial explícita: esta versión es preliminar/advisory. La asociación a test contracts se infiere desde `recommended_tests`, por lo que puede ser más amplia que una cobertura semántica específica por comando. El enforcement real de crecimiento monolítico queda para `POST-H-006-E`.

Micro-sprint posterior ejecutado: `POST-H-006-E — Gate de no crecimiento monolítico`.


## 13. Avance de implementación — POST-H-006-E

Estado: `implemented-initial`.

`POST-H-006-E — Gate de no crecimiento monolítico` convierte la evidencia advisory del reporte D en un gate local bloqueante: si aparece un comando público como `legacy-unregistered` y no está cubierto por la allowlist temporal source-controlled, el gate devuelve `BLOCK`.

Artefactos implementados:

```text
src/devpilot_core/cli_registry/growth_gate.py
.devpilot/cli_registry/legacy_command_allowlist.json
tests/test_post_h_006_e_cli_no_growth_gate.py
docs/audits/post_h_006_e_no_growth_gate_report.md
docs/post_h_006_e_manifest.json
outputs/reports/cli_command_registry_no_growth_gate.json
outputs/reports/cli_command_registry_no_growth_gate.md
```

Alcance implementado:

```text
- Gate `CliNoGrowthGate` para comparar registry actual contra allowlist legacy.
- Comando CLI `python -m devpilot_core cli-registry guard --json`.
- Opción `--write-report` para evidencia local en outputs/reports.
- Allowlist explícita `.devpilot/cli_registry/legacy_command_allowlist.json` con legacy conocido.
- Descriptor declarativo para `cli-registry.guard`.
- Test focal que demuestra que un comando legacy no allowlisted produce BLOCK.
- TCR v1/v2 sincronizado con `post-h-006-cli-no-growth-gate`.
```

Criterios PASS cubiertos:

```text
- Un comando legacy no cubierto por allowlist falla en test focal.
- Legacy actual queda registrado en allowlist explícita y temporal.
- `test-contracts validate` y `validate-v2` siguen PASS.
- El gate no ejecuta comandos públicos ni importa handlers dinámicamente.
- Reportes se escriben solo con `--write-report`.
```

Fuera de alcance explícito:

```text
- No reduce automáticamente deuda legacy existente.
- No migra handlers adicionales.
- No activa runtime registry router.
- No activa dynamic handler loading.
- No habilita remote execution, connector write ni plugin execution.
```

Limitación industrial explícita: esta versión es `implemented-initial`. El gate impide crecimiento monolítico no registrado, pero la reducción real de deuda requiere migraciones/descriptor coverage por familias de comandos y `POST-H-007 — ApplicationService boundary hardening`.

Siguiente hito recomendado: `POST-H-007 — ApplicationService boundary hardening`.
