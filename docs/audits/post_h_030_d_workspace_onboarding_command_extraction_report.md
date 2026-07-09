---
doc_id: POST-H-030-D-WORKSPACE-ONBOARDING-REPORT
title: "POST-H-030-D - Workspace/onboarding command extraction report"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-09"
approval: approved
---

# POST-H-030-D - Workspace/onboarding command extraction report

## Decision

POST-H-030-D queda implementado como `implemented-initial/local-first`.

La extracción mueve la construcción de resultados de comandos workspace/onboarding y portfolio-readiness hacia módulos propietarios sin cambiar la interfaz pública de la CLI.

## Alcance implementado

Módulos propietarios:

- `src/devpilot_core/cli_commands/workspace.py`
- `src/devpilot_core/cli_commands/workspace_onboarding.py`

Comandos extraídos en POST-H-030-D:

- `workspace register`
- `workspace list`
- `workspace select`
- `workspace registry-validate`
- `workspace isolation-check`
- `portfolio status`
- `portfolio hardening-gate`

Comandos workspace/onboarding ya consolidados en el boundary desde POST-H-006/POST-H-024 y preservados por esta implementación:

- `workspace init`
- `workspace status`
- `workspace bootstrap`
- `workspace readiness-preview`

## Compatibilidad preservada

`src/devpilot_core/cli.py` conserva:

- parser público;
- nombres de comandos;
- flags;
- wrappers estables;
- escritura opcional de reportes;
- eventos;
- persistencia;
- renderizado JSON/humano;
- códigos de salida.

Los módulos extraídos solo construyen `CommandResult` y delegan a servicios de dominio existentes.

## Boundaries preservados

- `workspace status` mantiene `ApplicationService.workspace_status`.
- `portfolio status` mantiene `ApplicationService.portfolio_status`.
- `workspace bootstrap` conserva dry-run por defecto y modo execute explícito.
- `workspace readiness-preview` conserva clasificación de evidencia faltante como pending/no overclaim.
- `workspace registry-validate` conserva validación v1/v2 sin mutar la fuente.
- `workspace isolation-check` conserva modo read-only.
- `portfolio hardening-gate` conserva el quality gate local-first sin red ni APIs externas.

## Safety invariants

- `runtime_router_enabled=false`.
- `dynamic_handler_loading_enabled=false`.
- `network_used=false`.
- `external_api_used=false`.
- `remote_execution_enabled=false`.
- `connector_write_enabled=false`.
- `plugin_execution_enabled=false`.
- No se habilitan mutaciones de fuente en runtime.
- No se agregan dependencias externas.

## Evidencia focal

Validación específica esperada:

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_030_workspace_onboarding_command_extraction.py -q
```

Validación contractual esperada:

```powershell
python -m devpilot_core cli-registry guard --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
```

## Limitaciones

Esta implementación no completa el desacoplamiento total de `cli.py`. El archivo sigue siendo el parser/wrapper/orquestador público. La compatibilidad observable completa mediante snapshots/tiered contracts queda para POST-H-030-E.
