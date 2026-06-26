---
doc_id: "POST-H-009-D-AUDIT"
title: "POST-H-009-D — Backlog governance y derivados del roadmap"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
related_backlog: "docs/backlogs/POST-H-009_documentation_governance.md"
---

# POST-H-009-D — Backlog governance y derivados del roadmap

## 1. Propósito

Documentar la implementación inicial de la governance determinística para backlogs ejecutables derivados del roadmap post-H.

## 2. Implementado

```text
- DocumentationBacklogGovernanceValidator.
- Registro gobernado de backlogs POST-H-002..POST-H-025 en DocumentationSourceRegistry.
- Validación de naming convention docs/backlogs/POST-H-###_<slug>.md.
- Validación de frontmatter mínimo para backlogs existentes.
- Validación de doc_id, id, priority y roadmap_source contra el roadmap machine-readable.
- Manejo informativo de backlogs futuros faltantes como planned.
- Métricas backlog_* dentro de DocumentationGovernanceReport.
- Contrato TCR v1/v2 para post-h-009-documentation-backlog-governance.
```

## 3. Implementado inicial

Esta implementación es `implemented-initial`. Cubre consistencia contractual y trazabilidad de backlogs, pero no juzga calidad semántica profunda de cada backlog ni integra todavía un subgate `docs-governance` dentro del `quality-gate hardening`.

## 4. Corrección documental heredada

Los backlogs draft `POST-H-010..POST-H-025` no declaraban `approval`. Se agregó:

```yaml
approval: "pending_owner_review"
```

Esto no cambia su estado `draft`; solo completa metadata documental mínima y evita drift futuro.

## 5. Comandos de verificación

```powershell
python -m pytest tests/test_documentation_governance_backlogs.py tests/test_documentation_governance_sync.py tests/test_documentation_governance_validator.py tests/test_post_h_009_documentation_governance.py tests/test_post_h_006_b_declarative_registry.py -q
python -m devpilot_core docs-governance validate --json
python -m devpilot_core docs-governance report --write-report --json
python -m devpilot_core schema validate --schema-id DocumentationGovernanceReport --instance outputs/reports/documentation_governance_report.json --json
python -m devpilot_core schema validate --schema-id DocumentationSourceRegistry --instance .devpilot/docs_governance/source_registry.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## 6. Criterios PASS

```text
PASS si backlog_governance_passed=true.
PASS si backlogs_expected_total=24.
PASS si backlogs_registered_total=24.
PASS si backlogs_checked_total=24.
PASS si backlogs_planned_missing_total se reporta como info cuando aplique.
PASS si blocking_findings_total=0.
PASS si no se usa red, API externa, LLM judge ni mutación de fuentes.
```

## 7. Criterios BLOCK

```text
BLOCK si un backlog existente del roadmap no está registrado.
BLOCK si un path existente rompe la convención POST-H-###_<slug>.md.
BLOCK si falta frontmatter mínimo en backlog existente.
BLOCK si doc_id/id/priority/roadmap_source contradicen el roadmap JSON.
BLOCK si el validator muta fuentes o usa servicios externos.
```

## 8. Riesgos y límites

| Riesgo | Mitigación |
|---|---|
| Falso positivo por parsing Markdown | Reglas frontmatter mínimas y determinísticas. |
| Tratar backlogs futuros como errores prematuros | Missing future backlog se reporta como info planned. |
| Burocracia documental | Registry y validator automatizan el control. |
| Calidad semántica no evaluada | Diferido; no usar como claim de suficiencia funcional profunda. |
| Falta de quality-gate subgate | Diferido a POST-H-009-E. |

## 9. Seguridad

```text
local_first=true
dry_run=true
read_only=true
network_used=false
external_api_used=false
llm_judge_used=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```
