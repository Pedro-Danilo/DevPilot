---
title: "Correctivo FUNC-SPRINT-71 — Sincronización de tests históricos Fase F"
doc_id: "DEVPL-AUDIT-CORR-FUNC-SPRINT-71-HISTORICAL-TESTS-SYNC"
status: "approved"
version: "1.0.0"
updated: "2026-06-16"
owner: "Ordóñez"
approval: "Aprobado para corrección de pruebas históricas Sprint 71"
source_repo: "repo_DevPilot_Local_90.zip"
related_sprint: "FUNC-SPRINT-71"
correction_type: "test/documentation synchronization"
preliminary: true
---

# Correctivo FUNC-SPRINT-71 — Sincronización de tests históricos Fase F

## 0. Estado

Veredicto: `PASS`.

## 1. Propósito

Documentar y validar el correctivo aplicado a las pruebas históricas de Fase F después de implementar `FUNC-SPRINT-71`, preservando la trazabilidad de alcance sin bloquear la evolución legítima de la Web UI.

## 2. Causa raíz

Después de implementar `FUNC-SPRINT-71`, la suite completa fallaba en siete pruebas documentales. Las causas fueron:

1. Tests históricos de Sprint 64 a Sprint 69 seguían esperando `source_repo: "repo_DevPilot_Local_88.zip"`, pero el backlog Fase F vigente quedó correctamente sincronizado como `source_repo: "repo_DevPilot_Local_89.zip"`, porque Sprint 71 se implementó a partir del repo de cierre Sprint 70.
2. `tests/test_sprint_69_documentation.py` seguía verificando en el README actual de `ui/web` la frase `No implementa Report Viewer`. Esa frase era válida para el alcance histórico de Sprint 69, pero dejó de ser válida cuando Sprint 70 implementó Report Viewer y Trace Viewer y Sprint 71 añadió Approval Center.
3. Persistía un `package-lock.json` accidental en la raíz del repositorio, aunque el manifest de Sprint 71 lo declaraba como eliminado. El lock válido es `ui/web/package-lock.json`.

## 3. Alcance del patch

Archivos ajustados:

- `tests/test_sprint_64_documentation.py`
- `tests/test_sprint_65_documentation.py`
- `tests/test_sprint_66_documentation.py`
- `tests/test_sprint_67_documentation.py`
- `tests/test_sprint_68_documentation.py`
- `tests/test_sprint_69_documentation.py`
- `package-lock.json` eliminado de raíz
- `docs/audits/corrective_sprint71_historical_tests_sync_audit.md`

## 4. Decisión de corrección

Los tests históricos deben verificar dos cosas diferentes:

- Estado global vigente de la aplicación: último hito `FUNC-SPRINT-71`, siguiente hito `FUNC-SPRINT-72`, backlog y contrato actual sincronizados.
- Alcance histórico preservado: limitaciones propias de Sprint 69 deben comprobarse en la auditoría de Sprint 69, no en el README actual de la Web UI que legítimamente evoluciona en Sprint 70 y Sprint 71.

Por eso `tests/test_sprint_69_documentation.py` ahora valida que la auditoría de Sprint 69 conserve la nota histórica sobre Report/Trace Viewer y que el README actual documente las capacidades ya implementadas.

## 5. Impacto funcional

Sin impacto funcional.

No se modifican:

- endpoints API;
- seguridad token/CORS;
- `ApplicationService`;
- Web UI runtime;
- OpenAPI;
- PolicyEngine;
- Approval Center;
- Action Launcher.

## 6. Criterios PASS

- `pytest -q` no falla por `source_repo` obsoleto.
- Los tests históricos conservan trazabilidad sin bloquear evolución posterior.
- `package-lock.json` raíz no existe.
- `ui/web/package-lock.json` permanece como lockfile válido del frontend.
- `validate all` no tiene bloqueantes.

## 7. Criterios BLOCK

- Bloquear si se cambia el backlog para hacerlo coincidir con tests obsoletos.
- Bloquear si se borra el lockfile correcto `ui/web/package-lock.json`.
- Bloquear si se elimina la evidencia histórica de límites Sprint 69 en la auditoría.
- Bloquear si los tests históricos vuelven a afirmar limitaciones superadas por sprints posteriores en artefactos vivos.

## 8. Comandos de verificación

```powershell
python -m pytest tests/test_sprint_64_documentation.py tests/test_sprint_65_documentation.py tests/test_sprint_66_documentation.py tests/test_sprint_67_documentation.py tests/test_sprint_68_documentation.py tests/test_sprint_69_documentation.py -q
python -m pytest tests/test_sprint_*_documentation.py tests/test_phase_f_web_first_strategy.py -q
python -m devpilot_core validate-artifact docs/audits/corrective_sprint71_historical_tests_sync_audit.md --json
python -m devpilot_core validate all --json
python -m pytest -q
```

## 9. Conclusión

El fallo era un problema de sincronización de pruebas documentales acumulativas, no un defecto funcional de Sprint 71. El correctivo deja las pruebas alineadas con el estado vigente y conserva la trazabilidad histórica del alcance Sprint 69 en la auditoría correspondiente.
