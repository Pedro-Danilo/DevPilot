---
title: "POST-H-002-C — Generador de dashboard local"
doc_id: "POST-H-002-C-AUDIT"
status: "approved"
approval: "internal"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
local_first: true
dry_run: true
---

# POST-H-002-C — Generador de dashboard local

## Propósito

`POST-H-002-C` implementa el builder local del dashboard de madurez. La capacidad convierte las fuentes leídas por `POST-H-002-B` en un `MaturityDashboard` validable por schema y en un reporte Markdown legible para operador.

El objetivo es evitar un dashboard ornamental: cada capacidad se deriva de la matriz de decisión post-H, el risk register, el roadmap priorizado y el Test Contract Registry. El builder no inventa madurez sin evidencia.

## Estado

Estado del micro-sprint: `implemented-initial`.

El builder queda disponible como módulo Python para pruebas y para el futuro comando CLI `maturity dashboard`, pero todavía no se expone por CLI ni escribe archivos persistidos.

## Alcance implementado

Se implementó:

```text
src/devpilot_core/maturity/dashboard.py
MaturityDashboardBuilder
DashboardBuildResult
render_maturity_dashboard_markdown()
validación in-memory contra schema MaturityDashboard
mapeo de dominios de decision matrix a MaturityCapability
mapeo de riesgos SEC-001/SEC-002/SEC-003 a capacidades no-go blocked
mapeo de roadmap POST-H a RoadmapDependency
render Markdown operador en memoria
```

No se implementó todavía:

```text
comando CLI maturity dashboard
--write-report
outputs/reports/maturity_dashboard.json
outputs/reports/maturity_dashboard.md
MaturityApplicationService
UI/API
quality-gate específico de maturity dashboard
```

Esas tareas corresponden a `POST-H-002-D` y `POST-H-002-E`.

## Funcionamiento

El flujo técnico es:

```text
PostHSourceReader
→ PostHSourceBundle
→ MaturityDashboardBuilder
→ MaturityDashboard
→ SchemaValidator(MaturityDashboard)
→ Markdown operator report in-memory
→ DashboardBuildResult / CommandResult compatible
```

El builder lee únicamente artefactos existentes dentro del workspace. No usa red, no usa APIs externas y no muta fuentes. El reporte Markdown se retorna en memoria para que el CLI futuro pueda decidir si lo escribe en `outputs/reports`.

## Integración dentro de DevPilot

`POST-H-002-C` se integra con:

```text
src/devpilot_core/maturity/models.py
src/devpilot_core/maturity/sources.py
docs/schemas/maturity_dashboard.schema.json
src/devpilot_core/schemas/SchemaValidator
tests/test_post_h_002_maturity_dashboard.py
```

El builder conserva la frontera de `POST-H-002-D`: no modifica `src/devpilot_core/cli.py` ni `src/devpilot_core/application/` en este micro-sprint.

## Criterios PASS

```text
PASS si el builder genera un MaturityDashboard conforme al schema.
PASS si el dashboard lista capacidades y dominios desde decision matrix.
PASS si el Markdown diferencia madurez, riesgo, cobertura y roadmap.
PASS si remote execution, connector write y plugin execution quedan como no-go/blocked cuando aplica.
PASS si la salida declara network_used=false, external_api_used=false y mutations_performed=false.
```

## Criterios BLOCK

```text
BLOCK si se declara production-ready completo.
BLOCK si se habilita remote execution.
BLOCK si se habilita connector write.
BLOCK si se habilita plugin execution.
BLOCK si el builder escribe reportes persistidos antes del micro-sprint CLI.
BLOCK si el dashboard ignora manifest, decision matrix, risk register o roadmap JSON.
```

## Riesgos y limitaciones

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Sobreinterpretar el builder como dashboard operativo final | Media | Documentar que CLI/report writing quedan para POST-H-002-D. |
| Madurez derivada de evidencia imperfecta | Media | Mantener metadata y source_evidence por capacidad. |
| Duplicar industrial-readiness | Media | El builder consume señales, no reemplaza gates existentes. |
| Aumentar acoplamiento CLI antes de tiempo | Media | No se modifica CLI en este micro-sprint. |

## Comandos de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_002_maturity_dashboard.py -q
python -m pytest tests/test_schema_registry.py tests/test_post_h_002_maturity_dashboard.py -q
python -m devpilot_core validate-frontmatter docs/audits/post_h_002_c_dashboard_builder_report.md --json
python -m devpilot_core validate-artifact docs/audits/post_h_002_c_dashboard_builder_report.md --json
python -m devpilot_core validate docs --json
python -m devpilot_core project-state validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
No remote execution.
No connector write.
No plugin execution.
No external APIs.
No network.
No report persistence until POST-H-002-D.
No production-ready completo.
```

## Próximo paso

El siguiente micro-sprint es `POST-H-002-D — CLI e integración ApplicationService`, donde se deberá exponer el builder mediante comando CLI mínimo y permitir escritura controlada bajo `outputs/reports`.
