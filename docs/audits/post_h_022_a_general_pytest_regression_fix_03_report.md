---
doc_id: "POST-H-022-A-GENERAL-PYTEST-REGRESSION-FIX-03-REPORT"
status: "approved"
created_by: "POST-H-022-A-FIX-03"
scope: "general-pytest-regression-fix"
---

# POST-H-022-A General Pytest Regression Fix 03

## Diagnostico

La tercera ejecucion general reporto `1456 passed, 1 failed, 0 errors`.

El unico fallo restante fue `test_documentation_source_registry_validates_against_schema`.

La causa real fue que `.devpilot/docs_governance/source_registry.json` conservaba 10 entradas con `classification` fuera del enum permitido por `docs/schemas/documentation_source_registry.schema.json`:

- `source_of_truth`
- `schema`
- `audit-report`
- `manifest`
- `test-contract`

El FIX-02 no corrigio el caso porque el script buscaba el enum en una ruta simple del schema, pero el schema real define `classification.enum` bajo `$defs.document.properties.classification.enum`.

## Correccion

- Se corrigieron las 10 entradas invalidas en `.devpilot/docs_governance/source_registry.json`.
- Se actualizo `scripts/post_h_022_a_fix_source_registry.py` para leer el enum desde `$defs` y, como fallback, desde la ruta simple.
- Se agrego el alias `source_of_truth -> source-of-truth`.

## Validacion

- `invalid_classifications_total=0`.
- `missing_required_total=0`.
- `docs-governance validate --json`: PASS, `blocking_findings_total=0`.
- `cli-registry guard --json`: PASS.

`pytest` y `schema validate` no pudieron ejecutarse completamente en este contenedor por dependencias ausentes (`pytest`, `jsonschema`). La validacion estructural equivalente del campo fallido se ejecuto directamente contra el enum real del schema.

## Alcance

No modifica runtime productivo. No habilita red, APIs externas, ejecucion remota ni acciones destructivas.
