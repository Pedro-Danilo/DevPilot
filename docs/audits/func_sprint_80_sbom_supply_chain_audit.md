---
doc_id: DEVPL-AUDIT-FUNC-SPRINT-80
status: approved
title: Auditoría FUNC-SPRINT-80 — SBOM y supply-chain baseline
owner: Ordóñez
standard: MIPSoftware
extension: MIASI
updated: 2026-06-17
version: 1.0.0
approval: approved_after_local_sbom_validation
---

# Auditoría FUNC-SPRINT-80 — SBOM y supply-chain baseline

## 0. Estado

`FUNC-SPRINT-80` queda implementado en estado `implemented-initial` y con veredicto `PASS` focalizado. La implementación crea una línea base SBOM local y una política de supply chain sin red, sin APIs externas, sin publicación, sin despliegue y sin mutación de fuente.

## 1. Propósito

Cerrar el gap de inventario de componentes de Fase G: antes de calcular checksums o ejecutar smoke release, DevPilot necesita declarar qué dependencias y componentes forman parte del producto y qué límites tiene la evidencia generada.

## 2. Alcance implementado

- Módulo `src/devpilot_core/release/sbom.py`.
- CLI `python -m devpilot_core release sbom --json`.
- Reportes opcionales `outputs/reports/release_sbom.*`.
- Política `docs/03_security/supply_chain_policy.md`.
- Manifest `docs/functional_sprint_80_manifest.json`.
- Pruebas `tests/test_release_sbom.py` y `tests/test_sprint_80_documentation.py`.

## 3. Funcionamiento técnico

El SBOM se genera a partir de fuentes locales: `pyproject.toml`, `ui/web/package.json` y `ui/web/package-lock.json`. El resultado incluye grupos de dependencias Python runtime/opcionales/build, dependencias directas npm y componentes bloqueados npm. Además, produce un payload CycloneDX-compatible preliminar y una declaración SLSA `local-baseline`.

## 4. Archivos creados

- `src/devpilot_core/release/sbom.py`: builder determinístico local del SBOM baseline.
- `docs/03_security/supply_chain_policy.md`: política de supply chain.
- `docs/audits/func_sprint_80_sbom_supply_chain_audit.md`: auditoría del sprint.
- `docs/functional_sprint_80_manifest.json`: manifest funcional.
- `tests/test_release_sbom.py`: pruebas del builder/CLI.
- `tests/test_sprint_80_documentation.py`: pruebas de sincronización documental.

## 5. Archivos modificados

- `src/devpilot_core/cli.py`: agrega `release sbom`.
- `src/devpilot_core/release/__init__.py`: exporta `ReleaseSbomBuilder`.
- `src/devpilot_core/release/manifest.py`: actualiza SBOM como artefacto esperado implementado inicialmente.
- `README.md`, `runbook.md`, backlog Fase G, functional backlog y changelog: sincronización documental.

## 6. Criterios PASS

- `release sbom --json` retorna PASS.
- `--write-report` genera evidencia bajo `outputs/reports`.
- Se declaran dependencias runtime, dev y build.
- Se incluyen dependencias directas y lockfile de Web UI cuando existan.
- No hay red, APIs externas, publicación, despliegue ni mutación de fuente.

## 7. Criterios BLOCK

- El SBOM requiere red.
- Omite dependencias dev.
- Omite dependencias build.
- Declara vulnerabilidades sin escaneo real.
- Publica, despliega, firma o etiqueta Git.
- Incluye secretos o runtime state.

## 8. Riesgos y limitaciones

Esta es una primera versión local. No reemplaza SCA industrial, no consulta vulnerabilidades ni licencias, no firma artefactos y no verifica checksums contra paquetes generados. Es una base auditable que debe evolucionar en Sprint 81 y posteriores.

## 9. Comandos de verificación

```powershell
python -m devpilot_core release sbom --json
python -m devpilot_core release sbom --json --write-report
python -m devpilot_core validate-artifact docs_security\supply_chain_policy.md --json
python -m devpilot_core schema validate-manifest docsunctional_sprint_80_manifest.json --json
python -m pytest tests	est_release_sbom.py tests	est_sprint_80_documentation.py -q
```

## 10. Conclusión

Sprint 80 habilita el inventario de componentes y dependencias requerido para avanzar hacia checksums, smoke tests y verificación de release. No introduce acciones destructivas ni dependencias nuevas.
