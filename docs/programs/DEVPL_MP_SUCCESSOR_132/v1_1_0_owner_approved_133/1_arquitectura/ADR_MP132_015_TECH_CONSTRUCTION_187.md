---
doc_id: ADR-MP132-015-187
title: "Selección tecnológica y preparación de construcción"
status: "PROGRAMMATIC_AMENDMENT"
version: "1.0.0"
date: "2026-10-17"
planning_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
execution_authority: false
---
# ADR MP132-015 — Technology Decision and Construction Readiness

## Contexto

Un stack hardcoded antes de Architecture contradice la selección por drivers MIPSoftware; un ADR aprobado sin scaffold, locks y comandos ejecutables tampoco garantiza preparación para construir. Pilot B define restricciones y resultados; no fija React/FastAPI/SQLite automáticamente.

## Decisión

1. En Architecture, la IA genera recomendación y alternativas razonadas **solo cuando son materialmente distintas**, desde RF, atributos de calidad, datos, riesgos, operación, presupuesto, skills y contexto. El Owner decide TechnologyProfile/ADRs dentro de approval Architecture; no duplicar autorizaciones.
2. El catálogo determinístico valida soporte, versiones/licencias, restricciones y compatibilidad, y registra consecuencias. No auto-instala dependencias ni ejecuta red por aprobar la arquitectura.
3. Un Technical Scaffold Workbench separado ejecuta plan/diff/approval/atomic apply para manifests, lockfiles, estructura, configuración sin secretos, comandos `run/test/lint/build`, health y estrategia de rollback. Reutiliza lifecycle de cambios existente.
4. `ConstructionReadiness` une Product/Technical Baseline FROZEN, PESP/MIASI contextual, decision/ADRs, scaffold, tests/Quality, Planning Increment+Sprint+Story READY y Git/source policy. N/A se justifica; blockers reales impiden avance sin introducir checklist Owner inocuo.

## Validación

Falla en proveedor, versión incompatible, dependency network deny, scaffold drift/partial, prueba de arranque, permisos de proyecto, lock missing, concurrencia y restart deben producir feedback recuperable. R3 gobierna Tech/Scaffold, R4 Planning, R5 construcción y R6 operación. No seleccionar tecnología ni ejecutar nada por esta ADR documental.
