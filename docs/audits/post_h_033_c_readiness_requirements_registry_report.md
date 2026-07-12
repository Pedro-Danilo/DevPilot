---
doc_id: POST-H-033-C-READINESS-REQUIREMENTS-REGISTRY-REPORT
title: POST-H-033-C — Readiness requirements registry report
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-11
approval: approved
---

# POST-H-033-C — Readiness requirements registry report

## Decisión

PASS preliminar de implementación: el readiness validator usa `.devpilot/readiness/readiness_requirements.json` como fuente primaria para listas de artefactos, conserva fallback Python temporal y bloquea registry inválido para evitar falsos PASS.

## Alcance implementado

- Schema `ReadinessRequirements` registrado en `docs/schemas/readiness_requirements.schema.json`.
- Registry local versionado `.devpilot/readiness/readiness_requirements.json`.
- Loader determinístico `src/devpilot_core/validators/readiness_requirements.py`.
- Integración progresiva con `src/devpilot_core/validators/readiness.py`.
- Tests de compatibilidad, ausencia, drift y registry inválido.
- Manifest `docs/post_h_033_c_manifest.json`.

## Invariantes preservados

- Sin LLM judge.
- Sin red ni APIs externas.
- Sin ejecución remota, conectores write o plugins.
- Sin mutaciones de fuente en runtime.
- MIASI sigue requerido para strict readiness.
- Parser/frontmatter/artifact validation permanecen en código determinístico.
- Fallback Python existe solo como compatibilidad temporal.

## Limitaciones

Esta es una primera versión `implemented-initial`. El fallback Python sigue presente para compatibilidad y debe retirarse solo después de evidencia acumulada de equivalencia entre registry, onboarding readiness preview y validation gateway. No se migran reglas MIASI ni docs-governance en este sprint.

## Validación focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_033_readiness_requirements_registry.py `
  tests/test_precode_readiness.py `
  tests/test_post_h_024_onboarding_readiness_preview.py `
  tests/test_validation_gateway.py `
  tests/test_schema_validator.py `
  -q

python -m devpilot_core schema validate --schema-id ReadinessRequirements --instance .devpiloteadinesseadiness_requirements.json --json
```
