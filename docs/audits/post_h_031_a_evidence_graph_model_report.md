---
doc_id: POST-H-031-A-EVIDENCE-GRAPH-MODEL-REPORT
title: "POST-H-031-A - Evidence graph model report"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-10"
approval: approved
---

# POST-H-031-A - Evidence graph model report

## 1. Propósito

POST-H-031-A inicia la ola `POST-H-031 — Observabilidad, evidence graph y operador` con un modelo local, determinístico, schema-backed y read-only para representar evidencia operacional de DevPilot.

El objetivo inmediato es que futuras vistas de operador puedan consumir un grafo único de evidencia, claims, no-go gates, gaps y runtime signals sin leer manualmente `.devpilot/`, `docs/`, schemas y reportes regenerables.

## 2. Implementado

- Schema `EvidenceGraph` en `docs/schemas/evidence_graph.schema.json`.
- Configuración versionada de fuentes en `.devpilot/evidence/evidence_graph_sources.json`.
- Bounded context `src/devpilot_core/evidence_graph/` con modelos y builder.
- Método `ApplicationService.evidence_graph(...)` para exponer el grafo sin duplicar lógica en CLI.
- Comando `python -m devpilot_core evidence graph --json`.
- Escritura explícita de reportes JSON/Markdown bajo `outputs/reports` mediante `--write-report`.
- Pruebas focales en `tests/test_post_h_031_evidence_graph_model.py`.

## 3. Implementado inicial

Esta versión es `implemented-initial/local-first`. El grafo modela evidencias y relaciones, pero todavía no implementa el health summary, gap-to-action mapping, claims/no-go dashboard completo ni export UX redactado. Esas capacidades corresponden a POST-H-031-B/C/D/E.

## 4. Contrato de seguridad

PASS requiere que el modelo permanezca read-only por defecto y que no ejecute comandos, no lea secretos, no lea `.devpilot/devpilot.db`, no use red, no use APIs externas y no mutile archivos fuente.

`--write-report` solo puede escribir evidencia regenerable bajo `outputs/reports`. Los ZIPs limpios no deben incluir `outputs/`.

## 5. Criterios PASS

- El grafo valida contra `SCHEMA-DEVPL-EVIDENCE-GRAPH-V1`.
- Las fuentes requeridas versionadas existen y se representan como nodos.
- Las fuentes runtime ausentes bajo `outputs/` se representan como `missing_expected`, sin promoverse a PASS.
- Claims permitidos/prohibidos y no-go gates principales quedan representados.
- `graph_declares_readiness=false`.
- El comando CLI y `ApplicationService` devuelven `CommandResult` compatible.

## 6. Criterios BLOCK

- Fuente prohibida hacia `.env`, `.devpilot/devpilot.db`, `.sqlite` o `.db`.
- Lectura de secretos o payloads crudos.
- Red, APIs externas o ejecución de comandos.
- Declaración de readiness desde el evidence graph.
- Escritura fuera de `outputs/reports` cuando se solicita reporte.

## 7. Comandos de verificación

```powershell
$env:PYTHONPATH="src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_evidence_graph_model.py -q
python -m devpilot_core evidence graph --json
python -m devpilot_core evidence graph --json --write-report
python -m devpilot_core schema validate --schema-id EvidenceGraph --instance outputs/reports/evidence_graph.json --json
```

## 8. Riesgos y limitaciones

- El grafo inicial es una capa de lectura y relación, no un dashboard final.
- La completitud operacional depende de que las fuentes versionadas sigan sincronizadas en docs governance y TCR.
- Las evidencias runtime bajo `outputs/` son regenerables y pueden estar ausentes en ZIPs limpios.
- Los próximos sprints deben convertir gaps en acciones concretas, resúmenes de salud y exports redactados de operador.

## 9. Próximo paso

`POST-H-031-B — Operator health summary` debe construir una vista resumida para operador sobre este grafo sin cambiar la semántica de los gates formales.
