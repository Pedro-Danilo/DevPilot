---
doc_id: DEVPL-OPS-RELEASE-VERIFICATION-001
title: DevPilot Local — Checksums, smoke tests y verificación de release
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-06-17
approval: approved_after_func_sprint_81_validation
sprint: FUNC-SPRINT-81
phase: FASE-G-PRODUCTIZACION-RELEASE
---

# DevPilot Local — Checksums, smoke tests y verificación de release

## Estado

Documento aprobado como implementación inicial de `FUNC-SPRINT-81`.


## 1. Propósito

Este documento define el procedimiento operativo inicial para verificar artefactos locales de release de DevPilot. `FUNC-SPRINT-81` introduce tres capacidades gobernadas:

- `release checksum`: calcula SHA256 sobre un artefacto real/local.
- `release smoke-test`: ejecuta comprobaciones mínimas de contenedor y CLI sin red.
- `release verify`: consolida checksum y smoke test en un reporte de verificación.

La implementación es `implemented-initial`: verifica integridad local y smoke básico, pero no firma, no publica, no despliega, no etiqueta Git y no reemplaza una validación completa de instalación/upgrade.

## 2. Requisitos previos

Antes de ejecutar la verificación de release debe existir un artefacto local generado por Sprint 79:

```powershell
python -m devpilot_core package build --kind all --version 0.1.0 --execute --json --write-report
```

Artefacto recomendado para la verificación inicial:

```text
dist/release/devpilot-local-0.1.0-source.zip
```

## 3. Comandos principales

```powershell
python -m devpilot_core release checksum --artifact dist/release/devpilot-local-0.1.0-source.zip --json
python -m devpilot_core release smoke-test --artifact dist/release/devpilot-local-0.1.0-source.zip --json
python -m devpilot_core release verify --artifact dist/release/devpilot-local-0.1.0-source.zip --json --write-report
```

Con `--write-report`, `release verify` genera:

```text
outputs/reports/release_verification.json
outputs/reports/release_verification.md
outputs/reports/checksums.sha256
```

## 4. Funcionamiento técnico

`release checksum` valida que el artefacto exista dentro del workspace y calcula SHA256 leyendo bytes locales.

`release smoke-test` valida:

- existencia del artefacto;
- formato soportado: `.zip`, `.whl` o `.tar.gz`;
- integridad de contenedor ZIP/TAR;
- ausencia de entradas prohibidas como `.git/`, `.venv/`, `node_modules/`, `outputs/`, `dist/`, caches, `.devpilot/devpilot.db` y `.devpilot/providers.yaml`;
- presencia de archivos mínimos cuando el artefacto es ZIP fuente;
- ejecución explícita de `python -m devpilot_core --version` y verificación de su exit code.

`release verify` ejecuta checksum y smoke test, consolida resultados, conserva exit codes observados y devuelve `PASS` o `BLOCK` según el resultado.

## 5. Criterios PASS

- El artefacto existe y está dentro del workspace.
- Se calcula SHA256.
- El smoke test no requiere red ni APIs externas.
- El smoke test observa y respeta exit codes.
- El reporte consolidado indica `release_verified=true`.
- Los reportes se escriben únicamente bajo `outputs/reports`.
- No hay publicación, despliegue, firma, Git tagging ni mutación de fuente.

## 6. Criterios BLOCK

- El artefacto no existe.
- El artefacto está fuera del workspace.
- El contenedor no puede abrirse o tiene entradas corruptas.
- El artefacto contiene runtime state, outputs, caches, `.git`, `.venv`, `node_modules`, `dist` interno o secretos evidentes.
- El smoke test ignora exit codes.
- El comando publica, despliega, firma o etiqueta Git.

## 7. Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-81-001 | Verificar un artefacto inexistente o equivocado. | Bloquear si el archivo no existe y mostrar ruta. |
| RISK-FUNC-81-002 | Falso positivo por smoke superficial. | Inspeccionar contenedor y ejecutar CLI con exit code observado. |
| RISK-FUNC-81-003 | Confundir checksum con firma. | Documentar que SHA256 no reemplaza firma criptográfica. |
| RISK-FUNC-81-004 | Contaminar evidencia de release con outputs. | Los outputs se regeneran y no se incluyen en ZIP fuente. |

## 8. Límites y evolución pendiente

Sprint 81 no implementa instalador, prueba de upgrade, backup/restore, firma criptográfica, publicación externa ni ReleaseAgent. Es una primera versión local de verificación de integridad y smoke test. La evolución industrial debe agregar:

- smoke install en ambiente aislado;
- validación de wheel/sdist instalados;
- verificación cruzada con SBOM y release manifest;
- firma opcional;
- provenance/SLSA más robusto;
- integración con ReleaseAgent dry-run de Sprint 84.
