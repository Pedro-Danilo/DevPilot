---
doc_id: "POST-H-021-REMOTE-RUNNER-DESIGN-RUNBOOK"
title: "Remote Runner Design Runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
phase: "POST-FASE-H"
created_by: "POST-H-021-E"
implementation_status: "implemented-initial"
local_first: true
dry_run: true
remote_execution_enabled: false
---

# Remote Runner Design Runbook

## 1. Propósito

Este runbook define cómo operar e interpretar el estado de Remote Runner después de POST-H-021. El hito queda cerrado como diseño `implemented-initial`, no como capacidad productiva de ejecución remota.

Regla operativa:

```text
remote registry existe != remote runner habilitado
remote readiness existe != remote execution permitido
remote quality gate PASS != autorización de ejecución remota
```

## 2. Interpretación design-only

`decision_status=design-only` significa que DevPilot solo conserva metadatos, criterios, ADR y reportes locales para evaluar preparación futura. En este estado:

```text
remote_execution_allowed=false
remote_runner_enabled=false
remote_execution_used=false
network_used=false
external_api_used=false
credentials_required=false
secrets_read=false
connector_write_enabled=false
plugin_execution_enabled=false
```

Un PASS del readiness report o del quality gate confirma que esas restricciones siguen vigentes. No habilita SSH, HTTP remote, gRPC, websockets, túneles, cloud control plane, workers remotos ni ejecución de comandos fuera del workspace local.

## 3. Verificación local

Comandos operativos:

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core remote runner readiness --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core quality-gate run --profile industrial --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
```

PASS requiere:

```text
readiness_level=remote-design-only
decision_status=design-only
remote_runner_enabled=false
remote_execution_used=false
network_used=false
external_api_used=false
credentials_required=false
secrets_read=false
blocking_findings_total=0
remote-readiness-design-only presente en hardening/industrial
```

## 4. BLOCK inmediato

Tratar como bloqueo cualquier evidencia de:

```text
remote_runner_enabled=true
remote_execution_allowed=true
remote_execution_used=true
network_used=true
external_api_used=true
credentials_required=true
secrets_read=true
shell_allowed=true
cloud_control_plane_enabled=true
connector_write_enabled=true
plugin_execution_enabled=true
```

Acción correctiva mínima:

```text
1. Detener el avance del sprint que introdujo el drift.
2. Revisar .devpilot/remote/remote_readiness_criteria.json.
3. Revisar .devpilot/remote/runner_registry.json.
4. Ejecutar remote runner readiness y quality-gate hardening.
5. Corregir el cambio que activó flags remotos.
6. Actualizar manifest, source registry, TCR y project_state si el fix cambia contratos.
```

## 5. Checklist go/no-go futuro

Antes de siquiera evaluar una habilitación futura de Remote Runner se requiere:

```text
POST-H-022 enterprise deployment threat model aprobado
POST-H-023 secure transport design aprobado
ADR futura explícita que cambie la decisión design-only
modelo RBAC/Approval para acciones remotas
sandbox remoto y límites de filesystem
modelo de secretos y rotación
observabilidad, trazas y auditoría
kill-switch probado
dry-run por defecto
quality gate remoto dedicado
pruebas de seguridad y regresión focal
runbook de incident response
```

No-go si falta cualquiera de los elementos anteriores o si la solución depende de credenciales, red o ejecución remota antes de contar con aprobación arquitectónica.

## 6. Límites

POST-H-021-E no agrega runtime remoto. Es un cierre documental y operativo de una capacidad preliminar de diseño. La evolución industrial requiere nuevos backlogs, ADR y quality gates antes de modificar `remote_execution_allowed=false`.

