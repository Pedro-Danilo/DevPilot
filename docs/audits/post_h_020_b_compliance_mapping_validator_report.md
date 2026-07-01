---
doc_id: "POST-H-020-B-COMPLIANCE-MAPPING-VALIDATOR-REPORT"
title: "POST-H-020-B — Compliance mapping validator report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
phase: "POST-FASE-H"
micro_sprint: "POST-H-020-B"
implementation_status: "implemented-initial"
approval: "approved_by_owner"
certification_claimed: false
legal_advice_claimed: false
network_used: false
external_api_used: false
mutations_performed: false
---

# POST-H-020-B — Compliance mapping validator report

## Resultado

POST-H-020-B queda implementado como `implemented-initial`.

Se incorpora `ComplianceMappingValidator` para validar semánticamente los mappings locales de compliance sin ejecutar comandos, sin recolectar evidencias y sin producir un reporte final. La capacidad sigue siendo local, declarativa y no-certificante.

## Artefactos principales

```text
src/devpilot_core/compliance/mapping.py
tests/test_post_h_020_compliance_mapping_validator.py
.devpilot/compliance/control_mappings.json
.devpilot/compliance/evidence_mappings.json
```

## Validaciones cubiertas

```text
- pack_id coherente entre control y evidence mappings.
- control_id único.
- evidence_id único.
- required_evidence con mapping real.
- controles críticos sin evidencia bloqueados.
- cobertura mínima por dominios security/testing/policy/release/observability/agentic.
- certification_claimed=false.
- legal_advice_claimed=false.
- disclaimer de no certificación y no asesoría legal.
- source_paths locales existentes.
- source_command declarativo sin tokens externos o mutantes.
```

## Evidencia local agregada

El baseline se amplía con cobertura inicial de dominio `agentic` mediante el control `DPL-AGT-001`, asociado a evidencias de RAG groundedness y evals de seguridad.

## Límites explícitos

POST-H-020-B no implementa:

```text
- collector de evidencias.
- report generator final.
- CLI compliance mapping report.
- audit pack integration.
- quality gate de compliance.
- certificación compliance.
- asesoría legal.
- envío de evidencias a terceros.
- conectores externos.
- red o APIs externas.
- remediación automática.
```

Estos elementos quedan para POST-H-020-C/D/E.
