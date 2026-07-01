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
implementation_status: "closed"
current_micro_sprint: "POST-H-020-E"
next_micro_sprint: "POST-H-021"
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

## 4. Estado POST-H-020-C

Estado: `implemented-initial`.

POST-H-020-C agrega collector local y report generator para compliance mapping:

```text
- src/devpilot_core/compliance/evidence.py
- src/devpilot_core/compliance/report.py
- tests/test_post_h_020_compliance_evidence_report.py
- docs/audits/post_h_020_c_compliance_evidence_report.md
- docs/post_h_020_c_manifest.json
```

Capacidades:

```text
- `ComplianceEvidenceCollector` inspecciona metadatos de `source_paths`.
- `ComplianceMappingReporter` genera `ComplianceMappingReport` validable.
- CLI `compliance mapping report --json --write-report`.
- Reportes runtime bajo `outputs/reports/compliance_mapping_report.json` y `.md`.
- Missing evidence explícito mediante findings.
- `source_command` se conserva como declaración y no se ejecuta.
```

## 5. Límites explícitos

POST-H-020-E cierra el backlog con documentación operativa final, disclaimers explícitos y tests de cierre documental. El hito queda como `implemented-initial`: apto para evidencia técnica local, no para certificación compliance, asesoría legal ni auditoría externa.

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

## 6. Criterios PASS

```text
PASS si los schemas validan los registries locales.
PASS si certification_claimed=false y legal_advice_claimed=false son obligatorios.
PASS si cada control declara control_id, domain, risk_level y required_evidence.
PASS si cada evidencia declara source_command/source_paths o justificación.
PASS si schema_catalog registra los tres contratos nuevos.
PASS si el validator semántico no reporta controles críticos sin evidencia.
PASS si la cobertura mínima incluye security/testing/policy/release/observability/agentic.
PASS si el reporte se genera localmente, schema-valid y con `disclaimer_present=true`.
PASS si no se ejecutan comandos declarados en `source_command`.
```

## 7. Criterios BLOCK

```text
BLOCK si un schema permite certification_claimed=true.
BLOCK si un schema permite legal_advice_claimed=true.
BLOCK si un control queda sin required_evidence.
BLOCK si una evidencia queda sin source ni justificación.
BLOCK si un documento afirma certificación o asesoría legal.
BLOCK si un required_evidence no existe en evidence_mappings.
BLOCK si un source_command intenta red/API externa, instalación o mutación.
BLOCK si se envían evidencias fuera del workspace.
BLOCK si missing evidence se oculta.
```

## POST-H-020-E — Runbook, disclaimers y cierre

Estado: `implemented-initial / cierre`.

DevPilot agrega el runbook dedicado `docs/05_operations/compliance_mapping_runbook.md` y los disclaimers `docs/03_security/compliance_mapping_disclaimers.md`. La documentación define cómo interpretar `mapped`, `partial`, `gap` y `not-applicable`; refuerza que los reportes son señales técnicas locales y no certificación, asesoría legal ni auditoría externa.

También se agrega `tests/test_post_h_020_compliance_runbook_disclaimers.py` para bloquear sobreclaims documentales y verificar que el backlog queda cerrado. Durante el cierre se corrige la desincronización de TCR v2 detectada en POST-H-020-D: los contratos POST-H-020-C/D usan `classification_status=explicit`, valor permitido por el schema.

Comandos principales:

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_020_compliance_runbook_disclaimers.py tests/test_post_h_020_compliance_quality_gate.py tests/test_post_h_020_compliance_evidence_report.py tests/test_post_h_020_compliance_mapping_validator.py tests/test_post_h_020_compliance_mapping_schema.py tests/test_post_h_020_compliance_evidence_mapping.py tests/test_post_h_020_compliance_no_certification.py tests/test_schema_registry.py tests/test_project_global_state.py tests/test_post_h_006_e_cli_no_growth_gate.py -q
python -m devpilot_core compliance mapping report --json --write-report
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core cli-registry guard --json
```

Límite explícito: POST-H-020 queda cerrado como capacidad local no-certificante. No habilita certificación compliance, asesoría legal, auditoría externa, envío de evidencias a terceros, ejecución de `source_command`, red/API externa, remote execution, connector write ni plugin execution.

Último hito cerrado: `POST-H-020 — Compliance mapping packs ampliados`
Siguiente hito: `POST-H-021`

## POST-H-020-C — Evidence collector y report generator local

Estado: `implemented-initial / hito activo`.

DevPilot agrega `ComplianceEvidenceCollector` y `ComplianceMappingReporter` para convertir los mappings locales en reportes runtime no certificantes. El collector solo inspecciona metadatos de rutas declaradas, no ejecuta comandos, no lee contenidos de evidencia, no usa red/API externa y no exporta evidencias a terceros.

Comandos principales:

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_020_compliance_evidence_report.py tests/test_post_h_020_compliance_mapping_validator.py tests/test_post_h_020_compliance_mapping_schema.py tests/test_post_h_020_compliance_evidence_mapping.py tests/test_post_h_020_compliance_no_certification.py tests/test_schema_registry.py tests/test_project_global_state.py tests/test_post_h_006_e_cli_no_growth_gate.py -q
python -m devpilot_core compliance mapping report --json --write-report
python -m devpilot_core schema validate --schema-id ComplianceMappingReport --instance outputs/reports/compliance_mapping_report.json --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core cli-registry guard --json
```

Límite explícito: POST-H-020-C es una primera versión local y no-certificante. No ejecuta `source_command`, no recolecta evidencias externas, no genera certificación, no ofrece asesoría legal, no usa conectores externos, no usa red/APIs externas, no habilita remote execution ni plugin execution.

Último hito: `POST-H-019 — Plugin sandbox design sin ejecución arbitraria`
Último hito cerrado: `POST-H-019 — Plugin sandbox design sin ejecución arbitraria`
Hito activo: `POST-H-020 — Compliance mapping packs ampliados`
Siguiente hito: `POST-H-020 — Compliance mapping packs ampliados`
Último micro-sprint implementado: `POST-H-020-C — Evidence collector y report generator local`
Siguiente micro-sprint: `POST-H-020-D — Integración con audit packs y quality gate`

## POST-H-020-D — Integración con audit packs y quality gate

Estado: `implemented-initial / hito activo`.

DevPilot agrega `ComplianceMappingQualityGate` y el subgate `compliance-mapping-pack` para los perfiles `hardening` e `industrial`. El subgate compone validator, collector, reporter, AuditPackV2 dry-run y la señal local `compliance-pack-integrity` sin ejecutar comandos de evidencia, sin escribir audit-pack ZIPs, sin red/API externa y sin claims de certificación o asesoría legal.

También se agrega al manifest de AuditPackV2 un bloque `compliance_mapping` con resumen no-certificante de controles, evidencias y disclaimers.

Comandos principales:

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_020_compliance_quality_gate.py tests/test_post_h_020_compliance_evidence_report.py tests/test_post_h_020_compliance_mapping_validator.py tests/test_post_h_020_compliance_mapping_schema.py tests/test_post_h_020_compliance_evidence_mapping.py tests/test_post_h_020_compliance_no_certification.py tests/test_schema_registry.py tests/test_project_global_state.py tests/test_post_h_006_e_cli_no_growth_gate.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core cli-registry guard --json
```

Límite explícito: POST-H-020-D es una primera integración local y no-certificante. No genera certificación compliance, no ofrece asesoría legal, no prueba cumplimiento legal, no ejecuta `source_command`, no usa red/APIs externas, no envía evidencias a terceros, no habilita remote execution ni plugin execution.

Último hito cerrado: `POST-H-019 — Plugin sandbox design sin ejecución arbitraria`
Hito activo: `POST-H-020 — Compliance mapping packs ampliados`
Último micro-sprint implementado: `POST-H-020-D — Integración con audit packs y quality gate`
Siguiente micro-sprint: `POST-H-020-E — Runbook, disclaimers y cierre`

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Sobreclaim de compliance certificada | `certification_claimed=false` como `const false` y disclaimers obligatorios. |
| Interpretación legal incorrecta | `legal_advice_claimed=false` y lenguaje no-certificante. |
| Evidencia incompleta | `required_evidence` obligatorio por control y validación semántica POST-H-020-B. |
| Drift de mappings | Registries source-controlled y tests focales. |

## 9. Comandos de verificación

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

POST-H-020 queda cerrado como `implemented-initial`. Evoluciones futuras pueden agregar marcos externos específicos, exportadores o revisiones formales, pero cualquier salida con implicaciones regulatorias, certificantes o de terceros requiere ADR, RBAC, approvals, threat model y quality gates adicionales.
