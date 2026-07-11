---
doc_id: POST-H-033-B-FRONTMATTER-SCHEMA-BACKED-REPORT
title: "POST-H-033-B — Frontmatter schema-backed validator report"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-033-B — Frontmatter schema-backed validator report

## Resultado

Estado: `implemented-initial`.

POST-H-033-B migra las reglas configurables del validador de frontmatter a un catálogo local versionado y validado por schema: `.devpilot/validation/frontmatter_catalog.json`.

## Alcance implementado

- Schema `FrontmatterMetadata` en `docs/schemas/frontmatter_metadata.schema.json`.
- Catálogo `.devpilot/validation/frontmatter_catalog.json` con campos requeridos, statuses permitidos, patrones regex, severidades y regla `approved_requires_approval`.
- Módulo `src/devpilot_core/validators/frontmatter_catalog.py` para carga validada y fallback seguro.
- Integración progresiva en `src/devpilot_core/validators/frontmatter.py`.
- Preservación de parser dependency-free, finding IDs históricos y severidades históricas.
- Reporte de `rule_source` y `catalog_version` en `CommandResult.data` y metadata de findings.

## Límites de seguridad

- No se agrega dependencia YAML externa.
- No se usa LLM judge.
- No se habilita red, APIs externas, remote execution, connector write, plugin execution ni mutaciones de fuente.
- Las reglas críticas no son desactivables desde JSON sin ADR/backlog.
- El fallback Python queda activo como compatibilidad temporal y reproduce las reglas históricas.

## Criterios PASS

- Catálogo valida contra `FrontmatterMetadata`.
- Frontmatter sigue deterministic.
- Documentos existentes conservan compatibilidad de hallazgos.
- Casos negativos para status, semver, fecha y doc_id están cubiertos.
- Catálogo inválido o ausente no abre bypass: se activa fallback seguro.

## Comandos de validación focal

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_033_frontmatter_schema_backed_validator.py -q
python -m devpilot_core schema validate --schema-id FrontmatterMetadata --instance .devpilot\validation\frontmatter_catalog.json --json
```

## Limitaciones

Esta es una migración inicial. La eliminación del fallback requiere evidencia adicional de equivalencia y deberá coordinarse con los siguientes micro-sprints POST-H-033-C a POST-H-033-F.
