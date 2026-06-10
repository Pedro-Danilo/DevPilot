---
title: "FUNC-SPRINT-25 — Traceability Model y extracción de entidades SDLC"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-25-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-25"
updated: "2026-06-10"
approval: "approved_by_owner"
---

# FUNC-SPRINT-25 — Traceability Model y extracción de entidades SDLC

## 1. Propósito

Este artefacto audita la implementación de `FUNC-SPRINT-25`. El sprint crea la primera capa ejecutable de trazabilidad SDLC mediante modelos serializables y un extractor local conservador de IDs explícitos en documentos Markdown/JSON.

El resultado es una versión **implemented-initial** del `Traceability Model`: detecta entidades `FR-*`, `REQ-*`, `US-*`, `AC-*`, `TEST-*` y `ADR-*`, reporta duplicados e IDs mal formados, y no infiere relaciones semánticas complejas.

## 2. Alcance implementado

Se implementó:

- paquete `src/devpilot_core/traceability/`;
- modelos `TraceEntity`, `TraceLink`, `TraceGraph` e `InvalidTraceToken`;
- extractor `MarkdownTraceabilityExtractor`;
- comando CLI `traceability scan`;
- soporte `--json` y `--write-report`;
- detección de IDs duplicados;
- detección de tokens ID-like mal formados;
- pruebas con fixtures y repo real;
- sincronización de README, runbook, backlog Fase A y manifest.

No se implementó:

- cobertura Req→AC→Test;
- inferencia de relaciones semánticas;
- validación de gaps de trazabilidad;
- reporte de cobertura SDLC;
- modificación automática de documentos;
- UI;
- APIs externas;
- ejecución de agentes;
- cambios en MIASI tools/policies/agents.

## 3. Funcionamiento técnico

`MarkdownTraceabilityExtractor` resuelve fuentes locales dentro del workspace, lee únicamente archivos `.md` y `.json`, y aplica dos patrones:

- patrón estricto para entidades válidas: `FR-*`, `REQ-*`, `US-*`, `AC-*`, `TEST-*`, `ADR-*` con segmentos alfanuméricos en mayúscula;
- patrón amplio para detectar tokens similares que no cumplen el contrato y reportarlos como `TRACEABILITY_ENTITY_ID_INVALID`.

El extractor produce un `TraceGraph` serializable con:

- `entities`: ocurrencias detectadas;
- `links`: lista vacía por diseño en Sprint 25;
- `invalid_tokens`: tokens mal formados;
- `duplicate_entity_ids`: ocurrencias repetidas por ID;
- `source_paths`: fuentes escaneadas.

El comando `traceability scan` devuelve un `CommandResult`. Los duplicados e inválidos son warnings no bloqueantes en esta primera versión, porque el objetivo del sprint es extraer y reportar, no cerrar cobertura SDLC.

## 4. Integración y rol dentro de DevPilot

Sprint 25 inaugura `src/devpilot_core/traceability/` como capa base para la trazabilidad de DevPilot. Se integra con:

| Componente | Relación |
|---|---|
| `cli.py` | Expone `python -m devpilot_core traceability scan`. |
| `CommandResult` | Normaliza salida y findings. |
| `ReportEngine` | Persiste evidencia con `--write-report`. |
| `EventLogger` | Emite evento local best-effort desde CLI. |
| `LocalStore` | Persiste historial best-effort desde CLI. |
| `ValidationGateway` | Queda como precondición de calidad documental/contractual, sin duplicar trazabilidad. |

El rol de Sprint 25 es preparar Sprint 26, donde se implementarán validación, cobertura y reportes de trazabilidad.

## 5. Comandos de uso

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core traceability scan --json
python -m devpilot_core traceability scan --json --write-report
python -m devpilot_core traceability scan --target docs/01_requirements --target docs/04_quality/test_strategy.md --json
python -m pytest tests/test_traceability_extractors.py -q
python -m pytest -q
```

## 6. Criterios PASS

- `src/devpilot_core/traceability/` es importable.
- `TraceEntity`, `TraceLink` y `TraceGraph` son serializables a JSON.
- El extractor detecta IDs `FR-*`, `REQ-*`, `US-*`, `AC-*`, `TEST-*`, `ADR-*`.
- El extractor reporta duplicados con `TRACEABILITY_ENTITY_DUPLICATE`.
- El extractor reporta IDs mal formados con `TRACEABILITY_ENTITY_ID_INVALID`.
- El comando `traceability scan` devuelve `CommandResult`.
- El comando soporta `--json`.
- El comando soporta `--write-report`.
- El comando no modifica documentos.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- El extractor infiere relaciones no presentes.
- El comando modifica archivos fuente.
- No hay findings para duplicados.
- El scan acepta targets fuera del workspace.
- La salida no cumple `CommandResult`.
- Se agregan dependencias externas sin ADR.

## 8. Riesgos

- La extracción es heurística y puede reportar referencias de documentación como duplicados aunque sean menciones legítimas.
- Los tokens con nombres de archivo, por ejemplo ADRs con sufijo `.md`, pueden aparecer como ID-like mal formados; esto es intencionalmente conservador.
- El grafo aún no mide cobertura ni gaps.
- Los links se mantienen vacíos hasta que exista extracción explícita de relaciones o reglas de cobertura.

## 9. ADR

No se creó ADR nueva porque Sprint 25 no introduce dependencia externa, almacenamiento nuevo, proveedor, política runtime ni acción destructiva. La implementación usa biblioteca estándar, `CommandResult`, `ReportEngine`, `EventLogger` y `LocalStore` ya existentes.

## 10. Pruebas implementadas

- `tests/test_traceability_extractors.py`
- `tests/fixtures/traceability/traceability_fixture.md`
- `tests/test_sprint_25_documentation.py`

## 11. Evolución recomendada

El siguiente paso es `FUNC-SPRINT-26 — Traceability Engine: validate, coverage y report`. Ese sprint debe consumir el `TraceGraph` de Sprint 25 para reportar gaps y cobertura sin modificar documentos.
