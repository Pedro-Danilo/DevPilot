---
title: "Auditoría FUNC-SPRINT-36 — DependencyGraph e import graph Python"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-36-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-36 — DependencyGraph e import graph Python

## 1. Propósito

Registrar la implementación de `FUNC-SPRINT-36 — DependencyGraph e import graph Python` como segundo sprint de Fase C.

## 2. Estado

Implementado en estado `implemented-initial`. La capacidad es local-first, read-only, determinística y no ejecuta el código analizado.

## 3. Funcionamiento técnico

`DependencyGraphBuilder` recorre archivos `.py` bajo un target controlado, excluye directorios runtime/caches y usa `ast.parse` para extraer imports. El motor no importa módulos, no invoca `python` sobre los archivos analizados y no llama red ni APIs externas.

El grafo resultante incluye:

- nodos por módulo Python;
- edges internas `source -> target`;
- imports externos por módulo;
- métricas `fan_in` y `fan_out`;
- dependientes y dependencias por módulo;
- findings de syntax error sin crash;
- notas explícitas sobre límites de imports dinámicos.

## 4. Integración con DevPilot

El nuevo comando CLI es:

```powershell
python -m devpilot_core repo dependency-graph --target src/devpilot_core --json
python -m devpilot_core repo dependency-graph --target src/devpilot_core --json --write-report
```

El comando devuelve `CommandResult`, soporta `--json`, puede escribir evidencia JSON/Markdown con `ReportEngine`, registra evento local y persiste historial operacional best-effort. Además, MIASI declara `repo.dependency_graph` como tool read-only y habilita su uso futuro por `repo.analysis` sin convertirlo todavía en agente ejecutor.

## 5. Rol dentro de DevPilot

Esta capacidad habilita FC-L1 de Fase C en su primera versión: repo intelligence basada en dependencias internas. Sirve como insumo para `RepoAnalyzer v2`, architecture/code drift, review rule packs, quality gates y futuros refactors controlados.

## 6. Criterios PASS

- Extrae imports Python con AST sin ejecutar código.
- Reporta nodos, edges, fan-in, fan-out, dependientes y dependencias.
- Separa imports internos de imports externos.
- Ignora `outputs/`, `.git/`, `.venv/`, caches y build artifacts.
- Un archivo Python inválido genera finding controlado y no rompe el análisis completo.
- El comando soporta `--json` y `--write-report`.
- La tool queda declarada en MIASI como read-only.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- Ejecutar o importar módulos analizados.
- Seguir symlinks fuera del workspace.
- Usar red, APIs externas o modelos.
- Tratar imports dinámicos como certeza absoluta.
- Modificar archivos del repositorio durante el análisis.

## 8. Riesgos

- Imports dinámicos con `importlib`, plugins o construcción runtime de nombres pueden no detectarse.
- Los edges expresan dependencias de import, no llamadas reales ni acoplamiento semántico completo.
- Repositorios muy grandes requerirán límites, perfiles y paginación más sofisticados.
- El matching interno inicial está optimizado para paquetes Python convencionales bajo `src/<package>`.

## 9. Veredicto

`FUNC-SPRINT-36` queda implementado como DependencyGraph inicial. Es una base apropiada para `FUNC-SPRINT-37 — RepoAnalyzer v2: estructura, riesgos y salud del repositorio`, pero todavía no reemplaza análisis semántico, SAST/SCA ni revisión arquitectónica completa.
