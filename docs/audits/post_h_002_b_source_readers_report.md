---
title: "POST-H-002-B — Lectores de fuentes post-H"
doc_id: "POST-H-002-B-AUDIT"
version: "1.0.0"
updated: "2026-06-24"
status: "approved"
approval: "internal"
owner: "Ordóñez"
---

# POST-H-002-B — Lectores de fuentes post-H

## Propósito

Implementar una primera versión `implemented-initial` de lectores locales y read-only para las fuentes creadas durante `POST-H-EVAL-001`, de forma que el futuro dashboard de madurez de `POST-H-002` se base en evidencia verificable y no en inferencias libres.

## Estado

Estado: `implemented-initial`.

El micro-sprint queda limitado a lectura, normalización y resumen de fuentes. No implementa todavía `MaturityDashboardBuilder`, no genera archivos en `outputs/reports`, no expone comando CLI y no integra ApplicationService.

## Alcance implementado

Se implementó `src/devpilot_core/maturity/sources.py` con:

```text
SourceSpec
SourceReadResult
PostHSourceBundle
PostHSourceReader
JSON_SOURCE_SPECS
MARKDOWN_SOURCE_SPECS
summarize_json_payload
extract_markdown_headings
```

Fuentes JSON obligatorias:

```text
docs/post_h_eval_001_manifest.json
.devpilot/evals/post_h_eval_001_decision_matrix.json
.devpilot/evals/post_h_eval_001_security_risk_register.json
.devpilot/evals/post_h_eval_001_test_cost_assessment.json
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
.devpilot/testing/test_contract_registry.json
```

Fuentes Markdown fallback:

```text
docs/audits/post_h_eval_001_baseline_assessment.md
docs/02_architecture/post_h_current_architecture_map.md
docs/03_security/post_h_security_risk_register.md
docs/04_quality/post_h_test_cost_assessment.md
docs/backlogs/post_h_prioritized_roadmap.md
docs/audits/post_h_eval_001_closure_report.md
```

## Funcionamiento

`PostHSourceReader` recibe la raíz del workspace y specs declarativas de fuentes. Para JSON, valida existencia, parseo y produce un resumen compacto con identificadores, estado, totales y señales de seguridad. Para Markdown, valida existencia, extrae headings y reporta secciones faltantes como warning cuando el documento es fallback no crítico.

El resultado se agrupa en `PostHSourceBundle`, que expone:

```text
ok
blocking_findings_total
warnings_total
evidence_paths()
source_by_id()
to_dict()
to_command_result()
```

## Integración dentro de DevPilot

La implementación se integra con el paquete `devpilot_core.maturity` y reutiliza `CommandResult`, `Finding`, `Severity` y `ExitCode`. No introduce dependencias externas, no toca `cli.py`, no crea comandos y no modifica el runtime de agentes.

## Criterios PASS

```text
PASS si todas las fuentes JSON obligatorias se leen correctamente.
PASS si una fuente crítica ausente genera Severity.BLOCK y ExitCode.BLOCK.
PASS si Markdown funciona como fallback controlado y warning-tolerant.
PASS si los resultados exponen network_used=false, external_api_used=false y mutations_performed=false.
PASS si los tests focales del paquete maturity siguen pasando.
```

## Criterios BLOCK

```text
BLOCK si se inventa madurez sin evidencia local.
BLOCK si se ignora alguna fuente JSON obligatoria.
BLOCK si los lectores mutan fuentes o escriben outputs.
BLOCK si se habilita remote execution, connector write, plugin execution, external APIs, red o shell.
```

## Riesgos y limitaciones

La capacidad todavía no construye el dashboard final. El riesgo principal es interpretar el bundle de fuentes como reporte de madurez definitivo. La conversión de fuentes a capacidades `MaturityCapability` y la generación JSON/Markdown corresponden a `POST-H-002-C`.

## Comandos de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_002_maturity_dashboard.py -q
python -m pytest tests/test_schema_registry.py tests/test_post_h_002_maturity_dashboard.py -q
python -m devpilot_core validate-frontmatter docs/audits/post_h_002_b_source_readers_report.md --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
external_api_used=false
network_used=false
mutations_performed=false
```

## Próximo paso

`POST-H-002-C — Generador de dashboard local` debe construir el dashboard JSON/Markdown usando estos lectores, validando el resultado contra `docs/schemas/maturity_dashboard.schema.json`.
