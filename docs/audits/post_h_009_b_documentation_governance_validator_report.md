# POST-H-009-B — Documentation governance validator report

## Propósito

`POST-H-009-B` implementa el primer validator ejecutable de gobernanza documental para DevPilot Local. El objetivo es validar la capa mínima de metadata definida en `.devpilot/docs_governance/source_registry.json`: existencia de fuentes, ownership, `status_required`, frontmatter de documentos approved, consistencia de `doc_id` y existencia de tests requeridos.

## Estado

Estado: `implemented-initial`.

La implementación es local-first, deterministic, read-only y no usa red, APIs externas ni LLM judge.

## Artefactos creados

```text
src/devpilot_core/docs_governance/validator.py
src/devpilot_core/docs_governance/report.py
docs/audits/post_h_009_b_documentation_governance_validator_report.md
docs/post_h_009_b_manifest.json
tests/test_documentation_governance_validator.py
```

## Artefactos modificados

```text
README.md
.devpilot/project_state.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
docs/05_operations/runbook.md
docs/05_operations/documentation_governance.md
docs/POST-H-009_documentation_governance.md
docs/backlogs/POST-H-009_documentation_governance.md
docs/release/CHANGELOG.md
src/devpilot_core/cli.py
src/devpilot_core/cli_registry/registry.py
src/devpilot_core/docs_governance/__init__.py
tests/test_post_h_006_b_declarative_registry.py
tests/test_post_h_009_documentation_governance.py
tests/test_project_global_state.py
```

## Comando principal

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core docs-governance validate --write-report --json
```

El comando genera `outputs/reports/documentation_governance_report.json` y `.md` únicamente si se usa `--write-report`.

## Controles implementados

```text
- DOCUMENTATION_SOURCE_MISSING: bloquea fuentes registradas inexistentes.
- DOCUMENTATION_OWNER_MISSING: bloquea owner vacío en registry.
- DOCUMENTATION_STATUS_REQUIRED_MISSING: bloquea status_required vacío.
- DOCUMENTATION_FRONTMATTER_REQUIRED: bloquea Markdown approved sin frontmatter.
- DOCUMENTATION_DOC_ID_MISMATCH: bloquea doc_id inconsistente.
- DOCUMENTATION_STATUS_MISMATCH: bloquea status inconsistente.
- DOCUMENTATION_REQUIRED_TEST_MISSING: bloquea tests requeridos inexistentes.
- DOCUMENTATION_HISTORICAL_ACTIVE_REVIEW: advierte si un historical queda activo como autoridad actual.
```

## Inconsistencia heredada corregida

El backlog `POST-H-009` estaba aprobado pero no declaraba `approval` en frontmatter. Se agregó:

```yaml
approval: "approved_by_owner"
```

en `docs/backlogs/POST-H-009_documentation_governance.md` y en su espejo `docs/POST-H-009_documentation_governance.md`.

## Límites explícitos

```text
- No implementa drift Markdown ↔ JSON; queda para POST-H-009-C.
- No gobierna todos los backlogs derivados; queda para POST-H-009-D.
- No integra docs-governance en quality-gate hardening; queda para POST-H-009-E.
- No reescribe documentación histórica.
- No usa red, APIs externas ni LLM judge.
```

## Criterios PASS/BLOCK

PASS:

```text
- docs-governance validate pasa sin findings bloqueantes.
- DocumentationGovernanceReport valida contra schema.
- TCR v1/v2 registra el contrato del validator.
- CLI registry registra docs-governance.validate como comando gobernado.
```

BLOCK:

```text
- Source-of-truth crítico sin test.
- Markdown approved sin frontmatter.
- doc_id/status inconsistente entre registry y source.
- Validator requiere red/API/LLM judge o muta fuentes.
```

## Conclusión

`POST-H-009-B` queda implementado como primera versión ejecutable del validator documental. Aporta control temprano contra drift por metadata, pero no sustituye el futuro sync validator ni el quality-gate documental final del backlog.
