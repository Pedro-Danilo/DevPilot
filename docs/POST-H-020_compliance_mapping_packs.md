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
current_micro_sprint: "POST-H-020-B"
next_micro_sprint: "POST-H-020-C"
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

## 3. Estado POST-H-020-B

Estado: `implemented-initial`.

POST-H-020-B agrega el validator semántico local para los mappings:

```text
- src/devpilot_core/compliance/mapping.py
- tests/test_post_h_020_compliance_mapping_validator.py
- docs/audits/post_h_020_b_compliance_mapping_validator_report.md
- docs/post_h_020_b_manifest.json
```

El validator comprueba:

```text
- Unicidad de control_id y evidence_id.
- Matching entre pack_id de controles y evidencias.
- Cada required_evidence tiene evidencia mapeada.
- Controles críticos sin evidencia producen BLOCK.
- Cobertura mínima por dominios security/testing/policy/release/observability/agentic.
- certification_claimed=false y legal_advice_claimed=false.
- Source paths locales existentes.
- Source commands declarativos sin tokens externos o mutantes.
```

Los registries locales se amplían con cobertura inicial del dominio `agentic` para conectar RAG/evals/safety con el baseline de compliance local.

## 4. Límites explícitos

POST-H-020-B no implementa todavía collector, report generator, CLI `compliance mapping report`, audit pack integration ni quality gate. Eso corresponde a POST-H-020-C/D/E.

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

## 5. Criterios PASS

```text
PASS si los schemas validan los registries locales.
PASS si certification_claimed=false y legal_advice_claimed=false son obligatorios.
PASS si cada control declara control_id, domain, risk_level y required_evidence.
PASS si cada evidencia declara source_command/source_paths o justificación.
PASS si schema_catalog registra los tres contratos nuevos.
PASS si el validator semántico no reporta controles críticos sin evidencia.
PASS si la cobertura mínima incluye security/testing/policy/release/observability/agentic.
```

## 6. Criterios BLOCK

```text
BLOCK si un schema permite certification_claimed=true.
BLOCK si un schema permite legal_advice_claimed=true.
BLOCK si un control queda sin required_evidence.
BLOCK si una evidencia queda sin source ni justificación.
BLOCK si un documento afirma certificación o asesoría legal.
BLOCK si un required_evidence no existe en evidence_mappings.
BLOCK si un source_command intenta red/API externa, instalación o mutación.
```

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Sobreclaim de compliance certificada | `certification_claimed=false` como `const false` y disclaimers obligatorios. |
| Interpretación legal incorrecta | `legal_advice_claimed=false` y lenguaje no-certificante. |
| Evidencia incompleta | `required_evidence` obligatorio por control y validación semántica POST-H-020-B. |
| Drift de mappings | Registries source-controlled y tests focales. |

## 8. Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace tests/test_post_h_020_compliance_mapping_validator.py tests/test_post_h_020_compliance_mapping_schema.py tests/test_post_h_020_compliance_evidence_mapping.py tests/test_post_h_020_compliance_no_certification.py tests/test_schema_registry.py tests/test_project_global_state.py -q
python -m devpilot_core schema validate --schema-id ComplianceControlMapping --instance .devpilot/compliance/control_mappings.json --json
python -m devpilot_core schema validate --schema-id ComplianceEvidenceMapping --instance .devpilot/compliance/evidence_mappings.json --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
```

## 9. Evolución pendiente

POST-H-020-C debe implementar collector local y report generator. POST-H-020-D debe integrar audit packs y quality gate. POST-H-020-E debe cerrar con runbook y disclaimers finales.
