---
doc_id: "POST-H-020-A-COMPLIANCE-MAPPING-SCHEMA-REGISTRY-REPORT"
title: "POST-H-020-A — Compliance mapping schema registry report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
---

# POST-H-020-A — Compliance mapping schema registry report

## 1. Veredicto

POST-H-020-A queda `implemented-initial`.

La implementación crea la capa contractual local para compliance mapping ampliado. Esta versión es declarativa y no certificante: `certification_claimed=false`, `legal_advice_claimed=false`, sin red, APIs externas, conectores, remote execution, plugin execution ni envío de evidencias a terceros.

Disclaimers obligatorios: `no certificación`, `no asesoría legal` y no auditoría externa.

## 2. Implementado

```text
- ComplianceControlMapping schema.
- ComplianceEvidenceMapping schema.
- ComplianceMappingReport schema.
- .devpilot/compliance/control_mappings.json.
- .devpilot/compliance/evidence_mappings.json.
- Registro de schemas en schema_catalog.
- Tests focales de schema y no-certification.
```

## 3. Implementado inicial

Los mappings cubren una primera base interna DevPilot:

```text
- remote execution disabled
- plugin execution blocked until ADR
- Policy/Approval/RBAC
- Test Contract Registry y quality gate
- release reproducibility
- observability retention
- documentation governance
```

## 4. No implementado todavía

```text
- validator semántico
- evidence collector
- compliance mapping report CLI
- audit pack integration
- quality-gate compliance-mapping-pack
- runbook/disclaimers finales de cierre
```

## 5. PASS/BLOCK

PASS si los schemas validan los registries locales, los schemas quedan registrados, y los flags de no-certificación son obligatorios.

BLOCK si cualquier contrato permite `certification_claimed=true`, `legal_advice_claimed=true`, controles sin evidencia o evidencias sin source/justificación.

## 6. Riesgos

El principal riesgo es sobreclaiming. La mitigación de esta primera versión es contractual: campos `const false`, disclaimers explícitos y tests de no-certificación. La validación semántica profunda queda para POST-H-020-B.

## 7. Comandos

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_020_compliance_mapping_schema.py tests/test_post_h_020_compliance_evidence_mapping.py tests/test_post_h_020_compliance_no_certification.py tests/test_schema_registry.py -q
python -m devpilot_core schema validate --schema-id ComplianceControlMapping --instance .devpilot/compliance/control_mappings.json --json
python -m devpilot_core schema validate --schema-id ComplianceEvidenceMapping --instance .devpilot/compliance/evidence_mappings.json --json
```
