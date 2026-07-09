---
doc_id: "POST-H-029-A-TEST-PROFILE-TAXONOMY-REPORT"
title: "POST-H-029-A — Test profile taxonomy report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
created: "2026-07-09"
updated: "2026-07-09"
approval: "approved"
sprint: "POST-H-029-A"
---

# POST-H-029-A — Test profile taxonomy report

## Decision

`PASS` — POST-H-029-A queda implementado como versión `implemented-initial/local-first`.

## Alcance implementado

- `TestProfileTaxonomy` schema-backed.
- `.devpilot/testing/test_profile_taxonomy.json` con diez perfiles operacionales: `always-fast`, `p0-critical`, `security`, `impact`, `release`, `release-candidate-local`, `docs-historical`, `full`, `manual` y `nightly-local`.
- Alias legacy `smoke`, `unit` y `all` preservados y mapeados a la nueva taxonomía.
- `src/devpilot_core/testing/profile_taxonomy.py` con runner read-only y comando `python -m devpilot_core tests taxonomy --json`.
- `.devpilot/testing/test_profiles.json` actualizado para que `tests.run` conserve perfiles controlados y approval-gated, sin shell arbitrario.
- Validación de comandos permitidos, timeouts, costos, aprobación para perfiles de alto riesgo y safety flags.

## No-go gates

No se habilita:

- ejecución arbitraria de shell;
- ejecución de tests desde JSON de taxonomía;
- red o APIs externas por defecto;
- mutaciones de fuente;
- remote execution;
- connector write;
- plugin execution.

## Estado y límites

POST-H-029-A no implementa reglas declarativas de impacto ni recomendaciones CLI avanzadas. Esa evolución corresponde a POST-H-029-B y POST-H-029-C. Tampoco reemplaza `pytest -q`: la regresión completa sigue preservada y deberá formalizarse con POST-H-029-E.
