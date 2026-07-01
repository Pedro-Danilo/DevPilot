---
doc_id: "POST-H-020-C-COMPLIANCE-EVIDENCE-REPORT"
title: "POST-H-020-C — Evidence collector y report generator local"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
created_by: "POST-H-020-C"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
local_first: true
dry_run: true
certification_claimed: false
legal_advice_claimed: false
---

# POST-H-020-C — Evidence collector y report generator local

## Resumen

POST-H-020-C agrega una primera versión industrial local para generar reportes de compliance mapping desde evidencias declaradas. La implementación es metadata-only: valida mappings, inspecciona metadatos de `source_paths` y genera reportes bajo `outputs/reports` solo cuando se solicita `--write-report`.

Este artefacto no declara certificación, no constituye asesoría legal, no representa auditoría externa y no envía evidencias a terceros.

## Componentes

```text
src/devpilot_core/compliance/evidence.py
src/devpilot_core/compliance/report.py
tests/test_post_h_020_compliance_evidence_report.py
docs/post_h_020_c_manifest.json
```

## Garantías

```text
commands_executed=false
network_used=false
external_api_used=false
mutations_performed=false
certification_claimed=false
legal_advice_claimed=false
```

## Criterios PASS

```text
PASS si ComplianceEvidenceCollector reporta evidencia declarada local sin ejecutar comandos.
PASS si ComplianceMappingReporter produce ComplianceMappingReport schema-valid.
PASS si missing evidence se expresa como finding.
PASS si compliance mapping report --json --write-report genera JSON/Markdown bajo outputs/reports por defecto y acepta rutas de salida explícitas.
PASS si cli-registry guard reconoce compliance.mapping.report en la allowlist.
```

## Límites

POST-H-020-C no implementa integración con audit packs ni quality gate. Eso queda para POST-H-020-D/E. Tampoco habilita conectores externos, red, APIs externas, remote execution, plugin execution, certificación compliance ni asesoría legal.
