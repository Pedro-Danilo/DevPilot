---
doc_id: "POST-H-029-C-RECOMMENDATIONS-REPORT"
title: "POST-H-029-C — Test impact CLI recommendations report"
status: "approved"
version: "1.0.0"
updated: "2026-07-09"
owner: "Ordóñez"
created: "2026-07-09"
phase: "POST-FASE-H"
approval: "approved"
---

# POST-H-029-C — Test impact CLI recommendations report

## Decisión

PASS — implementación inicial local-first.

## Alcance implementado

POST-H-029-C agrega una salida normalizada sobre `test-impact analyze-v2` mediante `TestImpactRecommendationReport`.

La implementación permite distinguir:

- `matched_contracts`;
- `matched_rules` provenientes de `TestImpactRuleRegistry`;
- `recommended_profiles`;
- `recommended_tests`;
- `recommended_commands`;
- `run_now`;
- `run_before_closure`;
- `manual_review`;
- `residual_risk`;
- `full_regression_required`;
- `waiver_required_if_full_regression_skipped`.

## Seguridad

- `tests_executed=false`.
- `network_used=false`.
- `external_api_used=false`.
- `remote_execution_enabled=false`.
- `connector_write_enabled=false`.
- `plugin_execution_enabled=false`.
- Los comandos recomendados son datos, no ejecución automática.

## Artefactos principales

- `docs/schemas/test_impact_recommendation_report.schema.json`.
- `src/devpilot_core/testing/recommendations.py`.
- `src/devpilot_core/testing/impact_v2.py`.
- `tests/test_post_h_029_test_impact_cli_recommendations.py`.
- `docs/post_h_029_c_manifest.json`.

## Validación esperada

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_029_test_impact_cli_recommendations.py -q
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/testing/impact_v2.py --json --write-report
python -m devpilot_core schema validate --schema-id TestImpactRecommendationReport --instance outputs/reports/test_impact_recommendation_report.json --json
```

## Limitaciones

Esta es una primera versión. No aprueba waivers, no ejecuta pruebas y no cierra automáticamente backlogs. POST-H-029-D debe formalizar el perfil `release-candidate-local`; POST-H-029-E debe agregar el guard histórico y reglas bloqueantes de cierre/regresión.
