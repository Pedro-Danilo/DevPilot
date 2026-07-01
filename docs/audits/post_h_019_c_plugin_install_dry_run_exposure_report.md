---
doc_id: "POST-H-019-C-PLUGIN-INSTALL-DRY-RUN-EXPOSURE-REPORT"
title: "POST-H-019-C — Plugin install dry-run y exposure report"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
created_by: "POST-H-019-C"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: "docs/backlogs/POST-H-019_plugin_sandbox_design.md"
---

# POST-H-019-C — Plugin install dry-run y exposure report

## Resultado

POST-H-019-C queda implementado como `implemented-initial`.

El sprint agrega validación estática e instalación simulada metadata-only para plugins registrados. El flujo produce un exposure report validable por schema y conserva el límite central del hito: un manifest puede ser declarado, validado e install-simulated, pero nunca queda autorizado como ejecutable.

## Componentes agregados

- `src/devpilot_core/plugins/static_validator.py`: valida registry, permission model, entrypoints deshabilitados, side effects seguros y manifest references sin leer archivos arbitrarios.
- `src/devpilot_core/plugins/exposure_report.py`: genera el reporte `PluginSandboxDesignReport` con summary, plugins, permission model, findings y safety flags.
- `docs/schemas/plugin_sandbox_design_report.schema.json`: contrato estructural del exposure report de plugins.
- `tests/test_post_h_019_plugin_static_validator.py`: pruebas de validación estática, schema y CLI `--all`.
- `tests/test_post_h_019_plugin_execution_blocked.py`: pruebas de bloqueo de ejecución, entrypoints importables y obligatoriedad de `--dry-run`.

## Evidencia esperada

```powershell
python -m devpilot_core plugin dry-run --all --dry-run --json --write-report
python -m devpilot_core schema validate --schema-id PluginSandboxDesignReport --instance outputs/reports/plugin_exposure_report.json --json
```

El resultado PASS debe declarar:

```text
plugins_total=2
metadata_only_total=2
install_simulated_total=2
execution_allowed_total=0
plugin_code_loaded=false
arbitrary_code_execution_performed=false
network_used=false
external_api_used=false
mutations_performed=false
dependencies_installed=false
marketplace_used=false
blocking_findings_total=0
```

## Límites vigentes

POST-H-019-C no implementa ejecución real de plugins, carga dinámica, subprocess, shell, pip install, marketplace, red, APIs externas, escritura de filesystem ni remote execution.

Cualquier ejecución futura de plugins requiere ADR, sandbox técnico, permission model endurecido, Approval/RBAC, observabilidad, evals, rollback y quality gate dedicado.
