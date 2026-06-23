---
doc_id: "POST-H-005-BACKLOG"
id: "POST-H-005"
title: "POST-H-005 — Architecture map executable / dependency ownership"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
phase: "POST-FASE-H"
priority: "P0"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
adr_source: "docs/adr/ADR-POSTH-003-cli-modularization.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# POST-H-005 — Architecture map executable / dependency ownership

## 1. Objetivo

Convertir el mapa arquitectónico post-H en un **inventario ejecutable y reproducible** de paquetes, dependencias, ownership, hotspots, boundaries, contratos y riesgos de acoplamiento.

Este hito debe producir la base técnica para `POST-H-006 — CLI command registry`, `POST-H-007 — ApplicationService boundary hardening` y futuras decisiones de modularización.

## 2. Contexto

El reverse engineering identificó hotspots claros:

```text
src/devpilot_core/cli.py
src/devpilot_core/cli_models.py
src/devpilot_core/application/
src/devpilot_core/policy/
src/devpilot_core/miasi/
src/devpilot_core/schemas/
src/devpilot_core/agents/
src/devpilot_core/multiagent/
src/devpilot_core/testing/
src/devpilot_core/quality/
src/devpilot_core/industrial/
```

El mapa actual documenta la arquitectura, pero el siguiente paso es hacerlo ejecutable para evitar que el sistema siga creciendo por acumulación no gobernada.

## 3. Alcance

Incluye:

```text
- Inventario AST de módulos Python.
- Grafo de dependencias entre paquetes devpilot_core.
- Ownership declarativo por paquete/dominio.
- Detección de hotspots por LOC, imports, fan-in/fan-out, funciones, comandos CLI y tests asociados.
- Reporte JSON/Markdown.
- Baseline de límites arquitectónicos.
- Reglas iniciales de dependencia prohibida/restringida.
```

No incluye:

```text
- Refactor del CLI.
- Movimiento físico de módulos.
- Cambio de semántica de comandos.
- Enforcement blocking agresivo en primera iteración.
- Herramientas externas de análisis obligatorias.
```

## 4. Entregables

```text
src/devpilot_core/architecture/models.py
src/devpilot_core/architecture/inventory.py
src/devpilot_core/architecture/dependencies.py
src/devpilot_core/architecture/ownership.py
src/devpilot_core/architecture/hotspots.py
src/devpilot_core/architecture/report.py
src/devpilot_core/architecture/__init__.py
docs/schemas/architecture_map.schema.json
.devpilot/architecture/ownership_registry.json
docs/02_architecture/current_executable_architecture_map.md
tests/test_post_h_005_architecture_map.py
tests/test_architecture_ownership_registry.py
```

Generated outputs:

```text
outputs/reports/architecture_map.json
outputs/reports/architecture_map.md
```

## 5. Ownership registry mínimo

```json
{
  "schema_version": "1.0",
  "id": "DEVPL-ARCHITECTURE-OWNERSHIP",
  "packages": [
    {
      "package": "devpilot_core.policy",
      "domain": "governance.security",
      "owner": "architecture/security",
      "criticality": "P0",
      "allowed_dependencies": ["devpilot_core.cli_models", "devpilot_core.approval", "devpilot_core.identity"],
      "forbidden_dependencies": ["devpilot_core.interfaces", "devpilot_core.remote"],
      "test_contracts": ["policy-engine-critical"],
      "notes": "Cross-cutting security layer."
    }
  ]
}
```

## 6. Reporte de arquitectura mínimo

```json
{
  "schema_version": "1.0",
  "generated_at_utc": "...",
  "summary": {
    "packages_total": 0,
    "modules_total": 0,
    "dependencies_total": 0,
    "hotspots_total": 0,
    "forbidden_dependency_findings_total": 0,
    "unowned_packages_total": 0
  },
  "packages": [],
  "dependencies": [],
  "hotspots": [],
  "ownership_gaps": [],
  "recommendations": []
}
```

## 7. Micro-sprints propuestos

### POST-H-005-A — Modelos y schema de architecture map

Tareas:

```text
1. Definir ArchitectureModule, ArchitecturePackage, DependencyEdge, Hotspot, OwnershipEntry.
2. Crear architecture_map.schema.json.
3. Registrar schema en schema_catalog.
4. Crear ownership_registry.json inicial.
```

PASS:

```text
PASS si schema valida reporte mínimo.
PASS si ownership registry tiene paquetes críticos iniciales.
```

BLOCK:

```text
BLOCK si no se incluyen cli.py, policy, schemas, agents, testing y quality/industrial.
```

### POST-H-005-B — Inventario AST de paquetes y módulos

Tareas:

```text
1. Recorrer src/devpilot_core.
2. Calcular LOC, clases, funciones, imports, exports aproximados.
3. Identificar comandos CLI y handlers.
4. Relacionar tests por naming/path heurístico.
5. Excluir caches/venv/outputs.
```

Comando propuesto:

```powershell
python -m devpilot_core architecture inventory --json
```

### POST-H-005-C — Grafo de dependencias y boundaries

Tareas:

```text
1. Parsear imports internos devpilot_core.
2. Construir fan-in/fan-out por módulo/paquete.
3. Detectar dependencias UI/API → core correctas e incorrectas.
4. Detectar core → interfaces como posible violation.
5. Marcar dependencias hacia remote/plugins/connectors como sensitive.
```

Comando propuesto:

```powershell
python -m devpilot_core architecture dependencies --json
```

### POST-H-005-D — Hotspot analyzer

Tareas:

```text
1. Calcular score por LOC + fan-in + fan-out + funciones + comandos + criticalidad.
2. Generar top 20 hotspots.
3. Diferenciar hotspot técnico vs core domain.
4. Emitir recomendaciones por hotspot.
```

Comando propuesto:

```powershell
python -m devpilot_core architecture hotspots --json
```

### POST-H-005-E — Ownership validation y reporte

Tareas:

```text
1. Validar ownership registry.
2. Detectar paquetes sin owner.
3. Detectar paquetes críticos sin test contracts asociados.
4. Generar architecture_map.json y .md.
5. Documentar baseline para POST-H-006/007.
```

Comando propuesto:

```powershell
python -m devpilot_core architecture map --write-report --json
```

## 8. Reglas arquitectónicas iniciales

```text
- interfaces/api puede depender de application, no de módulos profundos salvo excepciones documentadas.
- ui/web no debe leer archivos del workspace directamente; debe consumir API/ApplicationService.
- policy no debe depender de interfaces/api ni ui.
- cli_models puede ser dependencia transversal, pero debe mantenerse estable.
- remote/plugins/connectors no deben ser dependencias obligatorias del core local.
- agents pueden depender de policy/modeling/observability/repo/review/refactor, pero no deben activar execution remota.
- quality/industrial pueden agregar señales, pero no deben mutar estado fuente.
```

## 9. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_005_architecture_map.py tests/test_architecture_ownership_registry.py -q
python -m devpilot_core architecture inventory --json
python -m devpilot_core architecture dependencies --json
python -m devpilot_core architecture hotspots --json
python -m devpilot_core architecture map --write-report --json
python -m devpilot_core schema validate --schema-id ArchitectureMap --instance outputs/reports/architecture_map.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Criterios PASS

```text
PASS si se genera architecture_map.json validable por schema.
PASS si se identifica top 20 hotspots.
PASS si todos los paquetes críticos tienen ownership o finding explícito.
PASS si se detectan dependencias prohibidas/restringidas.
PASS si el reporte sirve como entrada objetiva para POST-H-006.
```

## 11. Criterios BLOCK

```text
BLOCK si se ignora cli.py como hotspot.
BLOCK si se omiten policy, schemas, testing, agents o application.
BLOCK si se cambia semántica runtime.
BLOCK si se habilita remote/plugins/connectors.
BLOCK si se usan herramientas externas obligatorias no versionadas.
```

## 12. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Inventario incompleto | Alta | AST + tests con fixtures conocidos. |
| Falsos positivos en imports | Media | Severity warning inicialmente. |
| Bloquear cambios legítimos | Media | No enforcement fuerte hasta baseline aprobado. |
| Aumentar acoplamiento CLI | Media | Comandos architecture mínimos. |
| Reporte no accionable | Alta | Recomendaciones por hotspot y owner. |

## 13. No-go gates

```text
NO-GO si el hito mueve módulos o refactoriza CLI.
NO-GO si se altera ApplicationService.
NO-GO si se habilita enforcement blocking sin baseline revisado.
NO-GO si el mapa omite dominios de seguridad o agentes.
```

## 14. Entregable verificable

```text
architecture_map.json validado por schema.
architecture_map.md legible.
ownership_registry.json inicial.
Top 20 hotspots reproducible.
Tests focales PASS.
Quality gate hardening PASS.
```
