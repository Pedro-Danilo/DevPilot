---
title: "POST-H-002-D — CLI e integración ApplicationService"
doc_id: "POST-H-002-D-AUDIT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
approval: "internal"
updated: "2026-06-24"
---

# POST-H-002-D — CLI e integración ApplicationService

## Propósito

Exponer el dashboard local de madurez de `POST-H-002-C` mediante una frontera estable de aplicación y un comando CLI operativo. La implementación permite al operador generar el dashboard en JSON y, con confirmación explícita mediante `--write-report`, persistir los reportes canónicos bajo `outputs/reports`.

## Estado

Estado: `implemented-initial`.

Esta entrega habilita operación local por CLI y `ApplicationService`, pero no cierra todavía el hito `POST-H-002`. El quality gate específico, documentación consolidada de cierre y estrategia de regresión completa quedan para `POST-H-002-E`.

## Alcance implementado

```text
src/devpilot_core/application/maturity_service.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
src/devpilot_core/cli.py
src/devpilot_core/maturity/dashboard.py
tests/test_post_h_002_maturity_dashboard.py
```

La operación expuesta es:

```text
maturity.dashboard
```

El comando CLI agregado es:

```powershell
python -m devpilot_core maturity dashboard --json
python -m devpilot_core maturity dashboard --json --write-report
```

## Funcionamiento

El flujo operativo es:

```text
CLI maturity dashboard
→ ApplicationService.maturity_dashboard()
→ MaturityApplicationService.dashboard()
→ MaturityDashboardBuilder.build()
→ MaturityDashboard schema-backed payload
→ CommandResult
→ optional outputs/reports/maturity_dashboard.json + .md with --write-report
```

Sin `--write-report`, la operación es read-only y no persiste artefactos. Con `--write-report`, la escritura queda limitada a:

```text
outputs/reports/maturity_dashboard.json
outputs/reports/maturity_dashboard.md
```

## Integración dentro de DevPilot

`MaturityApplicationService` evita que el CLI importe directamente detalles de lectura de fuentes o renderizado del dashboard. Esto respeta la frontera `ApplicationService` y prepara un futuro consumo por API/UI sin duplicar lógica de core.

El contrato de aplicación registra el dominio `maturity` como `implemented-initial` y la capacidad `maturity.dashboard` como operación con side effect explícito solo cuando el adaptador solicita escritura de reportes.

## Criterios PASS

```text
PASS si maturity dashboard --json retorna CommandResult ok=true.
PASS si ApplicationService expone maturity_dashboard().
PASS si --write-report genera maturity_dashboard.json y maturity_dashboard.md bajo outputs/reports.
PASS si el dashboard mantiene remote_execution_enabled=false.
PASS si el dashboard mantiene connector_write_enabled=false.
PASS si el dashboard mantiene plugin_execution_enabled=false.
PASS si el dashboard mantiene external_apis_enabled_by_default=false.
PASS si las pruebas focales del micro-sprint pasan.
PASS si validate docs, project-state, test-contracts y quality-gate hardening no tienen findings bloqueantes.
```

## Criterios BLOCK

```text
BLOCK si se escribe fuera de outputs/reports.
BLOCK si el CLI habilita red, APIs externas o proveedores remotos.
BLOCK si se habilita remote execution, connector write o plugin execution.
BLOCK si se declara production-ready completo, enterprise-ready, remote-ready o compliance-certified.
BLOCK si el CLI salta ApplicationService y acopla directamente la interfaz con detalles internos del builder.
```

## Riesgos y limitaciones

El principal riesgo es sobreinterpretar el dashboard CLI como declaración productiva. Esta entrega solo expone y persiste el dashboard local como señal operativa. No reemplaza `industrial-readiness`, no habilita UI/API, no ejecuta red y no cierra el hito completo.

Limitaciones esperadas:

```text
No hay route HTTP nueva.
No hay Web UI nueva.
No hay quality gate específico de maturity dashboard.
No hay declaración production-ready-local.
No hay regresión completa pytest -q hasta cierre de POST-H-002-E.
```

## Comandos de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_002_maturity_dashboard.py -q
python -m pytest tests/test_schema_registry.py tests/test_application_services.py tests/test_post_h_002_maturity_dashboard.py -q
python -m devpilot_core maturity dashboard --json
python -m devpilot_core maturity dashboard --json --write-report
python -m devpilot_core validate-frontmatter docs/audits/post_h_002_d_cli_application_service_report.md --json
python -m devpilot_core validate-artifact docs/audits/post_h_002_d_cli_application_service_report.md --json
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
No red.
No mutaciones fuera de outputs/reports.
No claims enterprise/compliance/productive completos.
```

## Próximo paso

`POST-H-002-E — Quality gate y documentación`, que debe cerrar el hito `POST-H-002` con gate específico, documentación final y regresión completa acordada para cierre del backlog.
