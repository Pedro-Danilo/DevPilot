---
doc_id: DEVPL-SUPPLY-CHAIN-POLICY
status: approved
title: DevPilot Local — Supply-chain policy baseline
owner: Ordóñez
standard: MIPSoftware
extension: MIASI
updated: 2026-06-17
version: 1.0.0
approval: internal
---

# DevPilot Local — Supply-chain policy baseline

## 0. Estado

Este documento queda aprobado como baseline inicial de seguridad de cadena de suministro para `FUNC-SPRINT-80`. Es una primera versión `implemented-initial`: inventaría dependencias locales y declara controles mínimos, pero no ejecuta SCA externo, no consulta bases de vulnerabilidades, no firma artefactos y no calcula checksums finales.

## 1. Propósito

Definir cómo DevPilot genera evidencia local de componentes y dependencias antes de fortalecer release con checksums, smoke install, firma, provenance y ReleaseAgent. El objetivo inmediato es evitar releases sin inventario de dependencias runtime, dev, build y UI.

## 2. Fuentes de verdad

Las fuentes locales autorizadas para el SBOM baseline son:

- `pyproject.toml` para dependencias Python runtime, opcionales/dev y build-system.
- `ui/web/package.json` para dependencias directas de la Web UI.
- `ui/web/package-lock.json` para componentes npm bloqueados/transitivos cuando exista.
- `docs/functional_sprint_*_manifest.json` para trazabilidad de sprints de release.

No se usan package registries, vulnerability feeds, GitHub APIs, PyPI APIs, npm APIs ni servicios externos.

## 3. Comando operativo

```powershell
python -m devpilot_core release sbom --json
python -m devpilot_core release sbom --json --write-report
```

Con `--write-report` se generan evidencias regenerables bajo:

```text
outputs/reports/release_sbom.json
outputs/reports/release_sbom.md
```

## 4. Modelo SBOM baseline

El SBOM incluye:

- metadata de release local;
- dependencias Python runtime;
- dependencias Python opcionales/dev;
- dependencias de build Python;
- dependencias directas npm;
- componentes bloqueados en `package-lock.json` cuando existan;
- payload CycloneDX-compatible preliminar;
- declaración de límites SLSA local-baseline.

## 5. Controles mínimos

- No usar red.
- No llamar APIs externas.
- No publicar ni desplegar.
- No mutar archivos fuente.
- No embebER secretos.
- No declarar vulnerabilidades si no se ejecutó un escaneo real.
- Reportar explícitamente si no hay lockfile o si una fuente local no existe.

## 6. Criterios PASS

- El comando `release sbom --json` retorna `CommandResult` parseable.
- Declara dependencias runtime y dev.
- Declara dependencias de build.
- Declara dependencias UI directas y bloqueadas cuando existan.
- Expone un payload CycloneDX-compatible preliminar.
- Declara que no hubo vulnerability scan remoto.
- Genera reportes únicamente bajo `outputs/reports` cuando se usa `--write-report`.

## 7. Criterios BLOCK

- Requerir red para generar el SBOM.
- Omitir dependencias dev.
- Omitir dependencias de build.
- Presentar el SBOM inicial como SCA completo.
- Publicar, desplegar, firmar o etiquetar Git desde el comando SBOM.
- Incluir secretos o runtime state como componentes de release.

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Falso sentido de seguridad | Declarar explícitamente que no hay vulnerability scan ni license scan. |
| Dependencias ocultas | Parsear `pyproject.toml`, `package.json` y `package-lock.json`. |
| Formato incompleto | Mantener compatibilidad progresiva con CycloneDX y evolucionar a schema dedicado. |
| Drift entre packaging y SBOM | Integrar el SBOM como artefacto esperado del Release Manifest. |

## 9. Evolución pendiente

- Schema JSON formal para `release_sbom`.
- Validación dedicada de CycloneDX.
- License scanning local o externo gobernado.
- Vulnerability scanning opcional con modo offline/cacheado.
- Checksums y verificación cruzada con paquetes generados.
- Provenance/SLSA más allá de `local-baseline`.
