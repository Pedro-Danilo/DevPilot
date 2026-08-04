---
doc_id: "DEVPL-UOC-000-CAPABILITY-INVENTORY-REPORT"
title: "UOC-000 — Capability inventory and base contracts audit"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
approval: "approved_by_owner"
updated: "2026-08-04"
created_by: "UOC-000"
canonical_commit: "43254e3e61cdafe65e0ed2d773fe9032b0a81f05"
preliminary: false
---

# UOC-000 — Capability inventory and base contracts audit

## 1. Decisión

UOC-000 queda `implemented-initial/PASS`. No añade runtime ni rutas UI. Autoriza
UOC-001 exclusivamente para exploración documental read-only.

## 2. Fuentes auditadas

- `.devpilot/cli_registry/command_ownership_matrix.json`;
- `.devpilot/cli_registry/cli_compatibility_contracts.json`;
- `.devpilot/interfaces/api_route_contract_registry.json`;
- `.devpilot/interfaces/ui_route_contract_registry.json`;
- `.devpilot/policy/guard_pattern_catalog.json`;
- `.devpilot/project_state.json`;
- capturas autoritativas de Dashboard, Reports, Traces, Approval Center y Settings;
- corrective UI-first aceptado;
- API-GAP-SEC-001 cerrado;
- integración canónica en `43254e3e61cdafe65e0ed2d773fe9032b0a81f05`.

## 3. Inventario

```text
CLI commands source: 193
CLI commands classified: 193
API routes source: 39
UI routes source: 5
UI routes mapped: 5
```

### Riesgo

| `forbidden` | 5 |
| `mutating` | 130 |
| `read-only` | 2 |
| `sensitive` | 56 |

### Paridad

| `CLI-BRIDGE-REGISTERED` | 181 |
| `PLANNED` | 3 |
| `POLICY-BLOCKED` | 5 |
| `UI-READ-ONLY` | 4 |

## 4. Gates

```text
classification_complete=true
mutating_without_policy_total=0
sensitive_ui_native_without_approval_total=0
critical_or_network_capabilities_policy_blocked=True
new_ui_routes_added=0
runtime_execution_enabled=false
arbitrary_shell_allowed=false
```

## 5. Contratos creados

- capability registry;
- document resource;
- edit plan;
- approval binding;
- governed job;
- evidence reference;
- feature flags/kill switches;
- sprint manifest.

Los contratos de edición y ejecución son deliberadamente no operativos. Sus
schemas fijan invariantes para UOC-004 en adelante.

## 6. Test Impact

UOC-000 modifica metadata, schemas, governance y tests. No cambia código Python
ni TypeScript de producción. La validación autoritativa requiere:

- tests propios UOC-000;
- schema registry;
- Project State;
- CLI ownership matrix;
- UI route registry enforcement;
- TCR v1/v2;
- Docs Governance.

No requiere full regression si el diff permanece dentro del payload aprobado.

## 7. Riesgos residuales

- La mayoría de comandos CLI todavía no tiene Application Service explícito.
- `write-report` se modela como mutación para impedir exposición UI sin policy.
- UOC-001 debe implementar path guards y opaque IDs antes de leer documentos.
- Ninguna feature flag futura queda habilitada por UOC-000.
