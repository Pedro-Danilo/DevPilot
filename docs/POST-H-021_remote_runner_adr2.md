---
doc_id: "POST-H-021-IMPLEMENTATION"
id: "POST-H-021"
title: "POST-H-021 — Remote Runner ADR-2"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P3"
implementation_status: "active"
current_micro_sprint: "POST-H-021-C"
next_micro_sprint: "POST-H-021-D"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-021 — Remote Runner ADR-2

## 1. Propósito

POST-H-021 define la decisión arquitectónica y los controles mínimos para evaluar un remote runner futuro sin habilitar ejecución remota en el presente.

La regla base queda explícita:

```text
remote registry existe != remote runner habilitado
remote readiness existe != remote execution permitido
remote design existe != secure transport implementado
```

## 2. Estado POST-H-021-A

Estado: `implemented-initial`.

POST-H-021-A inventaría el baseline existente y agrega criterios de readiness design-only:

```text
docs/schemas/remote_readiness_criteria.schema.json
.devpilot/remote/remote_readiness_criteria.json
tests/test_post_h_021_remote_disabled_invariants.py
docs/audits/post_h_021_a_remote_inventory_baseline_report.md
docs/post_h_021_a_manifest.json
```

El sprint confirma que `src/devpilot_core/remote/runner.py` y `.devpilot/remote/runner_registry.json` son stubs/metadata bloqueados, no runtime remoto.

## 3. Estado POST-H-021-B

Estado: `implemented-initial`.

POST-H-021-B — ADR-2 de Remote Runner crea la ADR formal de Remote Runner:

```text
docs/adr/ADR-POSTH-004-remote-runner-adr2.md
tests/test_post_h_021_remote_adr2.py
docs/audits/post_h_021_b_remote_adr2_report.md
docs/post_h_021_b_manifest.json
```

La ADR se aprueba como decisión `design-only`. No autoriza ejecución remota inmediata y mantiene `remote_execution_allowed=false` y `remote_runner_enabled=false`.

Alternativas rechazadas:

```text
enable-now
SSH ad hoc
connector-as-runner
plugin-as-runner
```

Prerrequisitos futuros mínimos:

```text
POST-H-022 — Enterprise deployment threat model
POST-H-023 — Secure transport design
RBAC/Approval hardening
sandbox remoto
observabilidad/auditoría
modelo de secretos
kill-switch
quality gate remoto
dry-run por defecto
```

## 4. Invariantes actuales

```text
remote_execution_allowed=false
remote_runner_enabled=false
execution_allowed=false
remote_execution_used=false
cloud_control_plane_enabled=false
network_used=false
external_api_used=false
shell_allowed=false
credentials_required=false
secrets_read=false
requires_future_adr=true
```

## 5. Estado POST-H-021-C — Remote readiness report read-only

Estado: `implemented-initial`.

POST-H-021-C implementa un reporte local read-only de readiness remoto:

```text
src/devpilot_core/remote/readiness.py
src/devpilot_core/remote/reports.py
docs/schemas/remote_readiness_report.schema.json
tests/test_post_h_021_remote_readiness_report.py
docs/audits/post_h_021_c_remote_readiness_report.md
docs/post_h_021_c_manifest.json
```

La CLI operativa es:

```powershell
python -m devpilot_core remote runner readiness --json
python -m devpilot_core remote runner readiness --json --write-report
```

El reporte confirma `readiness_level=remote-design-only`, `future_adr_required=true`, `remote_runner_enabled=false`, `remote_execution_used=false`, `network_used=false`, `external_api_used=false`, `credentials_required=false`, `secrets_read=false` y `blocking_findings_total=0`.

El artefacto no autoriza ejecución remota. Solo lee criterios, registry y schemas locales; la escritura de reportes queda limitada a `outputs/reports/` bajo ejecución explícita.

## 6. Límites explícitos

POST-H-021-A/B/C no habilitan:

```text
remote execution
secure transport
SSH
HTTP remote
gRPC
websockets
tunnels
cloud control plane
remote workers
remote credentials
secret access
connector write
plugin execution
```

## 7. Evolución pendiente

POST-H-021 sigue activo. Las siguientes etapas previstas son:

```text
POST-H-021-D — Quality gate remote disabled
POST-H-021-E — Runbook, rollback y cierre
```

Cualquier cambio que pretenda activar ejecución remota requiere ADR futura, RBAC/Approval, secure transport, sandboxing, observabilidad, kill-switch, pruebas de seguridad y quality gate dedicado.
