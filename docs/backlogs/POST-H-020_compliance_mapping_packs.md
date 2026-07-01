---

doc_id: "POST-H-020-BACKLOG"
id: "POST-H-020"
title: "POST-H-020 — Compliance mapping packs ampliados"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "in-progress"
current_micro_sprint: "POST-H-020-B"
next_micro_sprint: "POST-H-020-C"
---

# POST-H-020 — Compliance mapping packs ampliados

## 0. Estado de implementación

Estado del backlog: `approved / in-progress`.

Micro-sprint actual: `POST-H-020-B — Compliance mapping validator`.

Resultado POST-H-020-A: `implemented-initial`. Se agregan schemas `ComplianceControlMapping`, `ComplianceEvidenceMapping` y `ComplianceMappingReport`, se registran en `schema_catalog.json`, y se crean los registries locales `.devpilot/compliance/control_mappings.json` y `.devpilot/compliance/evidence_mappings.json`. El hito permanece no-certificante: `certification_claimed=false`, `legal_advice_claimed=false`, sin red, APIs externas, conectores, remediación automática ni envío a terceros.

Resultado POST-H-020-B: `implemented-initial`. Se agrega `ComplianceMappingValidator` para validar unicidad de controles/evidencias, cobertura de `required_evidence`, bloqueo de controles críticos sin evidencia, cobertura mínima por dominio (`security`, `testing`, `policy`, `release`, `observability`, `agentic`) y no-claims de certificación o asesoría legal. El validator no recolecta evidencias, no ejecuta `source_command` y no genera el reporte final.

Disclaimers obligatorios: este hito es `no certificación`, `no asesoría legal` y no auditoría externa.

Siguiente micro-sprint: `POST-H-020-C — Evidence collector y report generator local`.

## 1. Objetivo

Ampliar los **compliance mapping packs locales** de DevPilot para mapear controles, evidencias, riesgos, políticas, pruebas y documentos contra marcos de referencia internos o externos, sin declarar certificación, cumplimiento legal formal ni auditoría externa.

El objetivo es producir un mecanismo local de mapeo y evidencia que ayude a razonar sobre seguridad, calidad, operación y gobernanza. No convierte a DevPilot en herramienta certificadora ni sustituye asesoría legal/compliance.

## 2. Contexto y justificación

El baseline post-H incluye `compliance/`, audit packs y evals de compliance-pack integrity en estado inicial. El risk register estableció como criterio BLOCK declarar compliance certificada. Por tanto, este hito debe ampliar capacidades de mapping sin sobreclaiming.

La necesidad técnica es que controles como `local-first`, `dry-run`, `PolicyEngine`, `Approval`, `RBAC`, `SecretGuard`, `TestContractRegistry`, `QualityGate`, `RAG groundedness`, `AuditPack` y `Release reproducibility` puedan mapearse a controles de referencia con evidencia verificable.

## 3. Alcance

Incluye:

```text
- Compliance pack registry ampliado.
- Control mapping schema.
- Evidence mapping schema.
- Pack validator semántico.
- Reporte local de cobertura por control.
- Disclaimers obligatorios de no-certificación.
- Integración con audit pack, quality gate y test contracts.
- Mapping inicial para controles internos DevPilot.
- Extensibilidad para marcos externos de referencia sin reclamar certificación.
```

No incluye:

```text
- Certificación compliance.
- Asesoría legal.
- Auditoría externa.
- Envío de evidencias a terceros.
- Firma legal de cumplimiento.
- Mapeo normativo exhaustivo de jurisdicciones.
- Automatización de remediación compliance.
- Conectores externos.
- Remote execution.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/03_security/post_h_security_risk_register.md
docs/04_quality/post_h_test_cost_assessment.md
docs/audits/post_h_eval_001_baseline_assessment.md
docs/audits/post_h_eval_001_closure_report.md
src/devpilot_core/compliance/
.devpilot/compliance/
docs/schemas/compliance_pack_registry.schema.json
src/devpilot_core/auditpack/
src/devpilot_core/quality/
src/devpilot_core/testing/
src/devpilot_core/policy/
.devpilot/testing/test_contract_registry.json
evals/fixtures/compliance_pack_integrity_cases.json
```

## 5. Entregables

```text
docs/schemas/compliance_control_mapping.schema.json
docs/schemas/compliance_evidence_mapping.schema.json
docs/schemas/compliance_mapping_report.schema.json
.devpilot/compliance/control_mappings.json
.devpilot/compliance/evidence_mappings.json
src/devpilot_core/compliance/mapping.py
src/devpilot_core/compliance/evidence.py
src/devpilot_core/compliance/report.py
tests/test_post_h_020_compliance_mapping_schema.py
tests/test_post_h_020_compliance_evidence_mapping.py
tests/test_post_h_020_compliance_no_certification.py
tests/test_post_h_020_compliance_quality_gate.py
docs/05_operations/compliance_mapping_runbook.md
docs/03_security/compliance_mapping_disclaimers.md
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/compliance/registry.py
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Compliance control mapping

```json
{
  "schema_version": "1.0",
  "pack_id": "devpilot.local.governance.baseline",
  "framework": "DevPilot Local Governance Baseline",
  "certification_claimed": false,
  "legal_advice_claimed": false,
  "controls": [
    {
      "control_id": "DPL-SEC-001",
      "title": "Remote execution disabled by default",
      "domain": "security",
      "risk_level": "critical",
      "mapped_capabilities": ["remote.runner.status", "policy.engine", "quality.gate"],
      "required_evidence": ["industrial-readiness", "quality-gate-hardening"],
      "status": "mapped",
      "owner": "security"
    }
  ]
}
```

### 6.2 Evidence mapping

```json
{
  "schema_version": "1.0",
  "control_id": "DPL-SEC-001",
  "evidence_id": "industrial-readiness",
  "evidence_type": "command-output",
  "source_command": "python -m devpilot_core industrial-readiness check --json",
  "source_paths": ["src/devpilot_core/industrial/readiness.py"],
  "required_fields": ["remote_runner_enabled", "remote_execution_used"],
  "expected_values": {
    "remote_runner_enabled": false,
    "remote_execution_used": false
  },
  "retention_class": "release-evidence"
}
```

### 6.3 Compliance mapping report

```json
{
  "schema_version": "1.0",
  "pack_id": "devpilot.local.governance.baseline",
  "ok": true,
  "certification_claimed": false,
  "controls_total": 20,
  "controls_mapped": 20,
  "controls_with_evidence": 18,
  "controls_missing_evidence": 2,
  "blocking_findings_total": 0,
  "disclaimer_present": true
}
```

## 7. Principios de diseño

```text
1. Compliance mapping is not certification.
2. Evidence must be local and reproducible.
3. Every claim must map to evidence or be marked gap.
4. No external audit claims.
5. No legal advice language.
6. No network or third-party submission.
7. Reports must include disclaimers.
8. Controls can be internal, external-reference or organization-specific.
9. Missing evidence is a finding, not something to hide.
10. Compliance packs must integrate with audit packs and quality gates.
```

## 8. Micro-sprints propuestos

### POST-H-020-A — Control mapping schemas y registry

Objetivo: definir schemas para mapping de controles y evidencias.

Tareas:

```text
1. Crear compliance_control_mapping.schema.json.
2. Crear compliance_evidence_mapping.schema.json.
3. Crear compliance_mapping_report.schema.json.
4. Registrar schemas en schema_catalog.json.
5. Crear .devpilot/compliance/control_mappings.json.
6. Crear .devpilot/compliance/evidence_mappings.json.
7. Crear tests de schema.
```

Criterios PASS:

```text
PASS si certification_claimed=false es obligatorio o default seguro.
PASS si todo control tiene control_id, domain, risk_level y required_evidence.
PASS si todo evidence mapping tiene source_command/source_paths o justificación.
PASS si schemas quedan registrados.
```

Criterios BLOCK:

```text
BLOCK si se permite certification_claimed=true sin bloqueo.
BLOCK si un control no tiene evidencia ni gap explícito.
BLOCK si el schema permite claims legales ambiguos.
```

### POST-H-020-B — Compliance mapping validator

Objetivo: implementar validador semántico para mappings.

Tareas:

```text
1. Implementar src/devpilot_core/compliance/mapping.py.
2. Validar unicidad de control_id/evidence_id.
3. Validar que required_evidence tenga mapping.
4. Validar que no haya certification/legal claims.
5. Validar cobertura de dominios mínimos: security, testing, policy, release, observability, agentic.
6. Crear tests positivos y negativos.
```

Criterios PASS:

```text
PASS si el validator detecta controles sin evidencia.
PASS si bloquea certification_claimed=true.
PASS si bloquea legal_advice_claimed=true.
PASS si reporta coverage por dominio.
```

Criterios BLOCK:

```text
BLOCK si se permite claim de certificación.
BLOCK si controles críticos carecen de evidencia sin BLOCK.
BLOCK si no se valida domain coverage.
```

### POST-H-020-C — Evidence collector y report generator local

Objetivo: generar reportes locales de compliance mapping desde evidencias existentes.

Tareas:

```text
1. Implementar compliance/evidence.py.
2. Implementar compliance/report.py.
3. Recolectar evidencias desde quality-gate, industrial-readiness, test-contracts, project-state y audit packs.
4. No ejecutar comandos externos peligrosos.
5. Generar compliance_mapping_report.json.
6. Agregar CLI compliance mapping report --json --write-report.
```

Criterios PASS:

```text
PASS si el reporte se genera localmente.
PASS si no usa red ni APIs externas.
PASS si missing evidence se reporta explícitamente.
PASS si disclaimer_present=true.
```

Criterios BLOCK:

```text
BLOCK si se envían evidencias fuera del workspace.
BLOCK si se ocultan gaps.
BLOCK si se genera lenguaje de certificación.
```

### POST-H-020-D — Integración con audit packs y quality gate

Objetivo: integrar compliance mapping con audit packs y gates sin convertirlo en certificación.

Tareas:

```text
1. Agregar compliance mapping summary al audit pack manifest si aplica.
2. Agregar subgate compliance-mapping-pack.
3. Validar disclaimers obligatorios.
4. Validar que no haya certification_claimed=true.
5. Agregar test contract post-h-020-compliance-mapping.
6. Integrar evals compliance-pack-integrity como señal adicional.
```

Criterios PASS:

```text
PASS si quality gate bloquea claims certificables.
PASS si audit pack incluye mapping summary sin sobreclaim.
PASS si test-contracts validate reconoce el contrato.
PASS si evals existentes siguen pasando.
```

Criterios BLOCK:

```text
BLOCK si el gate permite compliance certification.
BLOCK si audit pack sugiere auditoría externa completada.
BLOCK si se omiten disclaimers.
```

### POST-H-020-E — Runbook, disclaimers y cierre

Objetivo: documentar operación segura de compliance mapping.

Tareas:

```text
1. Crear docs/05_operations/compliance_mapping_runbook.md.
2. Crear docs/03_security/compliance_mapping_disclaimers.md.
3. Documentar cómo interpretar mapped/partial/gap/not-applicable.
4. Documentar límites: no certificación, no asesoría legal.
5. Ejecutar validaciones focales.
```

Criterios PASS:

```text
PASS si el runbook explica mapeo vs certificación.
PASS si los disclaimers son explícitos.
PASS si los reportes distinguen gaps.
PASS si no hay claims enterprise/compliance certificada.
```

Criterios BLOCK:

```text
BLOCK si los docs afirman cumplimiento certificado.
BLOCK si no se explica límite legal.
BLOCK si no hay criterios para evidencia faltante.
```

## 9. Comandos esperados de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_020_compliance_mapping_schema.py -q
python -m pytest tests/test_post_h_020_compliance_evidence_mapping.py -q
python -m pytest tests/test_post_h_020_compliance_no_certification.py -q
python -m pytest tests/test_post_h_020_compliance_quality_gate.py -q
python -m devpilot_core compliance mapping report --json --write-report
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Sobreclaim de certificación | Alta | certification_claimed=false + gate BLOCK. |
| Evidencia insuficiente | Media-alta | missing evidence explícito. |
| Interpretación legal incorrecta | Alta | disclaimers obligatorios. |
| Drift entre mapping y código | Media-alta | watched_paths y test contracts. |
| Reportes incompletos | Media | schema + validator + quality gate. |

## 11. No-go gates

```text
NO-GO si se declara compliance certificada.
NO-GO si se afirma asesoría legal.
NO-GO si se envían evidencias a terceros.
NO-GO si controles críticos carecen de evidencia sin finding.
NO-GO si el report oculta gaps.
NO-GO si se usa red/API externa.
```

## 12. Definition of Done

```text
- Schemas de control/evidence/report creados y registrados.
- Control mappings y evidence mappings locales creados.
- Validator semántico implementado.
- Report generator local implementado.
- Disclaimers obligatorios documentados.
- Quality gate actualizado.
- Test contract agregado.
- Audit pack integration definida.
- No claims de certificación.
```
