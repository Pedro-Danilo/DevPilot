---
doc_id: "POST-H-014-C-UI-ROUTE-CONTRACT-REPORT"
title: "POST-H-014-C — UI Route Contract y shell de producto"
status: "implemented-initial"
owner: "Ordóñez"
updated: "2026-06-28"
phase: "POST-H-014-C"
approval: "approved_by_owner"
---

# POST-H-014-C — UI Route Contract y shell de producto

## Resultado

POST-H-014-C implementa una primera versión industrial-local del contrato de la Web UI. El objetivo es que la shell visual no crezca como frontend paralelo sin gobierno, sino como superficie contract-driven acoplada a rutas API permitidas.

## Artefactos

```text
docs/schemas/ui_route_contract.schema.json
.devpilot/interfaces/ui_route_contract_registry.json
src/devpilot_core/interfaces/api/ui_contracts.py
ui/web/src/components/ContractBadges.ts
tests/test_post_h_014_ui_shell_contract.py
docs/post_h_014_c_manifest.json
```

## Controles implementados

```text
- Dashboard, Reports, Traces, Approvals y Settings tienen contrato UI.
- Cada página declara allowed_api_routes contra ApiRouteContractRegistry.
- Cada página declara local_only=true y no-go flags false.
- La UI muestra badges local-first, dry-run/plan-only, no-remote, no connector write y no plugin execution.
- La UI mantiene estados loading/empty/error y visibilidad BLOCK/ERROR.
- Smoke tests verifican API-only y ausencia de acciones destructivas.
```

## Seguridad

```text
remote_execution_allowed=false
connector_write_allowed=false
plugin_execution_allowed=false
external_api_allowed=false
network_server_started_by_tests=false
```

## Limitaciones

Esta capacidad es `implemented-initial`. No implementa router SPA completo, UX final, autenticación enterprise ni quality-gate final. POST-H-014-D y POST-H-014-E deben completar hardening local y señal de quality gate.
