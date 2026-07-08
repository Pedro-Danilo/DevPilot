---
doc_id: "DEVPL-AUDIT-POST-H-026-B-RC-PROFILE"
title: "POST-H-026-B — Release candidate verification profile report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordonez"
updated: "2026-07-08"
approval: "pending-owner-review"
---

# POST-H-026-B — Release candidate verification profile report

## Implementado

- Perfil `release-candidate-local` versionado en `.devpilot/testing/test_profiles.json`.
- Módulo `src/devpilot_core/release_candidate/verification_profile.py`.
- Comando `python -m devpilot_core release-candidate profile --profile release-candidate-local --json`.
- Schema `ReleaseCandidateVerificationProfile`.
- Binding TCR v1/v2 y recomendación Test Impact v2 para cambios en `src/devpilot_core/release_candidate`.

## Estado

`implemented-initial / plan-only`. La inspección no ejecuta pytest, no ejecuta shell, no usa red y no escribe outputs salvo con `--write-report`.

## PASS

- Perfil local-only sin external APIs.
- Pytest permanece approval-gated mediante `tests.run`.
- TCR v2 selecciona contratos para `release-candidate-local`.
- El reporte plan-only valida contra schema.

## BLOCK

- Faltan comandos RC obligatorios.
- El perfil habilita red/API externa/shell arbitrario.
- Se relaja aprobación de pytest.
- TCR v2 no reconoce el perfil.

## Riesgos

- El perfil RC es una aceleración operacional; no reemplaza la suite completa al cierre del backlog.
- UI/API smoke e install smoke aún no están implementados; aparecen como comandos esperados para los próximos micro-sprints.

## Verificación

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_026_release_candidate_profile.py tests/test_test_contract_registry_profiles_v2.py tests/test_test_contract_registry_v2.py tests/test_test_impact_v2.py -q
python -m devpilot_core release-candidate profile --profile release-candidate-local --json
python -m devpilot_core schema validate --schema-id ReleaseCandidateVerificationProfile --instance outputs/reports/release_candidate_verification_profile_report.json --json
```
