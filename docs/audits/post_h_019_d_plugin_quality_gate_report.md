---
doc_id: "POST-H-019-D-PLUGIN-QUALITY-GATE-REPORT"
title: "POST-H-019-D — Plugin quality gate safety report"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
---

# POST-H-019-D — Plugin quality gate safety report

## Estado

`implemented-initial`.

POST-H-019-D integra seguridad de plugins al quality gate local mediante el subgate `plugin-sandbox-design`. La implementación valida metadatos y evidencia local, no ejecuta plugins y no concede permiso de ejecución.

## Implementado

- `PluginSandboxQualityGate` compone `PluginRegistry`, `PluginPermissionModel` y `PluginExposureReporter`.
- `quality-gate run --profile hardening` e `industrial` incluyen el subgate `plugin-sandbox-design`.
- El gate valida señal preliminar desde `evals/fixtures/plugin_ecosystem_eval_cases.json`.
- El contrato `post-h-019-plugin-sandbox-design` queda promovido a cobertura de quality gate.

## PASS

- PASS si `plugin_execution_allowed=false`.
- PASS si `execution_allowed_total=0`.
- PASS si todos los plugins registrados son metadata-only.
- PASS si registry, permission model y exposure report pasan.
- PASS si `plugin_ecosystem_eval_signal_present=true`.
- PASS si `network_used=false`, `external_api_used=false`, `source_mutations_performed=false` y `dependencies_installed=false`.

## BLOCK

- BLOCK si se habilita ejecución de plugins.
- BLOCK si el permission model permite `plugin.code.execute`.
- BLOCK si aparece `importlib`, `subprocess`, `pip install`, marketplace, red o API externa como mecanismo de plugin.
- BLOCK si el quality gate deja de evaluar plugin registry, permission model o exposure report.

## Riesgos

- Confundir un subgate de seguridad con un runtime de plugins.
- Sobredeclarar madurez productiva antes del runbook final y ADR trigger de POST-H-019-E.
- Relajar la política deny-by-default para permisos críticos sin ADR futura.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace tests/test_post_h_019_plugin_quality_gate.py tests/test_quality_gate.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core plugin dry-run --all --dry-run --json --write-report
python -m devpilot_core plugin validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
```

## Limitaciones

Esta versión es `implemented-initial`. No implementa ejecución real de plugins, aislamiento de runtime, firma, marketplace, instalación de dependencias, red, APIs externas, filesystem write ni remote execution. POST-H-019-E debe completar runbook metadata-only, trigger ADR y cierre documental del hito.
