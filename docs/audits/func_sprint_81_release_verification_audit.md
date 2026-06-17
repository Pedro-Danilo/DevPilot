---
doc_id: DEVPL-AUDIT-FUNC-SPRINT-81
title: FUNC-SPRINT-81 — Checksums, smoke tests y verificación de release — Auditoría
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-06-17
approval: approved_after_func_sprint_81_validation
sprint: FUNC-SPRINT-81
phase: FASE-G-PRODUCTIZACION-RELEASE
---

# FUNC-SPRINT-81 — Checksums, smoke tests y verificación de release — Auditoría

## Estado

Documento aprobado como implementación inicial de `FUNC-SPRINT-81`.


## 1. Propósito

Registrar la implementación inicial de la verificación local de release para DevPilot: generación de SHA256, smoke test mínimo y reporte consolidado `release verify`.

## 2. Alcance implementado

`FUNC-SPRINT-81` agrega el módulo `devpilot_core.release.verification` y los comandos:

```powershell
python -m devpilot_core release checksum --artifact dist/release/devpilot-local-0.1.0-source.zip --json
python -m devpilot_core release smoke-test --artifact dist/release/devpilot-local-0.1.0-source.zip --json
python -m devpilot_core release verify --artifact dist/release/devpilot-local-0.1.0-source.zip --json --write-report
```

La verificación requiere un artefacto local real. No crea paquetes por sí sola; el paquete debe generarse con `package build --execute`.

## 3. Archivos creados

- `src/devpilot_core/release/verification.py`: builders de checksum, smoke test y verificación consolidada.
- `docs/05_operations/release_verification.md`: procedimiento operativo.
- `docs/audits/func_sprint_81_release_verification_audit.md`: auditoría del sprint.
- `docs/functional_sprint_81_manifest.json`: manifest funcional.
- `tests/test_release_verification.py`: pruebas de builders y CLI.
- `tests/test_sprint_81_documentation.py`: pruebas de sincronización documental.

## 4. Archivos modificados

- `src/devpilot_core/cli.py`: subcomandos `release checksum`, `release smoke-test`, `release verify`.
- `src/devpilot_core/release/__init__.py`: exportación de builders de verificación.
- `src/devpilot_core/release/manifest.py`: artefactos esperados de checksums/smoke/verification en Sprint 81.
- `README.md`, `docs/05_operations/runbook.md`, `docs/05_operations/release_manifest.md`, `docs/05_operations/release_artifacts_matrix.md`, `docs/devpilot_backlog_fase_G_productizacion_release.md`, `docs/functional_backlog_after_precode.md`, `docs/release/CHANGELOG.md`: sincronización de estado.

## 5. Criterios PASS

- SHA256 calculado sobre artefacto real/local.
- Smoke test inspecciona contenedor y ejecuta comando CLI mínimo.
- Exit codes son observados y usados para decidir PASS/BLOCK.
- `release verify` consolida checksum y smoke test.
- No hay red, API externa, publicación, despliegue, firma, Git tagging ni mutación de fuente.
- Reportes opcionales se limitan a `outputs/reports`.

## 6. Criterios BLOCK

- Artefacto inexistente.
- Artefacto fuera del workspace.
- Artefacto corrupto o formato no soportado.
- Artefacto contiene runtime state, outputs, caches, `.git`, `.venv`, `node_modules`, `dist` interno o secretos evidentes.
- Smoke test ignora exit codes.
- Cualquier publicación, despliegue, firma o Git tagging automático.

## 7. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-81-001 | Verificación sobre artefacto incorrecto. | Exigir `--artifact` explícito y archivo existente. |
| RISK-FUNC-81-002 | Smoke test superficial. | Validar contenedor y CLI con exit code. |
| RISK-FUNC-81-003 | Confundir checksum con firma. | Documentar límite; firma queda fuera de alcance. |
| RISK-FUNC-81-004 | Falta de instalación real. | Declarar smoke install/upgrade como evolución futura. |

## 8. Veredicto

`FUNC-SPRINT-81` queda en estado `implemented-initial`: suficiente para verificación local de integridad y smoke básico, pero aún no equivale a un pipeline de release con instalación aislada, firma, upgrade o publicación externa.
