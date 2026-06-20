---
title: "POST-H-001 — Industrial hardening de tests y contratos"
doc_id: "DEVPL-POST-H-001-INDUSTRIAL-HARDENING"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-FASE-H"
source_repo: "repo_DevPilot_Local_130.zip"
source_phase_closure: "docs/audits/phase_h_advanced_capabilities_closure.md"
created: "2026-06-19"
updated: "2026-06-19"
classification: "hardening-before-new-features"
approval: "approved_by_owner"
implementation_status: "implemented-initial"
---

# POST-H-001 — Industrial hardening de tests y contratos

## Propósito

Este documento define el sprint post-H orientado a endurecer pruebas, contratos y gates antes de nuevas funcionalidades.

## 1. Estado propuesto

`POST-H-001` se propone como el primer sprint posterior al cierre de Fase H. Su estado inicial es `draft-for-review` porque no implementa una nueva capacidad funcional de usuario final; propone una intervención de endurecimiento industrial sobre pruebas, contratos y gates.

La prioridad es alta porque Fase H cerró con 863 pruebas en PASS, múltiples gates, documentación histórica acumulada y varios contratos nuevos. Ese crecimiento es positivo, pero aumenta el costo de detección cuando una desincronización documental o contractual rompe la suite completa.

## 2. Objetivo

Reducir el costo de validación, disminuir fragilidad en pruebas históricas y endurecer contratos sin frenar la evolución del producto.

En términos operativos, el sprint debe convertir la suite actual en una estructura más mantenible, con capas claras:

1. pruebas rápidas de contrato;
2. pruebas focales por sprint o feature;
3. pruebas documentales de estado global;
4. pruebas históricas inmutables;
5. gates agregados para CI/local;
6. reportes de impacto para saber qué validar ante cada cambio.

## 3. Problema que resuelve

Durante los últimos sprints se observó un patrón recurrente: un cambio correcto en el estado global del proyecto puede romper múltiples pruebas históricas porque esas pruebas mezclan dos responsabilidades distintas:

- verificar que el sprint original creó sus artefactos;
- verificar que README, backlog, changelog o runbook tengan el último hito global vigente.

Eso genera deuda de pruebas. Un test de Sprint 85, por ejemplo, no debería fallar cada vez que el último hito avanza de Sprint 96 a 97, 98, 99 o POST-H. Debe validar el contrato histórico del Sprint 85 y delegar el estado global a un test único de sincronización global.

## 4. Principios de diseño

### 4.1 Separar contrato histórico de estado global

Cada sprint histórico debe conservar pruebas que validen:

- archivos creados por ese sprint;
- contratos propios del sprint;
- manifest del sprint;
- auditoría del sprint;
- invariantes de seguridad propias.

Pero no debe validar directamente:

- último hito global del README;
- `next_sprint` global;
- rango global del changelog;
- source repo global;
- cierre de fase actual.

Eso debe centralizarse en una suite única de `project_state` o `global_sync`.

### 4.2 Tests baratos primero

La validación debe ejecutarse en capas:

```text
fast-contracts      -> segundos
feature-focused     -> segundos/minutos
historical-docs     -> minutos
quality-gate ci     -> minutos
full pytest         -> cierre definitivo
```

### 4.3 No debilitar gates

Endurecer no significa borrar pruebas. Significa ubicar cada prueba en el nivel correcto y hacer que los mensajes de fallo indiquen el contrato exacto roto.

### 4.4 No ocultar warnings importantes

Los warnings de secciones recomendadas faltantes deben seguir visibles, pero no deben bloquear si el perfil los clasifica como recomendados. El sprint debe diferenciar `warning`, `blocker`, `regression`, `contract drift` y `documentation drift`.

## 5. Alcance funcional

### Incluye

- Inventario de tests por categoría.
- Clasificación de pruebas por capa de validación.
- Creación de un registry local de contratos de test.
- Desacoplamiento de pruebas históricas frente a estado global mutable.
- Comando de impacto para sugerir qué suites ejecutar según archivos modificados.
- Reporte de deuda de contratos y pruebas.
- Perfil `quality-gate hardening` o equivalente.
- Documentación operativa y criterios PASS/BLOCK.

### No incluye

- Nuevas funcionalidades agentic.
- Remote runners reales.
- Cloud/CI remoto obligatorio.
- Reescritura completa de la suite.
- Eliminación masiva de pruebas.
- Dependencias externas pesadas.

## 6. Diseño propuesto

## 6.1 Test Contract Registry

Crear un registry declarativo, por ejemplo:

```text
.devpilot/testing/test_contract_registry.json
```

Contenido esperado:

```json
{
  "schema_version": "1.0",
  "contracts": [
    {
      "contract_id": "sprint-85-documentation",
      "scope": "historical-sprint",
      "owner": "FUNC-SPRINT-85",
      "test_files": ["tests/test_sprint_85_documentation.py"],
      "mutable_global_state_allowed": false,
      "global_state_source": null,
      "critical": true
    },
    {
      "contract_id": "project-global-state",
      "scope": "global-state",
      "test_files": ["tests/test_project_global_state.py"],
      "validates": ["README.md", "runbook.md", "backlogs", "CHANGELOG.md"],
      "critical": true
    }
  ]
}
```

El objetivo no es ejecutar dinámicamente tests desde JSON, sino documentar y validar la intención de cada suite.

## 6.2 Schema de registry

Crear:

```text
docs/schemas/test_contract_registry.schema.json
```

El schema debe validar:

- `contract_id` único;
- `scope` permitido: `unit`, `feature`, `historical-sprint`, `global-state`, `integration`, `quality-gate`, `safety`, `ui-smoke`;
- rutas de test existentes;
- criticidad;
- fase/sprint asociado;
- si depende o no de estado global mutable.

## 6.3 Project State Contract

Crear un contrato centralizado, por ejemplo:

```text
.devpilot/project_state.json
```

o, si se prefiere no agregar otro archivo runtime/config, derivarlo desde README/backlog/manifest más reciente.

Campos recomendados:

```json
{
  "current_phase": "POST-FASE-H",
  "last_completed_sprint": "FUNC-SPRINT-99",
  "next_sprint": "POST-H-001",
  "phase_h_status": "closed_implemented_initial",
  "industrial_baseline_ready": true,
  "maturity_level": "industrial-baseline-ready"
}
```

La regla clave: solo las pruebas de estado global validan estos campos. Las pruebas históricas no los duplican.

## 6.4 Test Impact Analyzer

Crear un módulo liviano:

```text
src/devpilot_core/testing/impact.py
```

CLI propuesto:

```powershell
python -m devpilot_core test-impact analyze --changed-files changed_files.txt --json
```

o:

```powershell
python -m devpilot_core test-impact analyze --since HEAD~1 --json
```

Si no se desea depender de Git, la primera versión puede aceptar una lista de rutas. Resultado esperado:

```json
{
  "ok": true,
  "recommended_suites": [
    "tests/test_schema_registry.py",
    "tests/test_project_global_state.py",
    "tests/test_sprint_99_documentation.py"
  ],
  "reasoning": [
    {
      "path": "docs/schemas/schema_catalog.json",
      "matched_contracts": ["schema-registry"]
    }
  ],
  "full_pytest_required": true
}
```

Debe ser conservador: si no puede determinar impacto, recomienda `pytest -q`.

## 6.5 Perfiles de validación

Agregar perfiles explícitos:

```text
fast-contracts
feature-focused
historical-docs
global-sync
hardening
full-local
```

Pueden exponerse como comandos del `quality-gate` o como documentación inicial si no se quiere ampliar CLI todavía.

Ejemplo:

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
```

El perfil `hardening` debería ejecutar:

- schema registry;
- MIASI structural validation;
- test contract registry validation;
- project global state validation;
- industrial readiness check;
- no full pytest por defecto, salvo `--include-pytest`.

## 6.6 Refactor de tests documentales históricos

Patrón actual problemático:

```python
assert "Último hito: `FUNC-SPRINT-99" in readme
```

dentro de tests de sprints históricos.

Patrón recomendado:

```python
assert "FUNC-SPRINT-85" in audit
assert "docs/functional_sprint_85_manifest.json" in changelog
assert Path("docs/functional_sprint_85_manifest.json").exists()
```

El último hito global debe validarse en:

```text
tests/test_project_global_state.py
```

## 7. Historias de usuario

| ID | Historia | Criterio de aceptación |
|---|---|---|
| POST-H-001-US-001 | Como maintainer, quiero clasificar tests por contrato para saber qué valida cada archivo. | Existe `test_contract_registry.json` validado por schema. |
| POST-H-001-US-002 | Como maintainer, quiero desacoplar tests históricos del último hito global. | Tests históricos no fallan por `next_sprint` global. |
| POST-H-001-US-003 | Como reviewer, quiero un gate de hardening rápido. | Existe `quality-gate hardening` o perfil equivalente. |
| POST-H-001-US-004 | Como developer, quiero saber qué pruebas ejecutar ante cambios concretos. | Existe `test-impact analyze` o reporte equivalente. |
| POST-H-001-US-005 | Como auditor, quiero distinguir warning documental de bloqueo contractual. | Reporte clasifica severity y origen. |

## 8. Tareas propuestas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| POST-H-001-T001 | Inventario de tests | `docs/audits/test_contract_inventory.md` | Lista completa por capa. |
| POST-H-001-T002 | Registry de contratos | `.devpilot/testing/test_contract_registry.json` | Schema PASS. |
| POST-H-001-T003 | Schema del registry | `docs/schemas/test_contract_registry.schema.json` | `schema validate` PASS. |
| POST-H-001-T004 | Global state test | `tests/test_project_global_state.py` | Centraliza último hito. |
| POST-H-001-T005 | Refactor histórico mínimo | Tests sprint 85–99 desacoplados de estado global mutable | PASS focal. |
| POST-H-001-T006 | Impact analyzer MVP | `src/devpilot_core/testing/impact.py` | Recomendaciones conservadoras. |
| POST-H-001-T007 | Quality gate hardening | Perfil o comando documentado | PASS. |
| POST-H-001-T008 | Auditoría | `docs/audits/post_h_001_test_contract_hardening_audit.md` | Validada. |
| POST-H-001-T009 | Manifest | `docs/post_h_001_manifest.json` o equivalente | Schema PASS. |

## 9. Archivos previstos

```text
src/devpilot_core/testing/__init__.py
src/devpilot_core/testing/contracts.py
src/devpilot_core/testing/impact.py
.devpilot/testing/test_contract_registry.json
docs/schemas/test_contract_registry.schema.json
docs/audits/test_contract_inventory.md
docs/audits/post_h_001_test_contract_hardening_audit.md
docs/post_h_001_manifest.json
tests/test_test_contract_registry.py
tests/test_test_impact.py
tests/test_project_global_state.py
```

Archivos probablemente modificados:

```text
src/devpilot_core/cli.py
src/devpilot_core/quality/gate.py
tests/test_sprint_85_documentation.py ... tests/test_sprint_99_documentation.py
README.md
docs/05_operations/runbook.md
docs/backlogs/post_phase_h_ideas.md
docs/release/CHANGELOG.md
docs/schemas/schema_catalog.json
```

## 10. Comandos objetivo

```powershell
python -m devpilot_core schema validate --schema docs\schemas\test_contract_registry.schema.json --instance .devpilot\testing\test_contract_registry.json --json
python -m devpilot_core test-impact analyze --changed-files changed_files.txt --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m pytest tests\test_test_contract_registry.py tests\test_test_impact.py tests\test_project_global_state.py -q
python -m pytest tests\test_sprint_*_documentation.py -q
pytest -q
```

## 11. Criterios PASS

- `pytest -q` sigue en PASS.
- Registry de contratos de test valida por schema.
- Existe una prueba única de estado global del proyecto.
- Tests históricos no duplican `last_completed_sprint`/`next_sprint` global.
- `quality-gate hardening` pasa sin ejecutar full pytest por defecto.
- `test-impact analyze` recomienda suites de manera conservadora.
- No se eliminan pruebas críticas para ocultar fallos.
- README, runbook, changelog y backlog post-H quedan sincronizados.

## 12. Criterios BLOCK

- Se borran pruebas históricas sin reemplazo equivalente.
- El impact analyzer dice que no hay que correr pruebas cuando hay cambios en contratos críticos.
- Se ocultan warnings o blockers relevantes.
- Las pruebas globales quedan duplicadas en múltiples sprints históricos.
- `pytest -q` falla.
- `quality-gate hardening` falla.
- No hay manifest ni auditoría del sprint.

## 13. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---:|---|
| Refactor de pruebas introduce falsos negativos | Alto | Cambios pequeños, fixture controlada, full pytest obligatorio al cierre. |
| Se interpreta hardening como reducción de cobertura | Alto | Mantener o aumentar cobertura; mover responsabilidades, no borrar garantías. |
| Impact analyzer demasiado optimista | Alto | Modo conservador: ante duda recomienda full pytest. |
| Exceso de nuevos contratos | Medio | Registry mínimo, schema simple, sin metaprogramación de pytest. |
| Más complejidad CLI | Medio | Preferir módulo pequeño y subcomando simple. |

## 14. Plan de ejecución sugerido

### Paso 1 — Auditoría sin modificar tests

Generar inventario de pruebas y mapear qué validan.

### Paso 2 — Crear registry y schema

Agregar contrato declarativo para clasificar suites.

### Paso 3 — Centralizar estado global

Crear `tests/test_project_global_state.py`.

### Paso 4 — Refactor mínimo de tests históricos

Eliminar de tests históricos las expectativas mutables globales y conservar expectativas propias del sprint.

### Paso 5 — Agregar impact analyzer MVP

Implementar recomendación conservadora de pruebas por rutas modificadas.

### Paso 6 — Integrar quality gate hardening

Agregar perfil `hardening` y documentarlo.

### Paso 7 — Cierre documental

Actualizar README, runbook, changelog, backlog post-H, auditoría y manifest.

## 15. Acciones posteriores a POST-H-001

Después de este sprint, las acciones recomendadas son:

1. `POST-H-002 — Maturity dashboard local`: visualizar madurez por capacidad usando el industrial readiness report.
2. `POST-H-003 — Policy/MIASI semantic validator ampliado`: verificar consistencia semántica agent-tool-policy, no solo schema.
3. `POST-H-004 — Observability retention local`: rotación, retención y consulta de reportes/trazas.
4. `POST-H-005 — RAG groundedness evals`: evaluar calidad de citas, fuentes y respuestas sin evidencia.
5. `POST-H-006 — UI/API industrial shell`: fortalecer experiencia local sin romper ApplicationService ni PolicyEngine.

## 16. Veredicto recomendado

Sí conviene implementar `POST-H-001` antes de nuevas funcionalidades.

La razón técnica es simple: DevPilot ya tiene suficientes capacidades y suficientes pruebas como para que el riesgo principal no sea falta de features, sino fragilidad de validación, contratos duplicados y costo de diagnóstico. Endurecer la suite ahora reduce regresiones futuras y mejora la velocidad de implementación posterior.


## 17. Implementación POST-H-001

Estado de implementación: `implemented-initial`.

La implementación crea un contrato explícito para la suite de pruebas, centraliza el estado global mutable del proyecto y agrega un analizador conservador de impacto de pruebas. Este sprint no elimina cobertura: mueve responsabilidades a capas más precisas y conserva `pytest -q` como validación definitiva de cierre.

Artefactos implementados:

- `.devpilot/testing/test_contract_registry.json`
- `.devpilot/project_state.json`
- `docs/schemas/test_contract_registry.schema.json`
- `docs/schemas/project_state.schema.json`
- `docs/schemas/post_h_manifest.schema.json`
- `src/devpilot_core/testing/contracts.py`
- `src/devpilot_core/testing/impact.py`
- `tests/test_project_global_state.py`
- `tests/test_test_contract_registry.py`
- `tests/test_test_impact.py`
- `docs/audits/test_contract_inventory.md`
- `docs/audits/post_h_001_test_contract_hardening_audit.md`
- `docs/post_h_001_manifest.json`

El alcance es una primera versión industrial de hardening: no reemplaza `pytest`, no ejecuta tests dinámicamente desde JSON y no introduce dependencias externas.
