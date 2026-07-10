---
doc_id: POST-H-030-E-CLI-COMPATIBILITY-REPORT
title: "POST-H-030-E — CLI compatibility contract tests"
status: approved
version: "1.0.0"
updated: "2026-07-09"
owner: "Ordóñez"
approval: approved
created_by: "POST-H-030-E"
criticality: P0
---

# POST-H-030-E — CLI compatibility contract tests

## Resultado

POST-H-030-E queda implementado como primera versión local-first de contratos de compatibilidad CLI y cierra el backlog POST-H-030 como `closed/cli-boundary-hotspot-reduction`.

## Alcance implementado

- Schema `CliCompatibilityReport` en `docs/schemas/cli_compatibility_report.schema.json`.
- Fixture source-controlled `.devpilot/cli_registry/cli_compatibility_contracts.json`.
- Módulo `src/devpilot_core/cli_registry/compatibility.py`.
- Comando `python -m devpilot_core cli-registry compatibility --json`.
- Subgate `cli-boundary-hotspot-reduction` para perfiles hardening/industrial.
- Test focal `tests/test_post_h_030_cli_compatibility_contracts.py`.

## Cobertura inicial

- Contratos totales: 72.
- Tier 0: 71 contratos para comandos migrados/high/critical.
- Tier 1: 1 contrato de gobernanza de operador.
- Smoke opt-in curado: 16 comandos seguros/read-only/dry-run.

## Invariantes preservados

- No hay router dinámico.
- No hay `importlib` de handlers.
- No se habilita red ni APIs externas.
- No se habilita remote execution, connector write ni plugin execution.
- Los contratos bloquean ausencia de JSON envelope, exit code policy, help esencial, normalización y safety flags.
- Los snapshots/fixtures no deben actualizarse para ocultar breaking changes.

## Limitaciones

Esta es una primera versión industrial. No snapshottea todos los comandos tier_2 ni reemplaza una comparación completa before/after por dominio. La evolución recomendada para POST-H-031+ es asociar contratos con evidence graph y operator health para exponer diferencias observables al operador.
