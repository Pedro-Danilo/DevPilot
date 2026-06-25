---
title: "POST-H-006-A — CLI command registry static inventory report"
doc_id: "POST-H-006-A-AUDIT"
version: "1.0.0"
status: "implemented-initial"
approval: "internal"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
sprint: "POST-H-006-A"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# POST-H-006-A — CLI command registry static inventory report

## Propósito

Este reporte documenta la implementación inicial del inventario estático del CLI y del modelo de registry de comandos de DevPilot.

La entrega convierte el parser actual de `src/devpilot_core/cli.py` en un reporte local, reproducible y validable por schema sin modificar nombres públicos, sin migrar handlers y sin ejecutar comandos registrados.

## Estado

Estado: `implemented-initial`.

`POST-H-006-A` inicia el hito `POST-H-006 — CLI command registry y desacoplamiento de handlers`. Esta versión es una baseline preliminar y advisory: sirve para entender la superficie actual del CLI y preparar migraciones posteriores, pero no debe usarse como loader dinámico de handlers.

## Alcance implementado

- Paquete `src/devpilot_core/cli_registry/`.
- Modelo `CommandDescriptor`, `CommandGroupDescriptor`, `CommandRiskLevel` y `CommandSideEffect`.
- Extractor AST read-only sobre `src/devpilot_core/cli.py`.
- Reporte schema-backed `CliCommandRegistry`.
- Comando CLI `python -m devpilot_core cli-registry report --json`.
- Escritura opcional de `outputs/reports/cli_command_registry.json` y `.md` con `--write-report`.
- Schema `docs/schemas/cli_command_registry.schema.json` registrado como `CliCommandRegistry`.
- Test contracts v1/v2 para el hito.

## Fuera de alcance explícito

- No se migran handlers fuera de `cli.py`.
- No se cambia la semántica de comandos públicos.
- No se elimina ni renombra ningún comando.
- No se habilita carga dinámica arbitraria de handlers.
- No se habilita remote execution, connector write ni plugin execution.
- No se ejecutan comandos a partir del registry.

## Funcionamiento técnico

`StaticCliInventoryExtractor` parsea el AST de `src/devpilot_core/cli.py` y detecta:

- llamadas `add_parser(...)`;
- relaciones `add_subparsers(...)`;
- paths públicos de comandos;
- flags declaradas mediante `add_argument(...)`;
- handlers inferidos desde `_dispatch` cuando es posible;
- riesgo operativo por grupo/side effects;
- flags de seguridad locales.

`CliCommandRegistryReportBuilder` valida el payload en memoria contra `CliCommandRegistry` y opcionalmente genera reportes bajo `outputs/reports/`.

## Criterios PASS

- PASS si el inventario detecta grupos principales del CLI: `workspace`, `schema`, `validate`, `quality-gate`, `test-contracts` y `architecture`.
- PASS si el JSON generado valida contra `CliCommandRegistry`.
- PASS si el comando `cli-registry report` retorna `CommandResult` con `exit_code=0`.
- PASS si `remote_execution_enabled`, `connector_write_enabled` y `plugin_execution_enabled` permanecen en `false`.
- PASS si no se migra ni altera semántica pública del CLI.

## Criterios BLOCK

- BLOCK si el registry permite carga dinámica arbitraria de handlers.
- BLOCK si se elimina o renombra un comando público.
- BLOCK si el reporte requiere red, APIs externas o ejecución remota.
- BLOCK si no valida contra schema.
- BLOCK si los artefactos documentales quedan desincronizados.

## Riesgos y limitaciones

- La asociación handler-comando es estática y preliminar; algunos handlers pueden quedar como `legacy_dispatch::*` hasta POST-H-006-B/C.
- El inventario AST no sustituye pruebas de paridad funcional.
- El registry aún no representa ownership modular real de handlers porque los handlers siguen en `cli.py`.
- La clasificación de riesgo es heurística y debe endurecerse antes de enforcement industrial.

## Comandos de validación

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_006_cli_command_registry.py tests/test_cli_command_registry_schema.py -q
python -m devpilot_core cli-registry report --write-report --json
python -m devpilot_core schema validate --schema-id CliCommandRegistry --instance outputs/reports/cli_command_registry.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```
