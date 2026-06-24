---
doc_id: "POST-H-002-BACKLOG"
id: "POST-H-002"
title: "POST-H-002 — Maturity dashboard local basado en assessment post-H"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
approval: "internal"
updated: "2026-06-23"
phase: "POST-FASE-H"
priority: "P0"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_runtime_features_added_by_backlog: true
no_remote_execution_enabled: true
---

# POST-H-002 — Maturity dashboard local basado en assessment post-H

## 1. Objetivo

Construir un **dashboard local, read-only y basado en evidencia** que consolide la madurez real de DevPilot después de `POST-H-EVAL-001`, diferenciando capacidades `production-ready-local`, `implemented`, `implemented-initial`, `experimental`, `planned` y `blocked`.

El objetivo no es crear una UI decorativa, sino convertir los artefactos post-H en una señal operativa para decidir qué se puede desarrollar, qué debe bloquearse y qué requiere hardening antes de declarar DevPilot como plataforma productiva local.

## 2. Contexto y justificación

`POST-H-EVAL-001` generó una línea base de madurez mediante assessment, matriz de decisión, mapa arquitectónico, risk register, evaluación de testing/costos, roadmap priorizado, manifest y closure report. Actualmente esa información existe, pero está distribuida en varios documentos y JSON. El operador necesita una vista única para responder:

```text
¿Qué capacidades están maduras?
¿Qué capacidades son solo initial/stub/planned?
¿Qué riesgos siguen abiertos?
¿Qué pruebas protegen cada dominio?
¿Qué hitos del roadmap desbloquean cada brecha?
¿DevPilot puede avanzar sin activar capacidades sensibles?
```

## 3. Alcance

Incluye:

```text
- Modelo local de madurez por dominio/capacidad.
- Lector determinístico de artefactos POST-H-EVAL-001.
- Comando CLI read-only para generar dashboard en JSON y Markdown.
- Reporte local en outputs/reports.
- Tests de contrato del dashboard.
- Integración inicial con quality-gate/industrial-readiness solo como fuente, no como reemplazo.
```

No incluye:

```text
- Web UI productiva nueva.
- API pública nueva.
- Remote execution.
- Conectores write.
- Plugins ejecutables.
- Activación de APIs externas.
- Declaración production-ready-local.
```

## 4. Fuentes de entrada obligatorias

```text
docs/audits/post_h_eval_001_baseline_assessment.md
docs/post_h_eval_001_manifest.json
.devpilot/evals/post_h_eval_001_decision_matrix.json
docs/02_architecture/post_h_current_architecture_map.md
docs/03_security/post_h_security_risk_register.md
.devpilot/evals/post_h_eval_001_security_risk_register.json
docs/04_quality/post_h_test_cost_assessment.md
.devpilot/evals/post_h_eval_001_test_cost_assessment.json
docs/backlogs/post_h_prioritized_roadmap.md
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
docs/audits/post_h_eval_001_closure_report.md
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
src/devpilot_core/maturity/models.py
src/devpilot_core/maturity/sources.py
src/devpilot_core/maturity/dashboard.py
src/devpilot_core/maturity/__init__.py
docs/schemas/maturity_dashboard.schema.json
docs/schemas/schema_catalog.json                    # registrar schema nuevo
outputs/reports/maturity_dashboard.json             # generado por comando, no versionar
outputs/reports/maturity_dashboard.md               # generado por comando, no versionar
tests/test_post_h_002_maturity_dashboard.py
```

Opcional, si no aumenta acoplamiento del CLI:

```text
src/devpilot_core/application/maturity_service.py
```

## 6. Modelo de datos mínimo

El dashboard debe representar al menos:

```json
{
  "schema_version": "1.0",
  "dashboard_id": "POST-H-002-MATURITY-DASHBOARD",
  "generated_at_utc": "...",
  "source_revision": {
    "roadmap_version": "1.1.0",
    "post_h_eval_status": "closed"
  },
  "summary": {
    "capabilities_total": 0,
    "production_ready_local_total": 0,
    "implemented_total": 0,
    "implemented_initial_total": 0,
    "experimental_total": 0,
    "planned_total": 0,
    "blocked_total": 0,
    "critical_risks_total": 0,
    "blocking_gaps_total": 0
  },
  "capabilities": [
    {
      "capability_id": "policy-engine",
      "name": "PolicyEngine",
      "domain": "governance",
      "status": "implemented",
      "maturity": "alta-local",
      "test_coverage": "alta",
      "risk": "medio",
      "source_evidence": ["..."],
      "roadmap_dependency": null,
      "no_go_gate": false
    }
  ],
  "roadmap_alignment": [
    {
      "milestone": "POST-H-003",
      "unblocks": ["test-contract-registry-2"],
      "priority": "P0"
    }
  ],
  "safety": {
    "remote_execution_enabled": false,
    "connector_write_enabled": false,
    "plugin_execution_enabled": false,
    "external_apis_enabled_by_default": false
  }
}
```

## 7. Micro-sprints propuestos

### POST-H-002-A — Modelo de madurez y schema

Objetivo: definir modelo de dominio `maturity` y schema JSON.

Tareas:

```text
1. Crear dataclasses/enums: CapabilityStatus, MaturityLevel, TestCoverageLevel, RiskLevel.
2. Crear MaturityCapability, MaturityDashboard, RoadmapDependency, SafetySignal.
3. Crear docs/schemas/maturity_dashboard.schema.json.
4. Registrar schema en docs/schemas/schema_catalog.json.
5. Agregar tests de schema registry.
```

Criterios PASS:

```text
PASS si el schema valida una instancia mínima.
PASS si todos los estados permitidos están enumerados.
PASS si se diferencia production-ready-local de production-ready completo.
```

Criterios BLOCK:

```text
BLOCK si se permite declarar production-ready completo.
BLOCK si se omite estado blocked/stub/planned.
```

Validación:

```powershell
python -m pytest tests/test_schema_registry.py tests/test_post_h_002_maturity_dashboard.py -q
```

### POST-H-002-B — Lectores de fuentes post-H

Objetivo: extraer señales de madurez desde artefactos existentes sin inferencias frágiles.

Tareas:

```text
1. Implementar source readers para manifest, decision matrix, risk register JSON, test cost JSON, roadmap JSON y test_contract_registry.
2. Implementar fallback controlado para documentos Markdown con búsqueda de secciones canónicas.
3. Reportar missing sources como finding warning o block según criticidad.
4. No modificar fuentes.
```

Criterios PASS:

```text
PASS si todas las fuentes obligatorias se detectan.
PASS si fuentes ausentes críticas producen BLOCK.
PASS si fuentes opcionales producen WARNING.
```

Criterios BLOCK:

```text
BLOCK si el dashboard inventa madurez sin evidencia.
BLOCK si ignora manifest o roadmap JSON.
```

### POST-H-002-C — Generador de dashboard local

Objetivo: producir dashboard JSON/Markdown read-only.

Tareas:

```text
1. Implementar MaturityDashboardBuilder.
2. Calcular summary global.
3. Listar capacidades y dominios.
4. Mapear riesgos críticos a roadmap.
5. Generar salida JSON serializable.
6. Generar reporte Markdown legible.
```

Criterios PASS:

```text
PASS si genera JSON conforme al schema.
PASS si el Markdown diferencia madurez, riesgo y cobertura.
PASS si remote/connectors/plugins permanecen blocked cuando aplique.
```

### POST-H-002-D — CLI e integración ApplicationService

Objetivo: exponer la capacidad sin contaminar `cli.py` más de lo necesario.

Comando propuesto:

```powershell
python -m devpilot_core maturity dashboard --json
python -m devpilot_core maturity dashboard --write-report --json
```

Tareas:

```text
1. Agregar handler mínimo CLI.
2. Si procede, crear MaturityApplicationService.
3. Usar CommandResult.
4. Soportar --write-report.
5. Registrar eventos/trazas existentes sin crear persistencia nueva obligatoria.
```

Criterios PASS:

```text
PASS si el comando devuelve exit_code 0 en baseline válido.
PASS si --write-report escribe outputs/reports/maturity_dashboard.{json,md}.
PASS si no escribe fuera de outputs/reports.
```

### POST-H-002-E — Quality gate y documentación

Objetivo: conectar dashboard con gates sin reemplazar gates existentes.

Tareas:

```text
1. Agregar prueba documental POST-H-002.
2. Agregar contract en Test Contract Registry v1 si corresponde.
3. Documentar uso en runbook.
4. Documentar limitaciones: no producción completa, no remote.
```

Criterios PASS:

```text
PASS si pytest focal pasa.
PASS si test-contracts validate pasa.
PASS si quality-gate hardening sigue PASS.
```

## 8. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_002_maturity_dashboard.py -q
python -m pytest tests/test_schema_registry.py tests/test_test_contract_registry.py -q
python -m devpilot_core schema validate --schema-id MaturityDashboard --instance outputs/reports/maturity_dashboard.json --json
python -m devpilot_core maturity dashboard --write-report --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 9. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Dashboard ornamental sin evidencia | Alta | Exigir source_evidence por capacidad. |
| Sobreclaim production-ready | Alta | Usar solo `production-ready-local` cuando aplique. |
| Duplicar industrial-readiness | Media | Consumir señales; no reemplazar gate. |
| Aumentar monolito CLI | Media-alta | Handler mínimo y service separado. |
| Drift con roadmap | Media | Consumir roadmap JSON 1.1.0. |

## 10. No-go gates

```text
NO-GO si se habilita remote execution.
NO-GO si se habilita connector write.
NO-GO si se habilita plugin execution.
NO-GO si se declara production-ready completo.
NO-GO si se usan APIs externas.
NO-GO si se generan mutaciones fuera de outputs/reports.
```

## 11. Entregable verificable

```text
Comando maturity dashboard ejecutable localmente.
Reporte JSON validable por schema.
Reporte Markdown legible para operador.
Tests focales PASS.
Quality gate hardening PASS.
```


## 12. Avance de implementación

### POST-H-002-A — Modelo de madurez y schema

Estado: `implemented-initial`.

Este micro-sprint aprueba el backlog `POST-H-002` para ejecución y entrega la primera base técnica del dashboard de madurez: vocabulario controlado de estados, niveles de madurez, cobertura de pruebas y riesgo; modelo de capacidades, dependencias de roadmap y señales de seguridad; schema JSON `MaturityDashboard`; registro del schema en el catálogo local; y pruebas focales de contrato.

Alcance explícito: esta entrega **no** implementa todavía lectores de fuentes post-H, generador del dashboard, comando CLI `maturity dashboard`, integración ApplicationService ni escritura de reportes. Es una versión preliminar de modelo/schema que prepara los micro-sprints `POST-H-002-B` a `POST-H-002-E`.

No-go gates conservados: no se habilita remote execution, connector write, plugin execution, external APIs, networking, mutaciones fuera de documentos/schemas/tests ni declaración `production-ready` completa. El modelo solo permite el estado `production-ready-local`, sujeto al gate final `POST-H-025`.
