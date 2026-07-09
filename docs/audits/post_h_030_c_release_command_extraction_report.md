---
doc_id: POST-H-030-C-RELEASE-COMMAND-EXTRACTION-REPORT
title: "POST-H-030-C — Release command extraction report"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-09"
approval: approved
source_of_truth: true
---

# POST-H-030-C — Release command extraction report

## Estado

`implemented-initial/local-first`.

## Alcance implementado

POST-H-030-C extrae la construcción de resultados de la familia release hacia `src/devpilot_core/cli_commands/release.py` preservando `src/devpilot_core/cli.py` como parser, wrapper público, punto de eventos, persistencia, renderizado JSON/humano y escritura opcional de reportes.

Familias cubiertas:

- `release`
- `release-candidate`
- `package`
- `install`
- `backup`
- `upgrade`

## Comandos migrados

- `backup.create`
- `backup.list`
- `backup.restore`
- `install.plan`
- `install.windows-smoke`
- `package.build`
- `package.source-zip-policy`
- `release.artifact-manifest`
- `release.changelog`
- `release.checksum`
- `release.environment-snapshot`
- `release.manifest`
- `release.python-artifact-verify`
- `release.reproducibility-pack`
- `release.reproducibility-verify`
- `release.sbom`
- `release.smoke-test`
- `release.source-archive-manifest`
- `release.upgrade-rollback-dry-run`
- `release.verify`
- `release-candidate.evidence-freshness`
- `release-candidate.final`
- `release-candidate.install-smoke`
- `release-candidate.profile`
- `release-candidate.ui-api-smoke`
- `upgrade.check`

## Invariantes preservados

- No se cambian nombres públicos de comandos.
- No se cambian flags públicos.
- No se cambia el envelope JSON `CommandResult`.
- No se cambian códigos de salida.
- No se habilita router dinámico.
- No se introduce carga dinámica de handlers.
- No se habilita red ni APIs externas.
- No se habilita publicación, despliegue, remote execution, connector write ni plugin execution.
- La escritura de reportes sigue siendo explícita con `--write-report` cuando aplica.

## Evidencia esperada

```powershell
$env:PYTHONPATH="src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_030_release_command_extraction.py -q
python -m devpilot_core cli-registry guard --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
```

## Limitaciones

Esta es una primera versión incremental. POST-H-030-E debe agregar contratos/snapshots observables para comparar salidas de comandos críticos y migrados. POST-H-030-C no declara la CLI completamente desacoplada ni elimina todos los handlers legacy de `cli.py`.
