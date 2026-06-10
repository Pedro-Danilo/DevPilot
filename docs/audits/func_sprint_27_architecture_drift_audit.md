---
title: "Auditoría FUNC-SPRINT-27 — Architecture/code drift inicial"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-27-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-27"
updated: "2026-06-10"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_owner_direction"
approved_by: "Ordóñez"
approved_at: "2026-06-10"
---
# Auditoría FUNC-SPRINT-27 — Architecture/code drift inicial

## 1. Propósito

Documentar la implementación de `FUNC-SPRINT-27 — Architecture/code drift inicial y cierre de Baseline Industrial Mínima`. El sprint agrega una primera validación ejecutable para comparar módulos de `src/devpilot_core/*` contra documentos C4/arquitectura y cerrar formalmente la Fase A con checklist, reporte y evidencia.

## 2. Estado

| Campo | Valor |
|---|---|
| Estado de implementación | `implemented-initial` |
| Tipo de validación | Heurística, local, read-only |
| Mutaciones | Ninguna sobre código/docs fuente |
| Red/API keys | No requeridas |
| ADR nueva | No requerida |

## 3. Funcionamiento técnico

El módulo `src/devpilot_core/traceability/architecture_drift.py` implementa `ArchitectureDriftDetector`. Su flujo es:

1. localiza la raíz `src/devpilot_core`;
2. enumera paquetes y módulos top-level relevantes;
3. carga documentos de arquitectura controlados: `architecture_document.md`, `c4_container.md` y `c4_component.md`;
4. aplica aliases conservadores por módulo;
5. emite `ARCHITECTURE_DRIFT_CODE_MODULE_UNDOCUMENTED` cuando un módulo no está representado explícitamente;
6. devuelve `CommandResult` con summary, módulos, documentos y findings;
7. preserva severidad `warning` para diferencias heurísticas, sin bloquear.

La integración se expone por medio de `TraceabilityEngine.architecture_drift()` y el comando:

```powershell
python -m devpilot_core traceability architecture-drift --json
python -m devpilot_core traceability architecture-drift --json --write-report
```

## 4. Integración y rol dentro de DevPilot

El detector se integra dentro del namespace `traceability` porque evalúa coherencia entre arquitectura documentada y código implementado. Complementa:

- `traceability scan`;
- `traceability validate`;
- `traceability coverage`;
- `traceability report`;
- `validate all`;
- C4 Component reconciliado.

No reemplaza análisis arquitectónico manual, ADRs ni revisión de diseño. Su valor es convertir drift evidente en evidencia local y reproducible.

## 5. Criterios PASS

- Existe `ArchitectureDriftDetector`.
- Existe comando `traceability architecture-drift`.
- El comando devuelve `CommandResult` JSON.
- El comando soporta `--write-report`.
- Los findings son no destructivos.
- `ARCHITECTURE_DRIFT_CODE_MODULE_UNDOCUMENTED` usa severidad warning.
- El detector no modifica archivos.
- No usa red ni API keys.
- No agrega dependencia externa.
- `pytest -q` pasa.

## 6. Criterios BLOCK

- El detector modifica documentos o código fuente.
- El detector bloquea por diferencias de naming menores.
- Se declara Fase A cerrada sin Schema Validator o Traceability Engine.
- Se declara como implementada una capacidad que sigue `planned`, `future` o `disabled`.
- Se introduce dependencia externa sin ADR.

## 7. Riesgos

- Los aliases pueden no cubrir todos los nombres usados por arquitectura.
- Puede reportar falsos positivos si un módulo está descrito con otro nombre.
- Puede reportar falsos negativos si un alias aparece de forma incidental.
- La validación es **implemented-initial** y no reemplaza análisis arquitectónico manual.

## 8. Veredicto

Sprint 27 cumple el alcance de Fase A: drift inicial, checklist de salida, reporte de cierre, manifest, pruebas y documentación sincronizada. La Baseline Industrial Mínima queda cerrada como base local-first verificable, con evolución posterior hacia Fase B.
