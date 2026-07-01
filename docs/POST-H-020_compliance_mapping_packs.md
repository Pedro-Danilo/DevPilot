---
doc_id: "POST-H-020-IMPLEMENTATION"
id: "POST-H-020"
title: "POST-H-020 — Compliance mapping packs ampliados"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
implementation_status: "in-progress"
current_micro_sprint: "POST-H-020-A"
next_micro_sprint: "POST-H-020-B"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
certification_claimed: false
legal_advice_claimed: false
---

# POST-H-020 — Compliance mapping packs ampliados

## 1. Propósito

POST-H-020 amplía los compliance mapping packs locales de DevPilot para mapear controles, evidencias, riesgos, políticas, pruebas y documentos contra marcos internos o referencias externas, sin declarar certificación, auditoría externa completada ni asesoría legal.

Este documento es la fuente de implementación acumulativa del hito. El backlog ejecutable vive en `docs/backlogs/POST-H-020_compliance_mapping_packs.md`.

## 2. Estado POST-H-020-A

Estado: `implemented-initial`.

POST-H-020-A crea la base contractual para control/evidence mapping:

```text
- docs/schemas/compliance_control_mapping.schema.json
- docs/schemas/compliance_evidence_mapping.schema.json
- docs/schemas/compliance_mapping_report.schema.json
- .devpilot/compliance/control_mappings.json
- .devpilot/compliance/evidence_mappings.json
```

Los tres schemas están registrados en `docs/schemas/schema_catalog.json`.

Disclaimers obligatorios: `certification_claimed=false`, `legal_advice_claimed=false`, `no certificación`, `no asesoría legal` y no auditoría externa.

## 3. Límites explícitos

POST-H-020-A no implementa todavía validator semántico, collector, report generator, CLI `compliance mapping report`, audit pack integration ni quality gate. Eso corresponde a POST-H-020-B/C/D.

No se habilita:

```text
- certification_claimed=true
- legal_advice_claimed=true
- auditoría externa
- envío de evidencias a terceros
- conectores externos
- network/API externa
- remediación automática
- remote execution
- plugin execution
```

## 4. Criterios PASS

```text
PASS si los schemas validan los registries locales.
PASS si certification_claimed=false y legal_advice_claimed=false son obligatorios.
PASS si cada control declara control_id, domain, risk_level y required_evidence.
PASS si cada evidencia declara source_command/source_paths o justificación.
PASS si schema_catalog registra los tres contratos nuevos.
```

## 5. Criterios BLOCK

```text
BLOCK si un schema permite certification_claimed=true.
BLOCK si un schema permite legal_advice_claimed=true.
BLOCK si un control queda sin required_evidence.
BLOCK si una evidencia queda sin source ni justificación.
BLOCK si un documento afirma certificación o asesoría legal.
```

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Sobreclaim de compliance certificada | `certification_claimed=false` como `const false` y disclaimers obligatorios. |
| Interpretación legal incorrecta | `legal_advice_claimed=false` y lenguaje no-certificante. |
| Evidencia incompleta | `required_evidence` obligatorio por control; validación semántica queda para POST-H-020-B. |
| Drift de mappings | Registries source-controlled y tests focales. |

## 7. Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace tests/test_post_h_020_compliance_mapping_schema.py tests/test_post_h_020_compliance_evidence_mapping.py tests/test_post_h_020_compliance_no_certification.py tests/test_schema_registry.py tests/test_project_global_state.py -q
python -m devpilot_core schema validate --schema-id ComplianceControlMapping --instance .devpilot/compliance/control_mappings.json --json
python -m devpilot_core schema validate --schema-id ComplianceEvidenceMapping --instance .devpilot/compliance/evidence_mappings.json --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
```

## 8. Evolución pendiente

POST-H-020-B debe implementar el validator semántico para unicidad, cobertura de dominios, required_evidence con mapping real y bloqueo explícito de claims. POST-H-020-C debe generar el reporte local; POST-H-020-D debe integrar audit packs y quality gate; POST-H-020-E debe cerrar con runbook y disclaimers finales.
