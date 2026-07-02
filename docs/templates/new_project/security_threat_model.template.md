---
doc_id: "NEW-PROJECT-SECURITY-THREAT-MODEL-TEMPLATE"
title: "Template — Security threat model for new DevPilot project"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
template_id: "security_threat_model"
artifact_kind: "new_project_template"
created_by: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---

# Security threat model — {{project_name}}

## 1. Activos protegidos

| Activo | Sensibilidad | Amenaza principal | Control mínimo |
|---|---|---|---|
| {{asset_1}} | {{sensitivity_1}} | {{threat_1}} | {{control_1}} |
| {{asset_2}} | {{sensitivity_2}} | {{threat_2}} | {{control_2}} |

## 2. Trust boundaries

```text
workspace local
outputs/ runtime no versionable
configuración source-controlled sin secretos
interfaces CLI/API/UI locales si existen
```

## 3. Reglas no-go iniciales

```text
network_used=false
external_api_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
secrets_included=false
raw_secret_storage_allowed=false
```

## 4. Amenazas iniciales

| ID | Amenaza | Severidad | Mitigación | Evidencia requerida |
|---|---|---:|---|---|
| TH-001 | Secretos en plantillas o fixtures | Alta | placeholders no sensibles y tests de escaneo | {{evidence}} |
| TH-002 | Automatización destructiva | Alta | dry-run por defecto y aprobación humana | {{evidence}} |
| TH-003 | Vendor lock-in | Media-alta | ModelAdapter y rutas mock/local/API separadas | {{evidence}} |
| TH-004 | Falsa readiness | Alta | readiness preview y gates determinísticos | {{evidence}} |

## 5. Aprobaciones humanas

```text
Acciones destructivas: aprobación humana obligatoria.
Uso de APIs externas: ADR + presupuesto + revisión de privacidad.
Persistencia de datos sensibles: threat model actualizado + controles.
```

## 6. Criterios PASS/BLOCK

PASS si amenazas, activos, límites y no-go gates están documentados.

BLOCK si aparecen secrets reales, credenciales, URLs privadas, llaves, tokens o habilitación remota no aprobada.
