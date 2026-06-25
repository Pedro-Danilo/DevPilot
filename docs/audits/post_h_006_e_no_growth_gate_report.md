---
title: "POST-H-006-E — Gate de no crecimiento monolítico"
doc_id: "AUDIT-POST-H-006-E"
status: "implemented-initial"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
local_first: true
read_only: true
---

# POST-H-006-E — Gate de no crecimiento monolítico

## Propósito

`POST-H-006-E` implementa un gate local para evitar que el CLI vuelva a crecer como monolito no gobernado. El gate compara el Command Registry actual contra `.devpilot/cli_registry/legacy_command_allowlist.json` y bloquea comandos públicos nuevos que aparezcan como `legacy-unregistered`.

## Artefactos técnicos

```text
src/devpilot_core/cli_registry/growth_gate.py
.devpilot/cli_registry/legacy_command_allowlist.json
tests/test_post_h_006_e_cli_no_growth_gate.py
docs/post_h_006_e_manifest.json
outputs/reports/cli_command_registry_no_growth_gate.json
outputs/reports/cli_command_registry_no_growth_gate.md
```

## Funcionamiento

El gate ejecuta estos pasos determinísticos:

```text
1. Construye el CliCommandRegistry acumulado A/B/C/D/E.
2. Lee la allowlist temporal de legacy conocido.
3. Extrae comandos con registry_phase=legacy-unregistered.
4. Calcula unexpected_legacy = current_legacy - allowed_legacy.
5. Devuelve PASS si no hay unexpected_legacy ni allowlist inválida.
6. Devuelve BLOCK si aparece cualquier comando legacy no allowlisted.
```

## Comando operativo

```powershell
python -m devpilot_core cli-registry guard --json
python -m devpilot_core cli-registry guard --write-report --json
```

## Seguridad

```text
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
dynamic_handler_loading_enabled=false
network_used=false
external_api_used=false
source_mutations_performed=false
```

El gate no ejecuta comandos públicos, no importa handlers dinámicamente y no modifica código fuente. Con `--write-report` solo genera evidencia bajo `outputs/reports/`.

## PASS

```text
PASS si todo comando legacy actual está cubierto por allowlist temporal.
PASS si un comando nuevo con descriptor declarativo no se considera crecimiento legacy.
PASS si test-contracts validate y validate-v2 siguen PASS.
```

## BLOCK

```text
BLOCK si aparece un comando legacy-unregistered no allowlisted.
BLOCK si la allowlist no existe, no es JSON válido o no está marcada como POST-H-006-E.
BLOCK si hay entradas duplicadas en la allowlist.
BLOCK si se intenta usar el registry como runtime router o loader dinámico sin ADR.
```

## Limitación industrial explícita

Esta versión es `implemented-initial`. Bloquea crecimiento monolítico no registrado, pero no reduce automáticamente la deuda legacy existente. La allowlist es temporal y debe disminuir conforme los comandos se registren declarativamente o se migren a `cli_commands`/ApplicationService en siguientes iteraciones.
