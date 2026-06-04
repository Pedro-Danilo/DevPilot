---
title: SBOM Policy
doc_id: MIPS-TPL-SBOM_POLICY
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_standard: MIPS-DOC-011 — DevOps, CI/CD, release y supply chain
template_id: sbom_policy
---

# SBOM Policy

## 1. Propósito

Definir cuándo, cómo y con qué formato se genera, conserva y usa el SBOM del proyecto.

## 2. Cuándo usarla

Usar esta plantilla cuando el proyecto de software requiera planificar, validar o auditar procesos de DevOps, CI/CD, release, despliegue, rollback, artefactos o cadena de suministro.

## 3. Campos obligatorios

| Campo | Descripción | Obligatorio |
|---|---|---:|
| project_id | Identificador del proyecto. | Sí |
| project_name | Nombre del proyecto. | Sí |
| owner | Responsable principal. | Sí |
| environment | Local/dev/staging/prod, si aplica. | Condicional |
| version | Versión relacionada. | Condicional |
| commit_sha | Commit relacionado. | Condicional |
| artifacts | Artefactos involucrados. | Condicional |
| evidence | Evidencia requerida. | Sí |
| risks | Riesgos identificados. | Sí |
| approvals | Aprobaciones necesarias. | Condicional |
| rollback_or_mitigation | Reversión o mitigación. | Condicional |
| miasi_applicable | Indica si aplica MIASI. | Sí |

## 4. Campos opcionales

| Campo | Descripción |
|---|---|
| related_issue | Issue/tarea asociada. |
| related_pr | PR/MR asociado. |
| sbom_path | Ruta del SBOM. |
| provenance_path | Ruta de provenance. |
| security_report | Ruta del reporte de seguridad. |
| test_report | Ruta del reporte de pruebas. |
| post_release_notes | Observaciones posteriores al despliegue. |

## 5. Ejemplo completo

```yaml
project_id: "demo-commerce"
project_name: "MicroCommerce Agent"
owner: "tech-lead"
environment: "staging"
version: "0.3.0-rc.1"
commit_sha: "abc123"
artifacts:
  - name: "backend-api"
    type: "container-image"
    version: "0.3.0-rc.1"
evidence:
  tests: "outputs/reports/release_test_report.md"
  security: "outputs/security/security_gate_report.md"
  quality_gate: "outputs/reports/quality_gate_report.md"
risks:
  - "database migration affects orders table"
approvals:
  - role: "technical_lead"
    status: "approved"
rollback_or_mitigation: "redeploy previous image and disable feature flag order-v2"
miasi_applicable: true
miasi_evidence:
  eval_report: "outputs/evals/agent_eval_report.json"
  policy_report: "outputs/security/policy_gate_report.json"
```

## 6. Criterios de revisión

- La plantilla está completa.
- La evidencia existe o está explícitamente marcada como pendiente.
- Los riesgos tienen mitigación.
- Las aprobaciones están definidas.
- Si MIASI aplica, existen artefactos agentic relacionados.

## 7. Criterios de rechazo

- Falta owner.
- Falta evidencia de pruebas o seguridad cuando aplica.
- No hay rollback/mitigación en cambios productivos.
- Hay secretos expuestos.
- El artefacto no es trazable.
- MIASI aplica pero no hay evaluación/policy/trazas.

## 8. Relación con el ciclo de vida

Esta plantilla se usa principalmente en las fases:

```text
18 Release
19 Despliegue
20 Operación
21 Monitoreo
22 Gestión de incidentes
23 Mantenimiento evolutivo
```

## 9. Relación con quality gates

Debe alimentar los gates de:

```text
CI PASS
security gate PASS
release readiness PASS
deployment readiness PASS
post-release verification PASS
MIASI gates PASS cuando aplique
```
