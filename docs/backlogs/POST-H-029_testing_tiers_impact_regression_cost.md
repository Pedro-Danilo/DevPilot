---
doc_id: "POST-H-029-BACKLOG"
id: "POST-H-029"
title: "POST-H-029 — Testing tiers, impacto y costo de regresion"
status: "approved"
version: "1.0.0"
owner: "Ordonez"
created: "2026-07-07"
updated: "2026-07-09"
approval: "approved"
phase: "POST-FASE-H"
priority: "P0"
roadmap_wave: "Ola 4"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
source_repo: "repo_DevPilot_Local_278_POST_H_028_E.zip"
depends_on: "POST-H-026, POST-H-027, POST-H-028"
local_first: true
dry_run_default: true
read_only_by_default: true
no_remote_execution_enabled: true
no_external_apis_required: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
claims_allowed: "production-ready-local"
claims_forbidden: "enterprise-ready, remote-ready, SaaS-ready, compliance-certified"
implementation_status: "active/implemented-initial-post-h-029-d"
current_micro_sprint: "POST-H-029-D"
next_micro_sprint: "POST-H-029-E"
---

# POST-H-029 — Testing tiers, impacto y costo de regresion

POST-H-029-D queda implementado como `implemented-initial/local-first`: agrega `ReleaseCandidateTestProfileReport`, `.devpilot/testing/release_candidate_test_profile.json`, validador `tests release-candidate-profile`, sincronización con taxonomy/TCR/tests.run y reglas explícitas de escalamiento a full regression. POST-H-029-E queda pendiente para el guard histórico bloqueante.


## Estado de implementación

POST-H-029 entra a implementación con status `approved`. POST-H-029-A queda implementado como `implemented-initial/local-first`: define la taxonomía operacional de perfiles, valida comandos permitidos y conserva `tests.run` approval-gated. POST-H-029-A/B/C/D quedan implementados como primeras versiones local-first. El micro-sprint POST-H-029-E permanece pendiente para regression guard histórico.

## 1. Dictamen ejecutivo

POST-H-029 debe hacer sostenible la evolucion de DevPilot mediante perfiles de prueba accionables, reglas de impacto confiables y controles explicitos sobre cuando se requiere regresion completa.

El roadmap v3 define la Ola 4 asi:

```text
Ola 4 - POST-H-029: Testing tiers, impacto y costo de regresion

Objetivo:
Hacer sostenible la evolucion con perfiles de pruebas accionables.

Micro-sprints:
- POST-H-029-A - Test profile taxonomy
- POST-H-029-B - TCR v2 impact rules
- POST-H-029-C - Test impact CLI recommendations
- POST-H-029-D - Release candidate test profile
- POST-H-029-E - Historical regression guard
```

Este backlog conserva esos cinco micro-sprints. El alcance es suficiente y necesario: taxonomia primero, reglas TCR v2 despues, recomendaciones CLI como tercera capa, perfil release candidate como cuarta capa y guard historico/final como cierre.

## 2. Fuentes consultadas

Fuentes obligatorias verificadas:

```text
/workspace/.cache/01-devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md
/workspace/.cache/02-repo_DevPilot_Local_262_POST_H_025_E.zip
/workspace/.cache/03-devpilot_onboarding_report_final_compilado.md
```

Repo descomprimido:

```text
/workspace/repo_DevPilot_Local_262_POST_H_025_E
```

Archivos consultados de forma focal:

```text
docs/04_quality/post_h_test_cost_assessment.md
docs/04_quality/test_contract_registry_2_design.md
docs/backlogs/POST-H-003_test_contract_registry_2.md
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/testing/test_profiles.json
docs/schemas/test_contract_registry.schema.json
docs/schemas/test_contract_registry_v2.schema.json
src/devpilot_core/testing/contracts.py
src/devpilot_core/testing/contracts_v2.py
src/devpilot_core/testing/profiles.py
src/devpilot_core/testing/profiles_v2.py
src/devpilot_core/testing/impact.py
src/devpilot_core/testing/impact_v2.py
src/devpilot_core/testing/tests_run.py
tests/test_test_contract_registry.py
tests/test_test_contract_registry_v2.py
tests/test_test_contract_registry_profiles_v2.py
tests/test_test_contract_registry_migration.py
tests/test_project_global_state.py
tests/test_schema_registry.py
```

## 3. Estado base que hereda POST-H-029

El repo 262 ya contiene una base de testing madura, pero aun incompleta para control fino de costo:

```text
- TCR v1 vigente.
- TCR v2 vigente con 188 contratos.
- TCR v2 valida schema y semantica.
- Perfiles TCR v2 existentes: p0-critical, security, release, impact, docs-historical.
- execution_profile en TCR v2: impact, release, always, manual.
- test-impact analyze v1.
- test-impact analyze-v2 con heuristicas para policy/security, schemas, CLI/API, agentes y release.
- tests.run controlado por perfiles y approval.
- quality-gate hardening incluye test-contract-registry y test-contract-registry-v2.
- test_profiles.json actual solo contiene smoke, unit y all.
```

Metricas observadas en la fuente actual:

```text
- TCR v2 total: 188 contratos.
- criticality: P0=13, P1=75, P2=100.
- risk_level: critical=25, high=69, medium=93, low=1.
- execution_profile: impact=106, release=43, always=37, manual=2.
- test_cost no esta efectivamente granularizado en el payload actual.
- tests/ contiene una suite amplia; el informe final y logs previos registran costos altos de pytest -q completo.
```

Brechas principales:

```text
- test_profiles.json no refleja tiers industriales reales.
- TCR v2 tiene perfiles, pero falta taxonomia operacional completa.
- test_cost/cost_class no esta normalizado de forma util.
- impact analyzer v2 es conservador, pero todavia depende de heuristicas para dominios P0.
- paths no mapeados pueden producir falsa confianza o forzar full regression.
- no existe perfil release-candidate-local formal como contrato de ejecucion.
- no existe guard historico que obligue regresion completa en cierres o cambios transversales.
```

## 4. Objetivo del backlog

Implementar una estrategia de testing por tiers que permita:

```text
1. Elegir pruebas focales con menor costo.
2. Reducir riesgo de sub-testing en dominios P0/P1.
3. Hacer explicito cuando se requiere pytest -q completo.
4. Convertir TCR v2 en fuente accionable para impacto/costo/perfiles.
5. Mantener trazabilidad entre cambios, contratos, pruebas y quality gates.
6. Evitar que una regresion focal se presente como sustituto automatico de cierre industrial.
```

## 5. No objetivos

POST-H-029 no incluye:

```text
- Reducir cobertura eliminando pruebas historicas.
- Saltar pytest -q en cierres de backlog cuando aplique.
- Ejecutar tests arbitrarios desde JSON.
- Permitir shell arbitrario en tests.run.
- Habilitar red o APIs externas en pruebas por defecto.
- Introducir CI cloud obligatorio.
- Convertir test-impact en decision automatica final.
- Reemplazar juicio humano para cambios P0/P1.
```

## 6. Principios de diseno

```text
1. Impact selection is advisory, not blind automation.
2. Tiers reduce cost, but do not erase final regression duties.
3. Unknown impact must increase verification, not reduce it.
4. P0/P1 changes require explicit justification of selected tests.
5. Test commands remain data until explicitly executed.
6. No arbitrary shell execution from registries.
7. No network/external API tests by default.
8. Historical documentation tests preserve continuity but are not runtime coverage.
9. Release candidate profile must be stricter than development impact profile.
10. Full regression remains mandatory for closure, release, unmapped P0 or high-risk drift.
```

## 7. Artefactos globales esperados al cierre de POST-H-029

Nuevos artefactos sugeridos:

```text
docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md
docs/POST-H-029_testing_tiers_impact_regression_cost.md
docs/schemas/test_profile_taxonomy.schema.json
docs/schemas/test_impact_rule_registry.schema.json
docs/schemas/test_impact_recommendation_report.schema.json
docs/schemas/release_candidate_test_profile_report.schema.json
docs/schemas/historical_regression_guard_report.schema.json
.devpilot/testing/test_profile_taxonomy.json
.devpilot/testing/test_impact_rules.json
.devpilot/testing/release_candidate_test_profile.json
src/devpilot_core/testing/profile_taxonomy.py
src/devpilot_core/testing/impact_rules.py
src/devpilot_core/testing/recommendations.py
src/devpilot_core/testing/release_candidate_profile.py
src/devpilot_core/testing/historical_regression_guard.py
tests/test_post_h_029_test_profile_taxonomy.py
tests/test_post_h_029_tcr_v2_impact_rules.py
tests/test_post_h_029_test_impact_cli_recommendations.py
tests/test_post_h_029_release_candidate_test_profile.py
tests/test_post_h_029_historical_regression_guard.py
docs/audits/post_h_029_a_test_profile_taxonomy_report.md
docs/audits/post_h_029_b_tcr_v2_impact_rules_report.md
docs/audits/post_h_029_c_test_impact_cli_recommendations_report.md
docs/audits/post_h_029_d_release_candidate_test_profile_report.md
docs/audits/post_h_029_e_historical_regression_guard_report.md
docs/post_h_029_a_manifest.json
docs/post_h_029_b_manifest.json
docs/post_h_029_c_manifest.json
docs/post_h_029_d_manifest.json
docs/post_h_029_e_manifest.json
```

Runtime outputs esperados, no versionables:

```text
outputs/reports/test_profile_taxonomy_report.json
outputs/reports/test_impact_rule_registry_report.json
outputs/reports/test_impact_recommendation_report.json
outputs/reports/release_candidate_test_profile_report.json
outputs/reports/historical_regression_guard_report.json
```

Artefactos a mantener sincronizados:

```text
README.md
docs/04_quality/post_h_test_cost_assessment.md
docs/04_quality/test_strategy.md
docs/04_quality/test_contract_registry_2_design.md
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
docs/schemas/schema_catalog.json
.devpilot/project_state.json
.devpilot/docs_governance/source_registry.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/testing/test_profiles.json
src/devpilot_core/cli.py o command registry equivalente
src/devpilot_core/quality/gate.py si se integra subgate testing-tiers-ready
```

## 8. Modelo de decision del backlog

POST-H-029 puede cerrar como PASS solo si:

```text
- test_profile_taxonomy_valid = true
- tcr_v2_impact_rules_valid = true
- impact_cli_recommendations_valid = true
- release_candidate_profile_valid = true
- historical_regression_guard_valid = true
- p0_p1_domains_mapped = true
- unknown_impact_escalates = true
- unsafe_commands_blocked = true
- network_external_api_tests_disabled_by_default = true
- full_regression_rules_documented = true
```

Debe emitir BLOCK si:

```text
- Un cambio P0/P1 puede recibir recomendacion de "no tests".
- Un path no mapeado reduce la verificacion en lugar de escalarla.
- test_profiles.json permite shell arbitrario.
- TCR v2 recommended_commands incluye comandos fuera de allowlist.
- release-candidate profile omite project-state, docs-governance, schemas, TCR, quality gate o production-ready-local-final.
- historical regression guard permite cerrar backlog sin justificacion de full regression o waiver aprobado.
- El backlog reduce safety flags de testing.
```

## 9. Micro-sprint POST-H-029-A — Test profile taxonomy

### Objetivo

Definir una taxonomia operacional de perfiles de prueba que distinga desarrollo rapido, impacto por cambio, seguridad, release candidate, documentacion historica, regresion completa y manual/nightly.

### Justificacion

TCR v2 ya contiene `execution_profile`, pero `test_profiles.json` actual solo tiene `smoke`, `unit` y `all`. Esa brecha impide que el operador use perfiles accionables y repetibles sin depender de seleccion manual.

### Alcance

Incluye:

```text
- Crear TestProfileTaxonomy schema.
- Crear .devpilot/testing/test_profile_taxonomy.json.
- Normalizar perfiles: always-fast, p0-critical, security, impact, release, release-candidate-local, docs-historical, full, manual, nightly-local.
- Definir costo esperado, timeout, prerequisitos, comandos permitidos y condiciones de uso.
- Mapear perfiles actuales smoke/unit/all a la nueva taxonomia sin romper compatibilidad.
- Actualizar test_profiles.json para reflejar perfiles controlados, sin shell arbitrario.
- Mantener tests.run approval-gated para ejecucion real.
```

No incluye:

```text
- Ejecutar pruebas desde el taxonomy.
- Eliminar perfiles historicos.
- Integrar CI cloud.
```

### Artefactos esperados

```text
docs/schemas/test_profile_taxonomy.schema.json
.devpilot/testing/test_profile_taxonomy.json
src/devpilot_core/testing/profile_taxonomy.py
tests/test_post_h_029_test_profile_taxonomy.py
docs/audits/post_h_029_a_test_profile_taxonomy_report.md
docs/post_h_029_a_manifest.json
```

### Criterios PASS

```text
- Taxonomy valida contra schema.
- Perfiles minimos existen.
- Cada perfil declara proposito, costo, timeout, comandos permitidos, safety flags y uso recomendado.
- Perfiles con riesgo alto requieren approval cuando ejecutan.
- No hay shell arbitrario.
- smoke/unit/all siguen documentados como aliases o perfiles legacy controlados.
- README/runbook/test strategy quedan sincronizados.
```

### Criterios BLOCK

```text
- Un perfil permite red/API externa por defecto.
- Un perfil ejecuta mutaciones sin approval.
- full regression se elimina o queda opcional sin regla.
- release-candidate-local no existe.
- Los perfiles quedan solo documentales y no validables.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_029_test_profile_taxonomy.py `
  tests/test_test_contract_registry_profiles_v2.py `
  tests/test_test_contract_registry_v2.py `
  tests/test_schema_registry.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core schema validate --schema-id TestProfileTaxonomy --instance .devpilot/testing/test_profile_taxonomy.json --json
python -m devpilot_core tests taxonomy --json
python -m devpilot_core tests profiles --json
```

## 10. Micro-sprint POST-H-029-B — TCR v2 impact rules

### Objetivo

Agregar reglas declarativas de impacto para que TCR v2 pueda mapear cambios a dominios, contratos, perfiles y escalamiento de verificacion con menor dependencia de heuristicas hardcodeadas.

### Justificacion

`TestImpactAnalyzerV2` aplica heuristicas utiles para policy/security, schemas, CLI/API, agentes y release. POST-H-029-B debe mover esa logica hacia un registry versionado y revisable, dejando el codigo como interprete de reglas.

### Alcance

Incluye:

```text
- Crear TestImpactRuleRegistry schema.
- Crear .devpilot/testing/test_impact_rules.json.
- Definir reglas por path/domain para policy, approval, security, schemas, CLI/API, UI/API, release, runtime state, agents, RAG, connectors, plugins, remote, enterprise, production readiness.
- Definir escalamiento por criticidad/riesgo.
- Definir "unmatched path policy": review-required o full-regression-required segun area.
- Enriquecer TCR v2 con owner_domain, service_boundary, subgate_id, schema_ids cuando aplique.
- Validar que P0/P1 tienen watched_paths suficientes.
- Normalizar cost_class/test_cost si el payload actual esta incompleto.
```

No incluye:

```text
- Reescribir todo TCR v2 manualmente en un solo cambio si no es necesario.
- Ejecutar pruebas automaticamente.
- Eliminar heuristicas fallback antes de que rules registry cubra P0.
```

### Artefactos esperados

```text
docs/schemas/test_impact_rule_registry.schema.json
.devpilot/testing/test_impact_rules.json
src/devpilot_core/testing/impact_rules.py
tests/test_post_h_029_tcr_v2_impact_rules.py
docs/audits/post_h_029_b_tcr_v2_impact_rules_report.md
docs/post_h_029_b_manifest.json
```

### Criterios PASS

```text
- Rules registry valida contra schema.
- Cada regla declara path_patterns, domains, profiles, recommended_tests, severity y escalation.
- P0/P1 domains tienen al menos una regla.
- Unmatched sensitive path produce BLOCK o full-regression-required.
- Cost metadata deja de ser nula/no accionable para contratos criticos.
- Recommended commands siguen allowlist local.
- TCR v2 validate-v2 sigue pasando.
```

### Criterios BLOCK

```text
- Un path security/policy/approval queda unmapped sin escalation.
- Una regla recomienda comando inseguro.
- Reglas permiten red/API externa por defecto.
- Cost metadata se inventa sin trazabilidad o queda ausente para P0.
- TCR v2 deja de validar.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_029_tcr_v2_impact_rules.py `
  tests/test_test_contract_registry_v2.py `
  tests/test_test_contract_registry_profiles_v2.py `
  tests/test_test_contract_registry_migration.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core schema validate --schema-id TestImpactRuleRegistry --instance .devpilot/testing/test_impact_rules.json --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core test-impact rules --json
```

#### Estado de implementación POST-H-029-B

Implementado como primera versión local-first. El registry contiene 12 reglas declarativas, cubre todos los dominios P0/P1 actuales de TCR v2, bloquea comandos fuera de allowlist y mantiene `tests_executed=false`. El uso sigue siendo advisory hasta POST-H-029-C/E.


## 11. Micro-sprint POST-H-029-C — Test impact CLI recommendations

### Objetivo

Convertir `test-impact analyze-v2` en una recomendacion CLI mas util para operador/desarrollador: perfiles, comandos, razonamiento, riesgo residual y justificacion de no ejecutar suite completa.

### Justificacion

El impact analyzer actual produce recomendaciones sin ejecutar tests. Esto es correcto. Pero debe generar una salida mas accionable que distinga "run these now", "run before closure", "full regression required" y "manual review required".

### Alcance

Incluye:

```text
- Crear TestImpactRecommendationReport schema.
- Extender CLI test-impact analyze-v2 con salida recomendada normalizada.
- Soportar --changed-paths-file.
- Incluir matched_contracts, matched_rules, recommended_profiles, recommended_commands, recommended_tests.
- Incluir residual_risk y full_regression_required.
- Incluir waiver_required si operador decide no correr full.
- Escribir reporte con --write-report.
- No ejecutar tests.
```

No incluye:

```text
- Autoejecutar pytest.
- Aprobar automaticamente waivers.
- Integrar git diff real si no hay fuente estable; puede quedar como futuro.
```

### Artefactos esperados

```text
docs/schemas/test_impact_recommendation_report.schema.json
src/devpilot_core/testing/recommendations.py
tests/test_post_h_029_test_impact_cli_recommendations.py
docs/audits/post_h_029_c_test_impact_cli_recommendations_report.md
docs/post_h_029_c_manifest.json
```

### Criterios PASS

```text
- Reporte valida contra schema.
- Changed path P0 recomienda p0-critical/security/impact segun reglas.
- Changed path release recomienda release/release-candidate segun reglas.
- Path no mapeado requiere review o full.
- recommended_commands no contienen shell control tokens.
- tests_executed=false siempre.
- --write-report escribe outputs/reports/test_impact_recommendation_report.json.
```

### Criterios BLOCK

```text
- Path sensible no mapeado devuelve PASS simple.
- Reporte omite riesgo residual.
- Comandos recomendados son inseguros.
- CLI ejecuta pruebas sin approval.
- Se oculta necesidad de pytest -q completo en cierres.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_029_test_impact_cli_recommendations.py `
  tests/test_test_contract_registry_profiles_v2.py `
  tests/test_test_contract_registry_v2.py `
  tests/test_schema_registry.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/policy/engine.py --json
python -m devpilot_core test-impact analyze-v2 --changed-paths src/devpilot_core/testing/impact_v2.py --json --write-report
python -m devpilot_core schema validate --schema-id TestImpactRecommendationReport --instance outputs/reports/test_impact_recommendation_report.json --json
```


#### Estado de implementación POST-H-029-C

Implementado como primera versión local-first. `test-impact analyze-v2` emite `TestImpactRecommendationReport` con contratos/reglas matcheadas, perfiles recomendados, pruebas, comandos, riesgo residual, señal de regresión completa y señal de waiver si se omite full regression. No ejecuta pruebas; los comandos recomendados son datos y deben ser ejecutados explícitamente por el operador. POST-H-029-D queda implementado como perfil release candidate formal; POST-H-029-E queda pendiente para guard histórico bloqueante.

## 12. Micro-sprint POST-H-029-D — Release candidate test profile

### Objetivo

Crear un perfil formal `release-candidate-local` que agrupe pruebas y comandos necesarios para validar un release candidate local sin depender exclusivamente de `pytest -q`.

### Justificacion

POST-H-026 y POST-H-027 requieren validacion focal fuerte. El perfil release candidate debe ejecutar o recomendar checks de estado, schemas, TCR, docs governance, quality gate, production-ready-local, packaging y UI/API hardening.

### Alcance

Incluye:

```text
- Crear ReleaseCandidateTestProfileReport schema.
- Crear .devpilot/testing/release_candidate_test_profile.json.
- Asociar el perfil con test_profile_taxonomy.
- Incluir comandos read-only y write-report controlado.
- Incluir tests focales P0/P1 por dominios release, production, UI/API, testing, schemas, docs governance.
- Definir prerequisitos y timeouts.
- Definir cuando escalar a pytest -q completo.
- Integrar con tests profiles/list y TCR v2 profile si corresponde.
```

No incluye:

```text
- Reemplazar full regression final.
- Ejecutar tests desde JSON sin approval.
- CI remoto obligatorio.
```

### Artefactos esperados

```text
docs/schemas/release_candidate_test_profile_report.schema.json
.devpilot/testing/release_candidate_test_profile.json
src/devpilot_core/testing/release_candidate_profile.py
tests/test_post_h_029_release_candidate_test_profile.py
docs/audits/post_h_029_d_release_candidate_test_profile_report.md
docs/post_h_029_d_manifest.json
```

### Contenido minimo del perfil

```text
- project-state validate
- docs-governance validate
- schema list
- test-contracts validate
- test-contracts validate-v2
- quality-gate run --profile hardening
- industrial-readiness production-ready-local-final
- api shell-gate
- release reproducibility/packaging checks
- POST-H-026/027/028 tests cuando existan
- P0/P1 impact recommendations
```

### Criterios PASS

```text
- release-candidate-local valida contra schema.
- Perfil contiene comandos P0 obligatorios.
- Perfil distingue required, recommended y optional.
- Perfil declara full_regression_required_when.
- Perfil no usa red/API externa.
- Perfil no ejecuta mutaciones sin approval.
- TCR v2 y test profiles quedan sincronizados.
```

### Criterios BLOCK

```text
- Perfil omite quality-gate hardening.
- Perfil omite production-ready-local-final.
- Perfil omite TCR v1/v2.
- Perfil no escala ante paths no mapeados.
- Perfil permite shell arbitrario.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_029_release_candidate_test_profile.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  tests/test_quality_gate.py `
  tests/test_test_contract_registry_profiles_v2.py `
  tests/test_project_global_state.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core tests release-candidate-profile --json
python -m devpilot_core tests release-candidate-profile --json --write-report
python -m devpilot_core schema validate --schema-id ReleaseCandidateTestProfileReport --instance outputs/reports/release_candidate_test_profile_report.json --json
```

#### Estado de implementación POST-H-029-D

Implementado como primera versión local-first. `release-candidate-local` queda formalizado en `.devpilot/testing/release_candidate_test_profile.json` y se valida mediante `python -m devpilot_core tests release-candidate-profile --json --write-report`. El perfil distingue comandos `required`, `recommended` y `optional`, declara prerequisitos, timeouts, targets P0/P1 y condiciones `full_regression_required_when`. No ejecuta pruebas desde JSON, conserva `tests.run` approval-gated y mantiene `pytest -q` completo como obligación explícita cuando aplique. POST-H-029-E queda pendiente para convertir estas decisiones de regresión histórica en guard de cierre.


## 13. Micro-sprint POST-H-029-E — Historical regression guard

### Objetivo

Implementar un guard que impida cerrar backlog, release candidate o hito mayor sin decidir explicitamente si se requiere regresion completa, regresion focal ampliada o waiver aprobado.

### Justificacion

El proyecto ha tenido regresiones acumulativas por desincronizacion documental, schemas, TCR, source registry y tests. Tambien tiene una suite costosa. El guard debe formalizar el criterio: no correr todo siempre, pero tampoco permitir cierres industriales con evidencia insuficiente.

### Alcance

Incluye:

```text
- Crear HistoricalRegressionGuardReport schema.
- Definir eventos que requieren full regression: cierre de backlog, release candidate PASS, cambios P0 no mapeados, schema catalog, project_state, quality gate, CLI core, API security, production-ready claims, TCR schema.
- Definir eventos que permiten focal ampliada.
- Definir waiver structure con owner, motivo, riesgo, pruebas ejecutadas y expiracion.
- Verificar que logs/reportes de validacion existen o se declaran pending.
- Integrar guard en quality-gate hardening/industrial como advisory o blocking segun contexto.
- Actualizar runbook de cierre.
```

No incluye:

```text
- Almacenar logs historicos pesados en repo.
- Forzar pytest -q en cada micro-sprint.
- Aceptar waiver permanente.
```

### Artefactos esperados

```text
docs/schemas/historical_regression_guard_report.schema.json
src/devpilot_core/testing/historical_regression_guard.py
tests/test_post_h_029_historical_regression_guard.py
docs/audits/post_h_029_e_historical_regression_guard_report.md
docs/post_h_029_e_manifest.json
```

### Criterios PASS

```text
- Guard report valida contra schema.
- Cierre de backlog sin decision de regresion produce BLOCK.
- Cambio P0 no mapeado exige full o waiver.
- Waiver sin owner/motivo/pruebas/riesgo/expiracion produce BLOCK.
- Micro-sprint normal permite focal con justificacion.
- Runbook explica cuando ejecutar pytest -q completo.
- quality-gate integra testing-tiers-ready.
```

### Criterios BLOCK

```text
- Guard permite cerrar backlog con "no se ejecuto full" sin justificacion.
- Waiver no expira.
- Full regression se exige siempre, incluso para cambios triviales, sin criterio.
- Logs runtime se versionan como fuente.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_029_historical_regression_guard.py `
  tests/test_post_h_029_release_candidate_test_profile.py `
  tests/test_post_h_029_test_impact_cli_recommendations.py `
  tests/test_quality_gate.py `
  tests/test_project_global_state.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core tests regression-guard --context micro-sprint --json
python -m devpilot_core tests regression-guard --context backlog-closure --json --write-report
python -m devpilot_core schema validate --schema-id HistoricalRegressionGuardReport --instance outputs/reports/historical_regression_guard_report.json --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 14. Quality gate propuesto

Al cierre de POST-H-029-E debe existir un subgate:

```text
testing-tiers-ready
```

Debe agregarse a:

```text
quality-gate run --profile hardening
quality-gate run --profile industrial
```

Debe verificar:

```text
- TestProfileTaxonomy valida.
- TestImpactRuleRegistry valida.
- TCR v1 valida.
- TCR v2 valida.
- Test impact recommendation report PASS para fixtures P0/P1/release/unmatched.
- Release candidate test profile valida.
- Historical regression guard valida.
- No network/external APIs por defecto.
- No shell arbitrario.
- No unsafe recommended commands.
```

## 15. Secuencia recomendada de implementacion

Orden obligatorio:

```text
1. POST-H-029-A — Test profile taxonomy.
2. POST-H-029-B — TCR v2 impact rules.
3. POST-H-029-C — Test impact CLI recommendations.
4. POST-H-029-D — Release candidate test profile.
5. POST-H-029-E — Historical regression guard.
```

Razon:

```text
- No se deben crear reglas de impacto sin taxonomia comun.
- No se deben mejorar recomendaciones CLI sin reglas declarativas.
- No se debe crear perfil release candidate antes de tener reglas y taxonomia.
- No se debe cerrar la ola sin guard de regresion historica.
```

## 16. Validacion focal recomendada por micro-sprint

Validacion base:

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core schema list --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core quality-gate run --profile hardening --json
```

Validacion focal acumulativa POST-H-029:

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_029_test_profile_taxonomy.py `
  tests/test_post_h_029_tcr_v2_impact_rules.py `
  tests/test_post_h_029_test_impact_cli_recommendations.py `
  tests/test_post_h_029_release_candidate_test_profile.py `
  tests/test_post_h_029_historical_regression_guard.py `
  tests/test_test_contract_registry.py `
  tests/test_test_contract_registry_v2.py `
  tests/test_test_contract_registry_profiles_v2.py `
  tests/test_test_contract_registry_migration.py `
  tests/test_quality_gate.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q
```

Validacion final opcional de cierre:

```powershell
python -m pytest -q
```

La suite completa debe reservarse para cierre de backlog, release candidate, cambios P0 no mapeados, cambios transversales o incidente de regresion amplia.

## 17. Cierre industrial del backlog

POST-H-029 solo puede cerrarse si:

```text
- Los cinco micro-sprints estan implementados, probados y documentados.
- testing-tiers-ready existe y pasa en hardening/industrial.
- test profile taxonomy valida.
- TCR v2 impact rules validan.
- test-impact analyze-v2 emite recomendaciones accionables.
- release-candidate-local profile esta definido.
- historical regression guard bloquea cierres sin decision de regresion.
- README, runbook, test strategy, TCR, source registry, changelog y project_state estan sincronizados.
- No se reduce cobertura ni se elimina full regression como opcion obligatoria.
```

## 18. Riesgos y mitigaciones

| Riesgo | Severidad | Mitigacion en POST-H-029 |
|---|---:|---|
| Sub-testing en dominios P0/P1 | Alta | Impact rules + unmatched escalation |
| Suite completa demasiado costosa | Alta | Tiers accionables + release-candidate profile |
| Falsa confianza por tests historicos | Media/alta | docs-historical separado de runtime coverage |
| Comandos inseguros en TCR | Alta | allowlist y validator |
| Path nuevo sin mapping | Alta | review/full-regression-required |
| Waivers permanentes | Media/alta | owner, riesgo, expiracion, pruebas ejecutadas |
| Full regression exigida sin criterio | Media | guard contextual por evento |
| Flakiness por perfiles demasiado amplios | Media | cost_class, timeout, profile taxonomy |

## 19. Instrucciones de almacenamiento en el repo

Ruta canonica recomendada dentro de `repo_DevPilot_Local_262_POST_H_025_E`:

```text
docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md
```

Ruta Windows equivalente:

```powershell
D:\Projects\DevPilot_Local\docs\backlogs\POST-H-029_testing_tiers_impact_regression_cost.md
```

Si se mantiene la convencion de documento top-level por hito, crear tambien durante POST-H-029-A:

```text
docs/POST-H-029_testing_tiers_impact_regression_cost.md
```

Ese documento top-level no debe divergir del backlog canonico. Si se crea, registrarlo en:

```text
.devpilot/docs_governance/source_registry.json
README.md
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
```

## 20. Git sugerido para incorporar este backlog

Cuando se copie este archivo al repo:

```bash
git add docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md
git commit -m "Add POST-H-029 testing tiers backlog"
```

Si tambien se agrega documento top-level o source registry:

```bash
git add docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md docs/POST-H-029_testing_tiers_impact_regression_cost.md .devpilot/docs_governance/source_registry.json README.md docs/05_operations/runbook.md docs/release/CHANGELOG.md
git commit -m "Register POST-H-029 testing tiers backlog"
```

## 21. Decision de alcance

POST-H-029 es una ola de sostenibilidad de calidad y costo de regresion.

La linea de corte es:

```text
Permitido: taxonomia, reglas de impacto, recomendaciones CLI, release-candidate profile, regression guard, reportes y documentacion.
No permitido: reducir cobertura sin criterio, ejecutar shell arbitrario, omitir full regression final, habilitar red/API externa o convertir test-impact en decision automatica irreversible.
```

La siguiente ola, POST-H-030, debe usar estos tiers y reglas para reducir hotspots de CLI con menor costo de validacion y menor riesgo de regresion.
