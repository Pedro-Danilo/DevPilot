---
doc_id: "POST-H-026-BACKLOG"
id: "POST-H-026"
title: "POST-H-026 — Release candidate local y verificacion de operador"
status: "proposed"
version: "0.1.0"
owner: "Ordonez"
created: "2026-07-07"
phase: "POST-FASE-H"
priority: "P0"
roadmap_wave: "Ola 1"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
source_repo: "repo_DevPilot_Local_262_POST_H_025_E.zip"
depends_on:
  - "POST-H-025"
local_first: true
dry_run_default: true
read_only_by_default: true
no_remote_execution_enabled: true
no_external_apis_required: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
claims_allowed:
  - "production-ready-local"
claims_forbidden:
  - "enterprise-ready"
  - "remote-ready"
  - "SaaS-ready"
  - "compliance-certified"
implementation_status: "backlog-proposed"
current_micro_sprint: "POST-H-026-A"
next_micro_sprint: "POST-H-026-A"
---

# POST-H-026 — Release candidate local y verificacion de operador

## 1. Dictamen ejecutivo

POST-H-026 debe convertir la declaracion `production-ready-local` cerrada en POST-H-025 en un release candidate local verificable por operador. El objetivo no es agregar nuevas capacidades funcionales, sino demostrar que DevPilot puede instalarse, levantarse, verificarse, diagnosticarse y auditarse localmente con bajo riesgo de error humano.

El roadmap v3 define la Ola 1 como:

```text
Ola 1 - POST-H-026: Release candidate local y verificacion de operador
Objetivo: Convertir la declaracion production-ready-local en release candidate local verificable.
```

El onboarding report final confirma el mismo sentido: despues de `production-ready-local`, el avance industrial debe medirse por estabilidad, reproducibilidad, operabilidad, freshness de evidencia, test tiers, UI/API smoke y reduccion de riesgo, no por cantidad de features nuevas.

Este backlog propone cinco micro-sprints. Se mantiene alineado con la estructura identificada en el roadmap y en el informe final:

```text
POST-H-026-A — Evidence freshness model
POST-H-026-B — Release candidate verification profile
POST-H-026-C — UI/API local smoke under RC
POST-H-026-D — Local install and run verification
POST-H-026-E — RC PASS/BLOCK report
```

## 2. Fuentes consultadas

Fuentes disponibles y verificadas en el entorno de trabajo:

```text
/workspace/.cache/01-devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md
/workspace/.cache/02-repo_DevPilot_Local_262_POST_H_025_E.zip
/workspace/.cache/03-devpilot_onboarding_report_final_compilado.md
```

Repo descomprimido para analisis:

```text
/workspace/repo_DevPilot_Local_262_POST_H_025_E
```

Evidencia contextual extraida:

```text
- El roadmap v3 registra que la version 262 alcanzo 1536 passed, 0 failed, 0 errors, 0 skipped.
- El estado vigente del producto es production-ready-local.
- No se declara enterprise-ready.
- No se declara remote-ready.
- No se declara SaaS-ready.
- No se declara compliance-certified.
- .devpilot/project_state.json registra last_completed_sprint=POST-H-025 y next_sprint=POST-H-026.
- .devpilot/testing/test_profiles.json existe, pero sus perfiles actuales son basicos: smoke, unit, all.
- El repo contiene production_ready_local_criteria.json, ProductionReadyLocalReport schema, quality gates, TCR v1/v2, UI/API route registries, release reproducibility, docs governance y runbooks operativos.
```

Archivos del repo consultados de forma focal:

```text
README.md
docs/backlogs/POST-H-025_production_ready_declaration_gate.md
docs/POST-H-025_production_ready_declaration_gate.md
docs/05_operations/runbook.md
docs/05_operations/ui_api_local_runbook.md
docs/audits/devpilot_local_production_ready_declaration.md
.devpilot/project_state.json
.devpilot/production/production_ready_local_criteria.json
.devpilot/testing/test_profiles.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/docs_governance/source_registry.json
.devpilot/interfaces/api_route_contract_registry.json
.devpilot/interfaces/ui_route_contract_registry.json
src/devpilot_core/industrial/production_ready.py
src/devpilot_core/release/
src/devpilot_core/testing/
src/devpilot_core/interfaces/
ui/web/README.md
```

## 3. Objetivo del backlog

Implementar un paquete de release candidate local que permita a un operador verificar DevPilot desde una copia limpia del repo, sin depender de memoria conversacional, outputs previos o supuestos manuales.

El release candidate local debe responder de forma reproducible:

```text
1. La evidencia usada para declarar production-ready-local sigue vigente?
2. Los artefactos criticos existen, validan contra schema y corresponden al estado actual?
3. Existe un perfil de verificacion RC accionable, mas barato que pytest -q completo?
4. La API local y la UI web local se levantan bajo restricciones localhost/token/CORS/policy?
5. Un operador puede instalar, ejecutar comandos minimos y validar el producto desde cero?
6. El resultado final es PASS o BLOCK, con causas y acciones correctivas?
```

## 4. Alcance funcional

Incluye:

```text
- Modelo de freshness/staleness para evidencia critica.
- Reporte schema-backed de freshness de evidencia.
- Perfil de verificacion release-candidate-local.
- Endurecimiento de test profiles para RC sin sustituir pytest -q final.
- Smoke UI/API local bajo condiciones de release candidate.
- Verificacion de instalacion local desde entorno limpio.
- Validacion de token/API/UI, localhost y CORS local.
- Verificacion de artefactos limpios: sin outputs, DB local, caches, venv ni node_modules en entregables.
- Reporte final PASS/BLOCK de release candidate local.
- Actualizacion de README, runbook, changelog, TCR, source registry, project_state y docs de auditoria cuando se implemente cada micro-sprint.
```

No incluye:

```text
- Habilitar remote execution.
- Habilitar connector write.
- Habilitar plugin execution.
- Habilitar APIs externas obligatorias.
- Declarar enterprise-ready.
- Declarar compliance-certified.
- Declarar remote-ready.
- Declarar SaaS-ready.
- Implementar instalador desktop.
- Implementar servicio persistente del sistema operativo.
- Publicar paquetes en registry externo.
- Reemplazar la suite general pytest -q como gate final de backlog.
- Convertir agentes IA en actores autonomos.
- Cambiar arquitectura C4 o ApplicationService sin ADR especifica.
```

## 5. Principios de diseno

```text
1. Evidence freshness before release candidate.
2. BLOCK is a valid outcome.
3. RC local no amplifica claims; solo verifica production-ready-local.
4. Toda mutacion de outputs debe ser explicita mediante --write-report.
5. Los comandos RC deben ser reproducibles en Windows local.
6. Los comandos RC no deben depender de red ni APIs externas.
7. UI/API solo debe levantarse en localhost.
8. CORS wildcard bloquea RC.
9. Token local requerido para rutas no publicas.
10. Los outputs runtime se regeneran; no son fuente versionable.
11. Los artefactos de release deben excluir .venv, node_modules, outputs, caches, dist y .devpilot/devpilot.db.
12. El operador debe poder ejecutar el flujo sin conocer detalles internos del repo.
```

## 6. Estado base que hereda POST-H-026

El repo 262 llega con:

```text
- POST-H-025 cerrado.
- Declaracion production-ready-local formal.
- ProductionReadyLocalCriteria y ProductionReadyLocalReport.
- Evidence aggregator read-only.
- Declaration gate CLI/API.
- Claims validator y no-go gates.
- Final production-ready-local declaration report.
- Quality-gate hardening/industrial con subgates acumulativos.
- Test Contract Registry v1/v2.
- Docs governance y source registry.
- UI/API industrial shell implemented-initial.
- Operator dashboard implemented-initial.
- Release reproducibility implemented-initial.
- Onboarding bootstrap implemented-initial.
- Project state apuntando a POST-H-026 como siguiente sprint.
```

Brechas que motivan POST-H-026:

```text
- La evidencia puede quedar stale despues de cambios.
- test_profiles.json todavia no ofrece un perfil RC suficientemente expresivo.
- pytest -q general es costoso y no debe ser el unico mecanismo cotidiano de avance.
- UI/API tiene pruebas contractuales y smoke, pero requiere smoke RC orientado a operador.
- La instalacion/arranque local debe verificarse como experiencia de release candidate.
- El operador necesita un reporte final RC con PASS/BLOCK y acciones correctivas.
```

## 7. Artefactos globales esperados al cierre de POST-H-026

Nuevos artefactos sugeridos:

```text
docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md
docs/POST-H-026_local_release_candidate_operator_verification.md
docs/schemas/local_release_candidate_criteria.schema.json
docs/schemas/local_release_candidate_report.schema.json
docs/schemas/evidence_freshness_report.schema.json
docs/schemas/local_install_smoke_report.schema.json
docs/schemas/ui_api_rc_smoke_report.schema.json
.devpilot/release/local_release_candidate_criteria.json
.devpilot/testing/test_profiles.json
src/devpilot_core/release_candidate/__init__.py
src/devpilot_core/release_candidate/evidence_freshness.py
src/devpilot_core/release_candidate/verification_profile.py
src/devpilot_core/release_candidate/install_smoke.py
src/devpilot_core/release_candidate/ui_api_smoke.py
src/devpilot_core/release_candidate/report.py
tests/test_post_h_026_evidence_freshness.py
tests/test_post_h_026_release_candidate_profile.py
tests/test_post_h_026_ui_api_rc_smoke.py
tests/test_post_h_026_install_smoke.py
tests/test_post_h_026_release_candidate_report.py
docs/audits/post_h_026_a_evidence_freshness_report.md
docs/audits/post_h_026_b_release_candidate_profile_report.md
docs/audits/post_h_026_c_ui_api_rc_smoke_report.md
docs/audits/post_h_026_d_install_smoke_report.md
docs/audits/post_h_026_e_release_candidate_closure_report.md
docs/post_h_026_a_manifest.json
docs/post_h_026_b_manifest.json
docs/post_h_026_c_manifest.json
docs/post_h_026_d_manifest.json
docs/post_h_026_e_manifest.json
```

Runtime outputs esperados, no versionables:

```text
outputs/reports/evidence_freshness_report.json
outputs/reports/evidence_freshness_report.md
outputs/reports/release_candidate_verification_profile_report.json
outputs/reports/release_candidate_verification_profile_report.md
outputs/reports/ui_api_rc_smoke_report.json
outputs/reports/ui_api_rc_smoke_report.md
outputs/reports/local_install_smoke_report.json
outputs/reports/local_install_smoke_report.md
outputs/reports/local_release_candidate_report.json
outputs/reports/local_release_candidate_report.md
```

Artefactos a mantener sincronizados:

```text
README.md
docs/05_operations/runbook.md
docs/05_operations/ui_api_local_runbook.md
docs/release/CHANGELOG.md
docs/schemas/schema_catalog.json
.devpilot/project_state.json
.devpilot/docs_governance/source_registry.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/interfaces/api_route_contract_registry.json
.devpilot/interfaces/ui_route_contract_registry.json
src/devpilot_core/cli.py o command registry equivalente
src/devpilot_core/application/services.py si se expone API/ApplicationService
src/devpilot_core/quality/gate.py si se integra subgate RC
```

## 8. Modelo de decision de release candidate local

Estados permitidos:

```text
PASS
BLOCK
```

Resultado `PASS` solo si:

```text
- critical_evidence_stale_total = 0
- critical_evidence_missing_total = 0
- no_go_gates_passed = true
- release_candidate_profile_passed = true
- install_smoke_passed = true
- ui_api_smoke_passed = true
- production_ready_local_final_passed = true
- docs_governance_passed = true
- tcr_v1_v2_passed = true
- schemas_valid = true
- clean_artifact_policy_passed = true
- forbidden_claims_detected_total = 0
```

Resultado `BLOCK` si:

```text
- Cualquier evidencia critica esta stale/missing.
- production-ready-local-final falla.
- UI/API no puede levantarse localmente o viola token/localhost/CORS.
- Instalacion local limpia no ejecuta comandos minimos.
- Se detecta runtime artifact versionable en paquete candidato.
- Se detecta claim enterprise/remote/SaaS/compliance.
- Algun no-go gate queda habilitado.
- El reporte final no valida contra schema.
```

## 9. Micro-sprint POST-H-026-A — Evidence freshness model

### Objetivo

Implementar un modelo deterministicamente verificable de freshness/staleness para la evidencia critica usada por `production-ready-local` y por el futuro release candidate local.

### Justificacion

POST-H-025 demuestra que la evidencia requerida existe y puede producir una declaracion final. POST-H-026-A debe agregar una capa temporal y contextual: la evidencia debe corresponder al repo actual, al sprint vigente y al set de archivos criticos esperado. Un PASS basado en evidencia antigua debe bloquear el RC.

### Alcance

Incluye:

```text
- Definir EvidenceFreshnessReport schema.
- Crear registry/config de evidencias RC con freshness policy.
- Clasificar evidencia como fresh, stale, missing, invalid, not_applicable.
- Validar evidencia versionada: docs, schemas, registries, criteria, manifests, runbooks.
- Validar evidencia runtime regenerable si existe: production_ready_local_report, quality gate report, ui_api_shell_report.
- Detectar referencias obsoletas evidentes como current_repo/source_repo que no coincidan con repo vigente.
- Emitir reporte read-only por defecto.
- Escribir outputs/reports/evidence_freshness_report.* solo con --write-report.
```

No incluye:

```text
- Ejecutar pytest completo.
- Recalcular toda la evidencia.
- Corregir automaticamente documentos stale.
- Publicar release.
```

### Artefactos esperados

```text
docs/schemas/evidence_freshness_report.schema.json
.devpilot/release/local_release_candidate_criteria.json
src/devpilot_core/release_candidate/evidence_freshness.py
tests/test_post_h_026_evidence_freshness.py
docs/audits/post_h_026_a_evidence_freshness_report.md
docs/post_h_026_a_manifest.json
```

### Contrato minimo del reporte

```json
{
  "schema_version": "1.0",
  "report_id": "evidence-freshness",
  "scope": "local-release-candidate",
  "decision": "PASS",
  "repo_version": "repo_DevPilot_Local_262_POST_H_025_E",
  "evidence_total": 0,
  "fresh_total": 0,
  "stale_total": 0,
  "missing_total": 0,
  "critical_stale_total": 0,
  "critical_missing_total": 0,
  "items": [],
  "safety": {
    "read_only": true,
    "network_used": false,
    "external_api_used": false,
    "source_mutations": false
  }
}
```

### Criterios PASS

```text
- El schema valida instancias PASS y BLOCK.
- El scanner detecta evidencia fresh, stale y missing mediante fixtures.
- Evidencia critica stale produce decision BLOCK.
- La ejecucion por defecto no escribe outputs.
- --write-report escribe JSON/Markdown bajo outputs/reports.
- No usa red, APIs externas ni mutaciones de fuente.
- TCR v1/v2 registra el contrato.
- README/runbook/changelog/source_registry quedan sincronizados.
```

### Criterios BLOCK

```text
- Una evidencia critica stale no bloquea.
- Se usa mtime de outputs como unica fuente de verdad.
- El reporte puede declarar PASS sin production_ready_local_criteria.json.
- Se versionan outputs runtime.
- Se altera evidence map de POST-H-025 sin prueba de regresion.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_026_evidence_freshness.py `
  tests/test_post_h_025_production_ready_criteria.py `
  tests/test_post_h_025_production_ready_aggregator.py `
  tests/test_schema_registry.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core release-candidate evidence-freshness --json
python -m devpilot_core release-candidate evidence-freshness --json --write-report
python -m devpilot_core schema validate --schema-id EvidenceFreshnessReport --instance outputs/reports/evidence_freshness_report.json --json
```

## 10. Micro-sprint POST-H-026-B — Release candidate verification profile

### Objetivo

Crear un perfil de verificacion RC que ejecute checks focales de alto valor sin obligar a correr `pytest -q` completo en cada iteracion.

### Justificacion

El repo ya tiene mas de 1500 tests y el informe reconoce el costo de regresion. POST-H-026-B debe hacer operacional el criterio de "verificacion pertinente" mediante perfiles versionados, TCR v2 y recomendaciones de impacto.

### Alcance

Incluye:

```text
- Agregar perfil release-candidate-local en .devpilot/testing/test_profiles.json o nuevo registry equivalente.
- Definir taxonomia always, impacted, release-candidate, full.
- Conectar TCR v2 con perfil RC.
- Integrar comandos actuales: project-state, docs-governance, schema list, schema validate, test-contracts v1/v2, quality-gate hardening, production-ready-local-final.
- Emitir reporte de perfil RC con comandos esperados, comandos ejecutados, resultados y duracion.
- Mantener tests.run approval-gated cuando ejecute pytest via MIASI.
```

No incluye:

```text
- Eliminar perfil all.
- Rebajar pytest -q como validacion final del backlog completo.
- Permitir shell arbitrario desde tests.run.
- Ejecutar comandos destructivos.
```

### Artefactos esperados

```text
docs/schemas/release_candidate_verification_profile.schema.json
.devpilot/testing/test_profiles.json
src/devpilot_core/release_candidate/verification_profile.py
tests/test_post_h_026_release_candidate_profile.py
docs/audits/post_h_026_b_release_candidate_profile_report.md
docs/post_h_026_b_manifest.json
```

### Perfil minimo recomendado

```json
{
  "profile_id": "release-candidate-local",
  "description": "Focused local RC verification profile for operator release candidate checks.",
  "commands": [
    "project-state validate",
    "docs-governance validate",
    "schema list",
    "test-contracts validate",
    "test-contracts validate-v2",
    "quality-gate run --profile hardening",
    "industrial-readiness production-ready-local-final",
    "release-candidate evidence-freshness",
    "release-candidate ui-api-smoke",
    "release-candidate install-smoke"
  ],
  "pytest_targets": [
    "tests/test_post_h_026_*.py",
    "tests/test_post_h_025_production_ready_final_declaration.py",
    "tests/test_post_h_014_*.py",
    "tests/test_release_*.py",
    "tests/test_quality_gate.py"
  ],
  "network_allowed": false,
  "external_api_allowed": false,
  "requires_approval_for_pytest": true
}
```

### Criterios PASS

```text
- El perfil RC esta versionado y validado.
- La CLI puede listar el perfil sin ejecutar nada.
- El perfil distingue comandos read-only de comandos con escritura de outputs.
- El perfil no acepta pytest args arbitrarios desde usuario.
- TCR v1/v2 registra los tests del perfil.
- test-impact v2 recomienda perfil RC cuando se tocan dominios release, production, UI/API, testing, schemas o docs governance.
```

### Criterios BLOCK

```text
- El perfil RC omite production-ready-local-final.
- El perfil RC omite evidence freshness.
- El perfil RC omite UI/API smoke o install smoke una vez implementados.
- El perfil permite shell arbitrario.
- El perfil usa network/API externa.
- Se relaja tests.run approval.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_026_release_candidate_profile.py `
  tests/test_test_contract_registry_profiles_v2.py `
  tests/test_test_contract_registry_v2.py `
  tests/test_test_impact_v2.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core tests profiles --json
python -m devpilot_core release-candidate profile --profile release-candidate-local --json
python -m devpilot_core test-impact analyze-v2 --changed-files src/devpilot_core/release_candidate/report.py --json
```

## 11. Micro-sprint POST-H-026-C — UI/API local smoke under RC

### Objetivo

Verificar que la API local y la UI web local operan bajo condiciones de release candidate: localhost, token, CORS local, rutas contractadas, estados visibles y sin acceso remoto.

### Justificacion

UI/API existe como `implemented-initial`, con route registries, security hardening y shell-gate. POST-H-026-C debe elevar la verificacion a experiencia RC: no basta con contratos; debe demostrarse que un operador puede levantar API/UI, autenticar y ver estados criticos.

### Alcance

Incluye:

```text
- Smoke API local sobre 127.0.0.1.
- Smoke token: rutas protegidas sin token fallan con 401/403.
- Smoke token valido: rutas operator dashboard/report/security posture responden ApplicationResponse.
- Smoke CORS: wildcard bloqueado, origen local permitido.
- Smoke UI: build/test actual y, si se adopta Playwright o equivalente, screenshots locales de rutas criticas.
- Validacion de UiRouteContractRegistry y ApiRouteContractRegistry.
- Reporte UiApiRcSmokeReport.
```

No incluye:

```text
- Auth enterprise.
- OIDC.
- Multiusuario.
- Exponer API fuera de localhost.
- Completar todas las vistas UI.
- Probar navegadores remotos.
```

### Artefactos esperados

```text
docs/schemas/ui_api_rc_smoke_report.schema.json
src/devpilot_core/release_candidate/ui_api_smoke.py
tests/test_post_h_026_ui_api_rc_smoke.py
tests/test_post_h_026_ui_api_rc_smoke_contract.py
docs/audits/post_h_026_c_ui_api_rc_smoke_report.md
docs/post_h_026_c_manifest.json
```

Si se introduce Playwright:

```text
ui/web/playwright.config.ts
ui/web/tests/rc-smoke.spec.ts
ui/web/test-results/             # runtime, no versionar resultados
outputs/reports/ui_api_rc_smoke_report.json
```

### Rutas/flujos minimos a cubrir

```text
- Health/status publico o controlado.
- Security posture protegido.
- Operator dashboard protegido.
- Report viewer / empty state.
- Trace viewer / empty state.
- Approval center / BLOCK o no pending approvals.
- Settings/security posture sin secretos raw.
- 401/403 sin token.
- BLOCK visible cuando una accion no-go se intenta desde UI/API.
```

### Criterios PASS

```text
- API solo se levanta en host local permitido.
- Rutas no publicas requieren token.
- CORS no acepta wildcard.
- UI consume API local, no lee .devpilot/outputs directamente.
- Estados loading/empty/error/BLOCK son visibles o verificables.
- El reporte valida contra schema.
- El smoke no habilita remote execution, connector write, plugin execution ni external APIs.
```

### Criterios BLOCK

```text
- API acepta 0.0.0.0 sin confirmacion/gate.
- CORS wildcard activo.
- Ruta protegida responde sin token.
- UI muestra secretos o token raw.
- UI dispara accion no-go fuera de dry-run.
- Smoke requiere red externa.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_026_ui_api_rc_smoke.py `
  tests/test_post_h_014_api_route_contracts.py `
  tests/test_post_h_014_security_hardening.py `
  tests/test_api_security.py `
  tests/test_api_contract.py `
  tests/test_web_ui_mvp.py `
  tests/test_web_ui_report_trace_viewer.py `
  tests/test_web_ui_approval_center.py `
  tests/test_web_ui_settings.py `
  -q
npm --prefix ui/web test
```

### Comandos objetivo

```powershell
python -m devpilot_core api token --json
$env:DEVPILOT_API_TOKEN="<token-generado>"
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute
python -m devpilot_core release-candidate ui-api-smoke --base-url http://127.0.0.1:8787 --json --write-report
python -m devpilot_core schema validate --schema-id UiApiRcSmokeReport --instance outputs/reports/ui_api_rc_smoke_report.json --json
```

## 12. Micro-sprint POST-H-026-D — Local install and run verification

### Objetivo

Verificar que un operador puede instalar y ejecutar DevPilot localmente desde una copia limpia del repo sin conocimiento interno, sin red obligatoria y sin contaminar el paquete con runtime artifacts.

### Justificacion

La declaracion `production-ready-local` debe ser operable. Si un operador no puede instalar, ejecutar CLI minima, levantar API/UI y validar gates base, el RC debe bloquear aunque el repo tenga evidencias internas correctas.

### Alcance

Incluye:

```text
- Script/servicio de install smoke read-only/dry-run por defecto.
- Verificacion Python version, venv, editable install o instalacion local segun guia.
- Verificacion de comandos minimos: --version, schema list, project-state, docs-governance, production-ready-local-final.
- Verificacion de dependencias frontend: npm install/npm test documentados, sin versionar node_modules.
- Verificacion de clean package hygiene.
- Verificacion de exclusiones de ZIP/entregable.
- Reporte LocalInstallSmokeReport.
```

No incluye:

```text
- Publicar wheel/sdist definitivo.
- Resolver packaging reproducible completo; eso pertenece a POST-H-027.
- Crear instalador MSI/EXE.
- Soportar despliegue cloud.
```

### Artefactos esperados

```text
docs/schemas/local_install_smoke_report.schema.json
src/devpilot_core/release_candidate/install_smoke.py
tests/test_post_h_026_install_smoke.py
docs/audits/post_h_026_d_install_smoke_report.md
docs/post_h_026_d_manifest.json
```

### Checklist minimo del operador

```text
1. Crear venv.
2. Instalar dependencias Python.
3. Ejecutar python -m devpilot_core --version.
4. Ejecutar project-state validate.
5. Ejecutar docs-governance validate.
6. Ejecutar schema list.
7. Ejecutar test-contracts validate y validate-v2.
8. Ejecutar production-ready-local-final --write-report.
9. Generar token API.
10. Levantar API en 127.0.0.1.
11. Ejecutar npm --prefix ui/web test.
12. Levantar UI local.
13. Ejecutar smoke RC.
```

### Criterios PASS

```text
- El procedimiento funciona desde una copia limpia.
- No requiere outputs previos.
- No requiere .devpilot/devpilot.db.
- No requiere red para checks core.
- No versiona .venv, node_modules, outputs, caches, dist ni DB local.
- Los comandos minimos devuelven JSON parseable cuando aplica.
- Los reportes escritos validan contra schema.
```

### Criterios BLOCK

```text
- Install smoke depende de rutas absolutas del desarrollador.
- Comandos minimos requieren outputs historicos.
- El paquete contiene runtime artifacts.
- API/UI solo funciona con configuracion no documentada.
- Se requiere red o API externa para el camino local core.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_026_install_smoke.py `
  tests/test_release_verification.py `
  tests/test_release_manifest.py `
  tests/test_post_h_017_release_reproducibility_pack.py `
  tests/test_project_global_state.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core release-candidate install-smoke --json
python -m devpilot_core release-candidate install-smoke --json --write-report
python -m devpilot_core schema validate --schema-id LocalInstallSmokeReport --instance outputs/reports/local_install_smoke_report.json --json
```

## 13. Micro-sprint POST-H-026-E — RC PASS/BLOCK report

### Objetivo

Emitir el reporte final `LocalReleaseCandidateReport` con decision `PASS` o `BLOCK`, evidencias, gaps, no-go gates, claims permitidos/prohibidos y acciones correctivas.

### Justificacion

Un RC local no debe ser una suma informal de comandos. Debe producir un artefacto auditable y schema-backed que el operador pueda anexar como evidencia de release candidate local.

### Alcance

Incluye:

```text
- LocalReleaseCandidateCriteria schema y criteria JSON.
- LocalReleaseCandidateReport schema.
- Agregador final de evidencia RC.
- CLI release-candidate final.
- ApplicationService method si aplica.
- Integracion opcional como subgate quality-gate: local-release-candidate.
- Reporte Markdown legible para operador.
- Auditoria final docs/audits/post_h_026_e_release_candidate_closure_report.md.
- Actualizacion de project_state: last_completed_sprint=POST-H-026 y next_sprint=POST-H-027 solo al cierre probado.
```

No incluye:

```text
- Cambiar el claim de producto por encima de production-ready-local.
- Publicar artefactos externos.
- Firmar releases formalmente; eso queda para POST-H-027 o posterior.
```

### Artefactos esperados

```text
docs/schemas/local_release_candidate_criteria.schema.json
docs/schemas/local_release_candidate_report.schema.json
.devpilot/release/local_release_candidate_criteria.json
src/devpilot_core/release_candidate/report.py
tests/test_post_h_026_release_candidate_report.py
docs/audits/post_h_026_e_release_candidate_closure_report.md
docs/post_h_026_e_manifest.json
```

### Contrato minimo del reporte final

```json
{
  "schema_version": "1.0",
  "report_id": "local-release-candidate",
  "decision": "BLOCK",
  "scope": "local-release-candidate",
  "production_ready_local_claim_preserved": true,
  "forbidden_claims_detected_total": 0,
  "no_go_gates_passed": true,
  "evidence_freshness_passed": false,
  "release_candidate_profile_passed": false,
  "ui_api_smoke_passed": false,
  "install_smoke_passed": false,
  "blocking_gaps_total": 0,
  "advisory_gaps_total": 0,
  "actions_required": [],
  "safety": {
    "network_used": false,
    "external_api_used": false,
    "remote_execution_enabled": false,
    "connector_write_enabled": false,
    "plugin_execution_enabled": false
  }
}
```

### Criterios PASS

```text
- El reporte final valida contra schema.
- PASS exige A, B, C y D en PASS.
- BLOCK incluye causas y acciones correctivas.
- Claims forbidden siguen en false.
- No-go gates siguen en false.
- El reporte se escribe solo con --write-report.
- TCR v1/v2, README, runbook, changelog, source registry y project_state quedan sincronizados.
```

### Criterios BLOCK

```text
- PASS puede emitirse con evidencia stale.
- PASS puede emitirse con UI/API smoke fallando.
- PASS puede emitirse con install smoke fallando.
- PASS puede emitirse con no-go gate activo.
- El reporte final no distingue blockers de advisory.
- El cierre actualiza project_state sin pruebas adjuntas.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_026_release_candidate_report.py `
  tests/test_post_h_026_evidence_freshness.py `
  tests/test_post_h_026_release_candidate_profile.py `
  tests/test_post_h_026_ui_api_rc_smoke.py `
  tests/test_post_h_026_install_smoke.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_quality_gate.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core release-candidate final --json
python -m devpilot_core release-candidate final --json --write-report
python -m devpilot_core schema validate --schema-id LocalReleaseCandidateReport --instance outputs/reports/local_release_candidate_report.json --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 14. Secuencia recomendada de implementacion

Orden obligatorio:

```text
1. POST-H-026-A — Evidence freshness model.
2. POST-H-026-B — Release candidate verification profile.
3. POST-H-026-C — UI/API local smoke under RC.
4. POST-H-026-D — Local install and run verification.
5. POST-H-026-E — RC PASS/BLOCK report.
```

Razon:

```text
- Sin freshness, el RC podria apoyarse en evidencia obsoleta.
- Sin perfil RC, no hay mecanismo economico de verificacion repetible.
- Sin UI/API smoke, la superficie de operador queda subvalidada.
- Sin install smoke, el RC no prueba instalabilidad real.
- Sin reporte final, no hay cierre auditable PASS/BLOCK.
```

## 15. Validacion general focal recomendada por micro-sprint

No ejecutar `pytest -q` completo en cada micro-sprint, salvo cierre de backlog o incidente de regresion amplia. Usar verificacion focal:

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core schema list --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core industrial-readiness production-ready-local-final --json --write-report
python -m devpilot_core schema validate --schema-id ProductionReadyLocalReport --instance outputs/reports/production_ready_local_report.json --json
```

Tests focales acumulativos POST-H-026:

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_026_evidence_freshness.py `
  tests/test_post_h_026_release_candidate_profile.py `
  tests/test_post_h_026_ui_api_rc_smoke.py `
  tests/test_post_h_026_install_smoke.py `
  tests/test_post_h_026_release_candidate_report.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_post_h_025_production_ready_declaration_gate.py `
  tests/test_post_h_025_production_ready_aggregator.py `
  tests/test_post_h_014_api_route_contracts.py `
  tests/test_post_h_014_security_hardening.py `
  tests/test_quality_gate.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q
```

UI/API:

```powershell
npm --prefix ui/web test
python -m devpilot_core api shell-gate --json --write-report
python -m devpilot_core schema validate --schema-id UiApiShellReport --instance outputs/reports/ui_api_shell_report.json --json
```

## 16. Cierre industrial del backlog

POST-H-026 solo puede cerrarse si:

```text
- Los cinco micro-sprints estan implementados, probados y documentados.
- El reporte final LocalReleaseCandidateReport existe y valida contra schema.
- El reporte final emite PASS o BLOCK sin ambiguedad.
- Si emite PASS, todos los no-go gates siguen deshabilitados.
- Si emite BLOCK, el backlog no se declara cerrado salvo que el objetivo sea explicitamente "BLOCK report accepted" con acciones correctivas documentadas.
- README, runbook, changelog, source registry, TCR y project_state estan sincronizados.
- La validacion focal acumulativa POST-H-026 pasa.
- La validacion general pytest -q se programa para cierre del backlog o para el siguiente checkpoint mayor, no para cada micro-sprint.
```

## 17. Riesgos y mitigaciones

| Riesgo | Severidad | Mitigacion en POST-H-026 |
|---|---:|---|
| PASS basado en evidencia stale | Alta | Evidence freshness gate bloqueante |
| RC profile demasiado liviano | Alta | TCR v2 + dominios P0 + production-ready-local-final obligatorio |
| UI/API insegura en entorno local | Alta | Smoke localhost/token/CORS/401/403/BLOCK |
| Instalacion solo funciona en maquina del desarrollador | Alta | Install smoke con rutas relativas y copia limpia |
| Drift documental por volumen de docs | Media/alta | docs-governance + source_registry + tests especificos |
| Runtime artifacts versionados | Alta | clean artifact policy + release reproducibility + runtime hygiene |
| Overclaim de enterprise/SaaS/remote/compliance | Alta | claims validator y forbidden claims en reporte RC |
| Costo excesivo de pruebas | Media | RC profile e impact tests, sin eliminar pytest -q final |
| Dependencia no controlada de red/npm | Media | Core sin red; frontend documenta npm como prerequisito local |

## 18. Instrucciones de almacenamiento en el repo

Ruta canonica recomendada dentro de `repo_DevPilot_Local_262_POST_H_025_E`:

```text
docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md
```

Ruta Windows equivalente:

```powershell
D:\Projects\DevPilot_Local\docs\backlogs\POST-H-026_local_release_candidate_operator_verification.md
```

Durante la implementacion de POST-H-026-A, si se mantiene la convencion de documento top-level por hito, crear tambien:

```text
docs/POST-H-026_local_release_candidate_operator_verification.md
```

Ese espejo top-level no debe divergir del backlog canonico. Si se crea, registrarlo en:

```text
.devpilot/docs_governance/source_registry.json
README.md
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
```

## 19. Git sugerido para incorporar este backlog

Cuando se copie este archivo al repo:

```bash
git add docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md
git commit -m "Add POST-H-026 local release candidate backlog"
```

Si tambien se agrega documento top-level o source registry:

```bash
git add docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md docs/POST-H-026_local_release_candidate_operator_verification.md .devpilot/docs_governance/source_registry.json README.md docs/05_operations/runbook.md docs/release/CHANGELOG.md
git commit -m "Register POST-H-026 local release candidate backlog"
```

## 20. Decision de alcance

Este backlog es de estabilizacion industrial local. No debe convertirse en una ola de nuevas features. La linea de corte es:

```text
Permitido: verificar, estabilizar, medir, bloquear, documentar, reportar, guiar al operador.
No permitido: ampliar claims, activar capacidades sensibles, introducir dependencia externa obligatoria, publicar servicios o convertir agentes en autonomos.
```

La siguiente ola, POST-H-027, deberia tomar el resultado de POST-H-026 y convertirlo en packaging reproducible e instalacion local mas robusta.
