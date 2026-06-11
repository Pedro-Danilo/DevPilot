---
title: "Auditoría FUNC-SPRINT-37 — RepoAnalyzer v2"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-37-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-37 — RepoAnalyzer v2

## 1. Propósito

Registrar la implementación de `FUNC-SPRINT-37 — RepoAnalyzer v2: estructura, riesgos y salud del repositorio` como tercer sprint de Fase C.

## 2. Estado

Implementado en estado `implemented-initial`. La capacidad es local-first, read-only y heurística. No debe interpretarse como certificación industrial de calidad, SAST/SCA, análisis de licencias ni quality gate definitivo.

## 3. Funcionamiento técnico

`RepoAnalyzer` consolida señales de:

- `RepoInventory`: estructura, categorías, tamaños y riesgos de archivos;
- `DependencyGraphBuilder`: nodos, edges, imports externos, fan-in y fan-out;
- `GitAdapter.status()`: estado Git si el workspace tiene repositorio Git disponible.

El analizador excluye `outputs/`, `.git/`, `.venv/`, caches, `build/`, `dist/` y `.devpilot/devpilot.db`. También ejecuta un escaneo acotado para TODO/FIXME/HACK sin emitir líneas de código y reusa detección de secretos sintéticos sin imprimir valores crudos.

## 4. Integración con DevPilot

El nuevo comando CLI es:

```powershell
python -m devpilot_core repo analyze --json
python -m devpilot_core repo analyze --json --write-report
```

La tool MIASI `repo.analyze` queda declarada como read-only y asignada al agente futuro `repo.analysis`.

## 5. Rol dentro de DevPilot

`RepoAnalyzer` es la primera capa de repo intelligence consolidada. Provee insumos para los sprints posteriores de architecture/code drift, review rule packs y repo quality gate dry-run.

## 6. Criterios PASS

- Devuelve `CommandResult` y soporta `--json`.
- Genera reportes JSON/Markdown con `--write-report`.
- No modifica archivos.
- No usa red, APIs externas ni modelos y no ejecuta ni importa código analizado.
- No ejecuta ni importa código analizado.
- Repos sin Git producen análisis parcial controlado.
- No emite secretos crudos.
- README, runbook, MIASI, backlog, test strategy, manifest y pruebas quedan sincronizados.

## 7. Criterios BLOCK

- Mezclar `outputs/` o caches como fuente de salud del repo.
- Emitir secretos crudos en stdout, reportes o findings.
- Romper cuando Git no está inicializado.
- Presentar `health_score` como veredicto absoluto.
- Habilitar patch apply, Git write, refactor execution, deploy o sandbox real.

## 8. Riesgos

- El `health_score` puede ser malinterpretado como certificación.
- Las heurísticas de módulos sin test cercano pueden generar falsos positivos.
- La detección de TODO/FIXME es textual y acotada.
- No hay análisis de vulnerabilidades, licencias, complejidad ciclomática industrial ni coverage real.

## 9. Veredicto

`FUNC-SPRINT-37` queda implementado como baseline inicial de RepoAnalyzer v2. La implementación es correcta para continuar hacia `FUNC-SPRINT-38 — Architecture/code drift inicial`, manteniendo bloqueadas las capacidades destructivas.
