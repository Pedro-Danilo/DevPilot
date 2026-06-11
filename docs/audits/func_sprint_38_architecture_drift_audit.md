---
title: "Auditoría FUNC-SPRINT-38 — Architecture/code drift inicial"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-38-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---
# Auditoría FUNC-SPRINT-38 — Architecture/code drift inicial

## 1. Propósito

Esta auditoría documenta la implementación de `FUNC-SPRINT-38 — Architecture/code drift inicial`. El objetivo del sprint es comparar la arquitectura documentada contra la estructura real del código, sin pretender análisis semántico completo ni certificación industrial.

## 2. Estado

El sprint queda implementado como capacidad `implemented-initial`. La nueva capacidad es local-first, read-only y heurística.

## 3. Funcionamiento técnico

El módulo `src/devpilot_core/repo/architecture_drift.py` implementa `ArchitectureDriftDetector`. El detector:

1. lee documentos controlados en `docs/02_architecture`;
2. extrae componentes desde tablas Markdown y nodos Mermaid;
3. obtiene módulos reales desde `DependencyGraphBuilder`;
4. incorpora señales resumidas de `RepoAnalyzer`;
5. construye una matriz `documented ↔ code`;
6. clasifica drift como `in_sync`, `doc_missing`, `code_missing` o `name_mismatch`;
7. asigna `confidence`, `match_type`, severidad y rationale.

## 4. Integración con DevPilot

La capacidad se expone mediante:

```powershell
python -m devpilot_core repo architecture-drift --json
python -m devpilot_core repo architecture-drift --json --write-report
```

También queda declarada como tool MIASI `repo.architecture_drift` para el agente futuro `repo.analysis`.

## 5. Rol dentro de DevPilot

El detector es una pieza de `FC-L2 — Drift y review industrial`. Su rol es generar una señal temprana de divergencia entre arquitectura y código antes de avanzar hacia rule packs, quality gates, patch preflight, sandbox y ejecución controlada.

## 6. Criterios PASS

- El comando devuelve `CommandResult`.
- El comando soporta `--json` y `--write-report`.
- Los findings separan `doc_missing`, `code_missing` y `name_mismatch`.
- La matriz incluye estado documental y confianza.
- No modifica documentos ni código.
- No ejecuta código analizado; no ejecuta ni importa código analizado. En términos operativos, no ejecuta código analizado.
- No usa red, APIs externas ni modelos; no usa red, APIs externas ni modelos.
- Componentes `planned`, `future` o `disabled` sin código no se tratan como bloqueantes.

## 7. Criterios BLOCK

- Inventar relaciones sin soporte en path, alias, nombre exacto o fuzzy matching explícito.
- Modificar documentación automáticamente.
- Ejecutar o importar código analizado.
- Usar LLM, red o API externa.
- Bloquear por componentes aspiracionales sin implementación.
- Habilitar patch apply, Git write, refactor execution, sandbox o deploy.

## 8. Riesgos

El matching es heurístico y puede producir falsos positivos o falsos negativos. La extracción Markdown/Mermaid depende del formato documental actual. En una versión industrial debería evolucionar hacia un Component Registry o Command Catalog versionado, con reglas explícitas de trazabilidad arquitectura-código.

## 9. Veredicto

`FUNC-SPRINT-38` queda implementado como capacidad inicial, segura y útil para revisión arquitectónica local. No reemplaza una auditoría arquitectónica manual ni un quality gate industrial definitivo.
