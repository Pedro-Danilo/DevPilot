---
title: "FUNC-SPRINT-07 Audit — Event Log JSONL y observabilidad local"
doc_id: "DEVPL-AUDIT-FUNC-007"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-07"
updated: "2026-06-07"
approval: "approved_by_owner_direction"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# FUNC-SPRINT-07 Audit — Event Log JSONL y observabilidad local

## 1. Propósito

Este artefacto registra la auditoría técnica de `FUNC-SPRINT-07 — Event Log JSONL y observabilidad local`. Su propósito es dejar trazabilidad sobre lo implementado, cómo se integra con DevPilot Local, qué comandos se deben usar, qué pruebas se ejecutaron, qué riesgos permanecen y bajo qué criterios el sprint puede cerrarse.

## 2. Alcance

El sprint implementa una primera versión local-first del Event Log JSONL. La implementación cubre:

- contrato `EventRecord`;
- logger append-only `EventLogger`;
- escritura segura bajo `outputs/traces/events.jsonl`;
- eventos `command.started`, `gate.evaluated`, `command.completed` y `command.error`;
- integración con el wrapper principal de CLI;
- integración con gates basados en `CommandResult`;
- redacción básica de secretos sintéticos y claves sensibles;
- pruebas unitarias y de integración CLI;
- sincronización de README, runbook y backlog funcional.

No incluye todavía rotación, retención configurable, persistencia SQLite, correlación formal con `EvidenceReport`, exportación OpenTelemetry, dashboards ni SecretGuard industrial.

## 3. Componentes creados

| Componente | Propósito | Rol dentro de DevPilot |
|---|---|---|
| `src/devpilot_core/observability/events.py` | Define `EventRecord`, `EventLogger`, redacción y helpers de eventos. | Base de observabilidad local append-only para comandos y gates. |
| `src/devpilot_core/observability/__init__.py` | Expone API pública del paquete de observabilidad. | Boundary importable para CLI, futuros agentes y futuros stores. |
| `tests/test_event_logger.py` | Valida JSONL, redacción, seguridad de rutas e integración CLI. | Quality gate automatizado del sprint. |
| `docs/functional_sprint_07_manifest.json` | Manifiesto del sprint. | Evidencia docs-as-code de cambios y criterios. |

## 4. Componentes modificados

| Componente | Ajuste | Motivo |
|---|---|---|
| `src/devpilot_core/cli.py` | Agrega wrapper de observabilidad alrededor de `main()` y eventos de resultado en gates. | Registrar inicio/cierre/error de comandos y evaluación de gates. |
| `README.md` | Actualiza estado, comandos, estructura y explicación de trazas. | Entrada operativa rápida sincronizada. |
| `docs/05_operations/runbook.md` | Documenta operación, verificación, PASS/BLOCK y riesgos de EventLogger. | Guía local de ejecución y recuperación. |
| `docs/functional_backlog_after_precode.md` | Marca Sprint 07 implementado y mueve `next_sprint` a Sprint 08. | Trazabilidad del backlog funcional. |

## 5. Funcionamiento técnico

`EventLogger` recibe un `EventRecord`, redacta datos sensibles mediante reglas básicas y escribe una línea JSON por evento en:

```text
outputs/traces/events.jsonl
```

El archivo es append-only. Cada línea debe ser JSON válido. La escritura se limita al project root para evitar salida accidental fuera del repositorio.

Eventos mínimos actuales:

```text
command.started    inicio de un comando CLI
gate.evaluated     resultado compacto de un gate/validador
command.completed  fin del comando con exit code
command.error      error controlado o excepción defensiva
```

## 6. Contrato de evento

```text
event_id
event_type
timestamp
level
command
status opcional
ok opcional
exit_code opcional
message opcional
subject opcional
summary opcional
findings opcional
metadata opcional
```

La implementación evita persistir payloads completos de comandos en eventos. Para `CommandResult`, solo registra `summary`, `findings` normalizados y metadatos acotados.

## 7. Redacción básica

La redacción inicial cubre:

```text
api_key
token
access_token
refresh_token
secret
password
authorization
sk-*
ghp_*
hf_*
xox*-*
```

Esta redacción es preliminar. En una versión de producción industrial debe migrar a SecretGuard/Policy Engine con reglas declarativas, pruebas de fuga, clasificación de datos, allowlists/denylists y auditoría de falsos positivos/falsos negativos.

## 8. Comandos de uso

```powershell
python -m devpilot_core --version
python -m devpilot_core standards status --json
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
Get-Content outputs\traces\events.jsonl -Tail 20
python -m pytest -q
```

## 9. Criterios PASS

El sprint se considera PASS si:

- `pytest -q` pasa completo;
- `EventLogger` escribe `outputs/traces/events.jsonl`;
- cada línea JSONL es parseable;
- los comandos CLI emiten `command.started` y `command.completed`;
- los gates/validadores integrados emiten `gate.evaluated`;
- los errores controlados emiten `command.error`;
- secretos sintéticos conocidos se redactan antes de persistirse;
- la escritura de eventos queda limitada al project root;
- README, runbook y backlog quedan sincronizados.

## 10. Criterios BLOCK

El sprint debe bloquearse si:

- `EventLogger` puede escribir fuera del project root;
- `events.jsonl` contiene líneas no parseables;
- se rompe compatibilidad con comandos previos;
- se filtran secretos sintéticos evidentes como `sk-*`, `ghp_*` o `hf_*`;
- la observabilidad modifica stdout/stderr esperado de los comandos;
- se agrega una dependencia externa no justificada;
- se requiere API key o red externa;
- `pytest -q` falla.

## 11. Pruebas aplicadas

Pruebas automatizadas incorporadas:

- escritura JSONL y redacción de secretos sintéticos;
- bloqueo de rutas fuera del project root;
- evento `gate.evaluated` derivado de `CommandResult`;
- integración CLI para `--version` con `command.started` y `command.completed`;
- integración CLI para `validate-frontmatter` con `gate.evaluated`;
- helpers de redacción sobre strings y estructuras anidadas;
- suite completa de regresión.

Resultado esperado:

```text
pytest -q -> 42 passed
```

## 12. Riesgos y evolución posterior

Esta implementación es una primera versión. Para alcanzar nivel de producción industrial debe evolucionar con:

- rotación y retención de eventos;
- correlación formal entre `event_id`, `report_id`, ejecución y futuro workspace;
- persistencia SQLite/EventStore;
- consultas históricas de auditoría;
- SecretGuard/Policy Engine declarativo;
- OpenTelemetry/exportadores externos opcionales;
- trazas agentic con `agent_id`, `tool_id`, costos, latencia y aprobación humana.

## 13. Decisión ADR

No se abre nueva ADR porque el sprint implementa una capacidad prevista explícitamente en el backlog, no agrega dependencias, no activa servicios externos, no altera seguridad ni persistencia estructural, no cambia proveedores, no modifica APIs externas y no altera decisiones arquitectónicas aprobadas. Se documenta como evolución funcional del core CLI y de observabilidad local.
