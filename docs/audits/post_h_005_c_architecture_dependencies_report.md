---
title: "POST-H-005-C — Architecture dependencies and boundaries report"
doc_id: "POST-H-005-C-AUDIT"
version: "1.0.0"
status: "approved"
approval: "internal"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
sprint: "POST-H-005-C"
local_first: true
dry_run: true
---

# POST-H-005-C — Grafo de dependencias y boundaries

## Propósito

Implementar una primera versión ejecutable del grafo de dependencias arquitectónicas de DevPilot a partir de imports Python internos bajo `src/devpilot_core`, sin ejecutar código del proyecto ni modificar fuentes.

## Estado

`implemented-initial / advisory dependency graph`.

## Alcance implementado

```text
- Builder `ArchitectureDependenciesBuilder`.
- CLI `python -m devpilot_core architecture dependencies --json`.
- Parseo AST local y read-only de imports internos `devpilot_core`.
- Materialización de `DependencyEdge` a nivel paquete.
- Cálculo de `direct_dependencies`, `fan_in` y `fan_out` por paquete.
- Clasificación advisory de policy: allow, restricted, forbidden, unknown.
- Marcado sensible para dependencias hacia/desde remote, plugins y connectors.
- Validación del payload contra `SCHEMA-DEVPL-ARCHITECTURE-MAP-V1`.
```

## Fuera de alcance explícito

```text
- No refactoriza CLI ni mueve módulos.
- No modifica ApplicationService ni boundaries runtime.
- No ejecuta tests desde el grafo.
- No convierte warnings en blockers de quality-gate.
- No calcula hotspot score; queda para POST-H-005-D.
- No genera `architecture_map.json/.md` final; queda para POST-H-005-E.
```

## Funcionamiento técnico

El builder ejecuta primero el inventario AST de `POST-H-005-B` para reutilizar el contrato `ArchitectureMap`. Después vuelve a parsear imports con resolución relativa más precisa y construye edges paquete→paquete. Cada edge incluye metadata de módulos fuente, módulos destino, imports de muestra, conteo de imports y razón de clasificación.

La clasificación combina el ownership registry con reglas base:

```text
- `forbidden_dependencies` del owner fuente producen policy=forbidden.
- `restricted_dependencies` producen policy=restricted.
- `allowed_dependencies` producen policy=allow.
- `interfaces` debe preferir `application` sobre deep core.
- `core -> interfaces` se marca como posible violation.
- remote/plugins/connectors se marcan como sensitive.
```

## Criterios PASS

```text
PASS si `architecture dependencies --json` devuelve ok=true.
PASS si `dependencies_total` y `package_edges_total` son mayores que cero.
PASS si fan-in/fan-out por paquete se materializa.
PASS si existen edges sensibles hacia remote/plugins/connectors cuando correspondan.
PASS si el payload valida contra `ArchitectureMap`.
PASS si safety conserva dry_run=true y network/API/mutations=false.
```

## Criterios BLOCK

```text
BLOCK si el comando importa módulos del proyecto dinámicamente.
BLOCK si ejecuta pruebas, subprocesses, red o APIs externas.
BLOCK si muta fuentes o cambia boundaries runtime.
BLOCK si no valida el payload contra el schema ArchitectureMap.
```

## Riesgos y limitaciones

```text
- El grafo es estático; no detecta importlib dinámico ni dependencias runtime.
- La resolución de imports se enfoca en dependencias internas Python, no UI web ni assets.
- Las violations son advisory warnings; enforcement queda diferido.
- La granularidad principal es paquete→paquete, no call graph ni clase→clase.
```

## Comandos de validación

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_architecture_dependencies.py tests/test_architecture_inventory.py tests/test_post_h_005_architecture_map.py tests/test_architecture_ownership_registry.py tests/test_schema_registry.py -q
python -m devpilot_core architecture dependencies --json
python -m devpilot_core validate docs --json
python -m devpilot_core project-state validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```
