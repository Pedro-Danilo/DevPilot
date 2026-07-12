---
doc_id: POST-H-033-F-DOCS-GOVERNANCE-RULE-REGISTRY-REPORT
title: "POST-H-033-F — Docs governance rule registry"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-033-F — Docs governance rule registry

## Resultado

Estado: `implemented-initial`.

POST-H-033-F agrega un registry declarativo para reglas de documentation governance sin reemplazar el source registry canónico. El source registry sigue declarando fuentes, ownership, estado, criticality, tests y relaciones; el nuevo rule registry declara cómo se gobiernan esas fuentes: severidades, lifecycle permitido, frontmatter requerido, required_tests y reglas de consistencia.

## Artefactos

- `.devpilot/docs_governance/rule_registry.json`: reglas versionadas de governance documental.
- `docs/schemas/docs_governance_rule_registry.schema.json`: contrato estructural `DocsGovernanceRuleRegistry`.
- `src/devpilot_core/docs_governance/rule_registry.py`: loader determinístico, fallback seguro y fail-closed para registry inválido.
- `src/devpilot_core/docs_governance/validator.py`: integración con `DocumentationGovernanceValidator` y exposición de `rule_source`/`catalog_version` en el reporte.
- `tests/test_post_h_033_docs_governance_rule_registry.py`: pruebas focales de schema, fallback, invalidez bloqueante, source-of-truth drift, required_tests y historical authority.

## Criterios PASS cubiertos

- Docs governance sigue bloqueando drift de source-of-truth y required_tests ausentes.
- Las reglas son auditables y versionadas.
- Source registry y rule registry se validan en conjunto.
- Critical/source-of-truth sin tests sigue bloqueando.
- Frontmatter required sigue aplicando donde corresponde.
- El reporte incluye `rule_source` y `catalog_version`.

## Límites

Esta es una primera versión. El fallback Python permanece activo como compatibilidad temporal y no debe retirarse hasta completar evidencia acumulada de equivalencia. No se habilitan LLM judge, red, APIs externas, remote execution, connector write, plugin execution, reglas ejecutables dinámicas ni mutaciones de fuente.

## Validación focal recomendada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_docs_governance_rule_registry.py `
  tests/test_documentation_governance_validator.py `
  tests/test_documentation_source_registry_schema.py `
  tests/test_documentation_governance_backlogs.py `
  tests/test_documentation_governance_sync.py `
  tests/test_schema_validator.py `
  -q

python -m devpilot_core schema validate --schema-id DocsGovernanceRuleRegistry --instance .devpilot\docs_governanceule_registry.json --json
python -m devpilot_core docs-governance validate --json
```
