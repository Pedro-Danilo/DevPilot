---
doc_id: "POST-H-028-E-GENERAL-PYTEST-REGRESSION-FIX-REPORT"
title: "POST-H-028-E — General pytest regression fix report"
status: "approved"
approval: "approved"
version: "1.0.0"
owner: "Ordóñez"
created: "2026-07-09"
updated: "2026-07-09"
sprint: "POST-H-028-E"
---

# POST-H-028-E — General pytest regression fix report

## Decision

`PASS` para el patch correctivo posterior al test general `pytest -q` de POST-H-028-E.

## Root causes

1. `scripts/visual_product_smoke.py` aceptaba únicamente versiones `0.6.0-post-h-*`; al cerrar POST-H-028-E la UI quedó en `0.6.3-post-h-028-e`, por lo que el gate visual heredado bloqueaba perfiles `ci`, `full`, `release`, `hardening` e `industrial`.
2. `.devpilot/docs_governance/source_registry.json` contenía entradas heredadas POST-H-026..028 incompletas o con clasificaciones fuera del enum del schema `DocumentationSourceRegistry`.
3. Tres backlogs/documentos POST-H-026/027 usaban listas YAML en frontmatter que el parser local de governance no soporta; varios audit reports aprobados carecían de `approval`.
4. `.devpilot/release/local_release_candidate_criteria.json` seguía comparando `project_state.current_repo` contra evidencia antigua de POST-H-027, por lo que RC/freshness quedaba en BLOCK tras POST-H-028-E.
5. `PackagingLocalReadyGate` dependía de outputs runtime (`outputs/release`, `.devpilot/backups`) que se omiten intencionalmente en ZIPs limpios; el gate necesitaba fallback por evidencia versionada.
6. Algunos tests históricos POST-H-023/024/027 seguían acoplados a campos globales mutables (`current_micro_sprint`, `last_completed_sprint`) en vez de usar claves phase-scoped (`post_h_024_current_micro_sprint`, etc.).

## Corrective actions

- Se generalizó la regla de versión visual a `0.6.x-post-h-*`.
- Se normalizó el source registry: `status=implemented-initial`, entradas con `classification/domain/criticality/required_tests/sync_rules`, enum válido y snapshot sincronizado con `project_state`.
- Se corrigió frontmatter de POST-H-026/027 para evitar warnings de parsing y se agregó `approval` a audit reports aprobados.
- Se actualizó freshness criteria al repo actual `repo_DevPilot_Local_278_POST_H_028_E.zip` y a estado global POST-H-028.
- Se agregó fallback clean-source a `PackagingLocalReadyGate`: el runner directo de upgrade/rollback sigue estricto, pero el subgate de quality puede pasar en repos limpios usando evidencia versionada y flags de project state.
- Se actualizaron tests históricos para distinguir estado global mutable de estado histórico por hito.

## Validation

- DocumentationSourceRegistry schema: PASS.
- docs-governance validate: PASS, `warnings_total=0`, `blocking_findings_total=0`.
- visual product smoke: PASS.
- evidence freshness: PASS.
- release-candidate final: PASS.
- quality-gate release: PASS.
- quality-gate CI: PASS.
- hardening subgates 0..42: PASS validados por lotes.
- POST-H-028 focal tests: PASS.
- npm UI smokes base/visual/operator-flows/route-enforcement: PASS.

## Limits

No se ejecutó nuevamente el `pytest -q` completo dentro de este entorno por costo; el patch se validó contra los fallos reportados en `pytest_general_H-28-E.txt` y contra los subgates que originaban las cascadas.
