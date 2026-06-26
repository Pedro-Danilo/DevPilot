---

doc_id: "POST-H-010-BACKLOG"
id: "POST-H-010"
title: "POST-H-010 — Observability retention local"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "active"
current_micro_sprint: "POST-H-010-C"
next_micro_sprint: "POST-H-010-D"
---

# POST-H-010 — Observability retention local

## 1. Objetivo

Diseñar e implementar una **política local de retención, rotación, redacción, exportación e higiene de observabilidad** para DevPilot, cubriendo eventos, trazas, métricas, AgentOps, sesiones agentic, reportes operacionales y persistencia SQLite local.

El objetivo no es agregar un backend externo de observabilidad ni activar OpenTelemetry remoto. El objetivo es que DevPilot pueda operar localmente con trazas útiles, seguras, retenidas por política y excluidas correctamente de paquetes limpios.

## 2. Contexto y justificación

El reverse engineering post-H identificó que DevPilot ya tiene una base real de observabilidad:

```text
src/devpilot_core/observability/events.py
src/devpilot_core/observability/tracing.py
src/devpilot_core/observability/trace_store.py
src/devpilot_core/observability/metrics.py
src/devpilot_core/observability/agentops.py
src/devpilot_core/store/local_store.py
.devpilot/devpilot.db
outputs/traces/events.jsonl
.devpilot/agent_sessions/
```

Sin embargo, la madurez actual es `implemented-initial`: existen eventos, trazas, métricas, AgentOps y persistencia local, pero no existe todavía una política formal que determine cuánto se conserva, cómo se rota, qué se redacta, qué se exporta, qué se elimina, qué entra en audit packs y qué queda excluido de ZIPs limpios.

Problemas a resolver:

```text
- Acumulación indefinida de outputs/traces/events.jsonl.
- Crecimiento no gobernado de .devpilot/devpilot.db.
- Sesiones agentic sin ciclo de vida operacional explícito.
- Ausencia de límites de tamaño y antigüedad.
- Falta de export redacted local reproducible.
- Riesgo de que artefactos runtime entren en paquetes limpios.
- Falta de un reporte de higiene de observabilidad para quality-gate.
```

## 3. Alcance

Incluye:

```text
- Política versionada de observability retention.
- Schema JSON para la política.
- Inventario read-only de observabilidad local.
- Plan de rotación/limpieza en dry-run.
- Export local redactado de eventos/traces/metrics/sessions.
- Validación de higiene de observabilidad.
- Integración con quality-gate hardening.
- Documentación operacional en runbook.
```

No incluye:

```text
- Export remoto activo.
- SaaS observability.
- OpenTelemetry collector real externo.
- Subida a servicios cloud.
- Recolección de secretos.
- Persistencia de raw prompts/raw outputs.
- Retención indefinida obligatoria.
- Borrado destructivo por defecto.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/observability/events.py
src/devpilot_core/observability/tracing.py
src/devpilot_core/observability/trace_store.py
src/devpilot_core/observability/metrics.py
src/devpilot_core/observability/agentops.py
src/devpilot_core/store/local_store.py
src/devpilot_core/agents/session.py
src/devpilot_core/policy/engine.py
src/devpilot_core/quality/gate.py
docs/05_operations/runbook.md
docs/03_security/post_h_security_risk_register.md
docs/backlogs/post_h_prioritized_roadmap.md
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
.devpilot/observability/retention_policy.json
docs/schemas/observability_retention_policy.schema.json
docs/schemas/observability_inventory.schema.json
docs/schemas/observability_cleanup_plan.schema.json
src/devpilot_core/observability/retention.py
src/devpilot_core/observability/inventory.py
src/devpilot_core/observability/cleanup.py
src/devpilot_core/observability/export.py
tests/test_post_h_010_observability_retention.py
tests/test_observability_retention_schema.py
docs/05_operations/observability_retention_runbook.md
outputs/reports/observability_inventory.json        # generado, no versionable
outputs/reports/observability_cleanup_plan.json     # generado, no versionable
outputs/reports/observability_retention_report.md   # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/cli.py o cli_registry cuando exista
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
docs/05_operations/runbook.md
```

## 6. Modelo de datos mínimo

### 6.1 Retention policy

```json
{
  "schema_version": "1.0",
  "policy_id": "devpilot-local-observability-retention",
  "local_first": true,
  "remote_export_enabled": false,
  "default_mode": "dry-run",
  "targets": [
    {
      "target_id": "events-jsonl",
      "path": "outputs/traces/events.jsonl",
      "kind": "jsonl",
      "classification": "runtime-observability",
      "contains_sensitive_payloads": false,
      "redaction_required": true,
      "retention_days": 30,
      "max_size_mb": 25,
      "rotation": {
        "enabled": true,
        "strategy": "size-or-age",
        "keep_rotated_files": 5
      },
      "clean_zip_excluded": true
    }
  ],
  "safety": {
    "delete_requires_execute": true,
    "dry_run_required_by_default": true,
    "raw_prompts_allowed": false,
    "raw_outputs_allowed": false,
    "secrets_allowed": false
  }
}
```

### 6.2 Observability inventory

Debe reportar como mínimo:

```text
target_id
path
exists
size_bytes
modified_at
records_estimated
retention_days
expired
rotation_recommended
redaction_required
clean_zip_excluded
risk_level
```

### 6.3 Cleanup plan

Debe reportar:

```text
actions_total
actions_by_kind
would_rotate
would_delete
would_redact
would_export
mutations_performed=false en dry-run
blocked_actions
required_approval_ids si aplica
```

## 7. Principios de diseño

```text
1. Local-first: todo opera sobre archivos locales del workspace.
2. Dry-run-first: ningún cleanup destructivo por defecto.
3. Evidence-first: todo plan produce reporte verificable.
4. Redaction-first: exportar solo payloads seguros.
5. ZIP hygiene: outputs, DB y agent_sessions no entran en fuente limpia.
6. Policy-aware: acciones destructivas pasan por PolicyEngine/Approval.
7. Deterministic: sin LLM, sin red, sin APIs externas.
```

## 8. Micro-sprints propuestos

### POST-H-010-A — Retention policy schema y defaults locales

Objetivo: definir contrato y política inicial para targets de observabilidad.

Tareas:

```text
1. Crear docs/schemas/observability_retention_policy.schema.json.
2. Registrar schema en docs/schemas/schema_catalog.json.
3. Crear .devpilot/observability/retention_policy.json.
4. Incluir targets: events.jsonl, devpilot.db, agent_sessions, outputs/reports, metrics, traces.
5. Crear tests de schema y carga de defaults.
6. Documentar clasificación runtime vs fuente versionable.
```

Criterios PASS:

```text
PASS si retention_policy.json valida contra schema.
PASS si todos los targets críticos están clasificados.
PASS si remote_export_enabled=false.
PASS si raw_prompts_allowed=false y raw_outputs_allowed=false.
PASS si clean_zip_excluded=true para outputs, db y agent_sessions.
```

Criterios BLOCK:

```text
BLOCK si se permite export remoto.
BLOCK si se permite guardar raw prompts/raw outputs.
BLOCK si se omite .devpilot/devpilot.db o .devpilot/agent_sessions.
```

Validación:

```powershell
python -m pytest tests/test_observability_retention_schema.py -q
python -m devpilot_core schema validate --schema-id ObservabilityRetentionPolicy --instance .devpilot/observability/retention_policy.json --json
```

### POST-H-010-B — Observability inventory read-only

Objetivo: construir inventario local de artefactos de observabilidad sin mutar archivos.

Tareas:

```text
1. Implementar src/devpilot_core/observability/inventory.py.
2. Leer retention_policy.json.
3. Inspeccionar existencia, tamaño, fechas y riesgo de cada target.
4. Generar CommandResult con summary y findings.
5. Agregar comando CLI observability inventory --json --write-report.
6. Escribir reporte en outputs/reports solo cuando --write-report sea explícito.
```

Criterios PASS:

```text
PASS si inventory no modifica archivos.
PASS si reporta todos los targets definidos en policy.
PASS si detecta targets ausentes como warning, no como error fatal cuando sean opcionales.
PASS si marca como riesgo cualquier archivo runtime que no esté excluido de ZIP limpio.
```

Criterios BLOCK:

```text
BLOCK si inventory borra o rota archivos.
BLOCK si lee secretos o raw payloads innecesarios.
BLOCK si requiere red o API externa.
```

Validación:

```powershell
python -m devpilot_core observability inventory --json --write-report
python -m pytest tests/test_post_h_010_observability_retention.py -q
```

### POST-H-010-C — Cleanup plan dry-run

Objetivo: generar plan local de limpieza/rotación sin ejecutar mutaciones por defecto.

Tareas:

```text
1. Implementar src/devpilot_core/observability/cleanup.py.
2. Calcular acciones would_rotate, would_delete, would_archive, would_redact.
3. Requerir --execute para cualquier mutación.
4. Integrar PolicyEngine para delete/rotate/archive.
5. Generar outputs/reports/observability_cleanup_plan.json.
6. Añadir findings BLOCK para intentos de cleanup fuera del workspace.
```

Criterios PASS:

```text
PASS si default es dry-run.
PASS si mutations_performed=false sin --execute.
PASS si delete/rotate requiere PolicyEngine.
PASS si cleanup fuera del workspace se bloquea.
```

Criterios BLOCK:

```text
BLOCK si se borra algo sin --execute.
BLOCK si se permite path escape.
BLOCK si el plan incluye .git, src o docs como targets de limpieza runtime.
```

Validación:

```powershell
python -m devpilot_core observability cleanup-plan --json --write-report
python -m pytest tests/test_post_h_010_observability_retention.py -q
```

### POST-H-010-D — Export local redactado

Objetivo: permitir export local de evidencia de observabilidad, redactada y empaquetable para auditoría local.

Tareas:

```text
1. Implementar src/devpilot_core/observability/export.py.
2. Exportar summary de eventos, métricas y spans sin payloads crudos.
3. Permitir export JSON/Markdown local bajo outputs/reports o outputs/audit_exports.
4. Incluir hashes/checksums opcionales.
5. Garantizar external_api_used=false y network_used=false.
6. Documentar qué se excluye y por qué.
```

Criterios PASS:

```text
PASS si export no incluye raw prompts ni raw outputs.
PASS si export no incluye secretos.
PASS si export indica redaction_applied=true.
PASS si export puede reproducirse localmente.
```

Criterios BLOCK:

```text
BLOCK si export contiene valores tipo API key, token, password o .env.
BLOCK si export remoto se habilita.
BLOCK si export falla silenciosamente sin findings.
```

Validación:

```powershell
python -m devpilot_core observability export --redacted --json --write-report
python -m pytest tests/test_post_h_010_observability_retention.py -q
```

### POST-H-010-E — Gate de retención e higiene observability

Objetivo: integrar la política de retención con quality-gate hardening y runbook.

Tareas:

```text
1. Agregar subgate observability-retention al quality gate hardening.
2. Validar policy, inventory y ZIP hygiene.
3. Actualizar .devpilot/testing/test_contract_registry.json.
4. Crear docs/05_operations/observability_retention_runbook.md.
5. Actualizar docs/05_operations/runbook.md.
6. Documentar comandos de mantenimiento local.
```

Criterios PASS:

```text
PASS si quality-gate hardening incluye subgate observability-retention.
PASS si test-contracts validate pasa.
PASS si project-state validate sigue pasando.
PASS si no se versionan outputs, db ni agent_sessions.
```

Criterios BLOCK:

```text
BLOCK si el gate depende de outputs efímeros para pasar.
BLOCK si el gate exige red.
BLOCK si el gate relaja exclusions del ZIP limpio.
```

Validación:

```powershell
python -m pytest tests/test_post_h_010_observability_retention.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 9. Casos de uso soportados al cierre

```text
- Un operador consulta inventario local de observabilidad.
- Un operador genera plan de cleanup sin mutar.
- Un operador exporta evidencia redactada.
- Quality gate detecta artefactos runtime no gobernados.
- Release hygiene confirma que runtime artifacts no entran en ZIP limpio.
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Borrado accidental de trazas útiles | Alta | dry-run por defecto, --execute explícito y PolicyEngine. |
| Export de datos sensibles | Alta | redaction-first, tests anti-secret, raw prompts prohibidos. |
| Crecimiento indefinido de DB/traces | Media-alta | retention_days, max_size_mb, cleanup plan. |
| Romper reproducibilidad por depender de outputs | Media | gates no deben requerir outputs efímeros. |
| Falsa sensación de observabilidad industrial | Media | disclaimers: local-only, no SaaS, no collector remoto. |

## 11. No-go gates

```text
NO remote export.
NO external observability service.
NO secrets in exported reports.
NO raw prompts/raw outputs.
NO deletion without --execute.
NO path outside workspace.
NO inclusion of runtime artifacts in clean ZIP.
```

## 12. Definition of Done del hito

```text
- Policy schema implementado y registrado.
- Retention policy local creada.
- Inventory read-only implementado.
- Cleanup plan dry-run implementado.
- Export redacted local implementado.
- Quality gate integrado.
- Test contract actualizado.
- Runbook actualizado.
- Pruebas focales y gates pasan.
```

## 13. Comandos finales esperados

```powershell
python -m devpilot_core observability inventory --json --write-report
python -m devpilot_core observability cleanup-plan --json --write-report
python -m devpilot_core observability export --redacted --json --write-report
python -m pytest tests/test_post_h_010_observability_retention.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```


## 14. Avance de implementación — POST-H-010-A

Estado: `implemented-initial`.

`POST-H-010-A — Retention policy schema y defaults locales` inicia el hito con un contrato source-controlled para gobernar retención de observabilidad local sin ejecutar inventario, limpieza, exportación ni mutaciones runtime.

Artefactos implementados:

```text
docs/schemas/observability_retention_policy.schema.json
.devpilot/observability/retention_policy.json
src/devpilot_core/observability/retention.py
tests/test_observability_retention_schema.py
tests/test_post_h_010_observability_retention.py
docs/audits/post_h_010_a_retention_policy_schema_report.md
docs/post_h_010_a_manifest.json
```

Capacidades implementadas:

```text
- Schema `ObservabilityRetentionPolicy` registrado en `schema_catalog`.
- Política local versionada para targets críticos: events JSONL, traces, SQLite local, agent_sessions, outputs/reports y métricas.
- Loader semántico `load_observability_retention_policy(root)`.
- Validador semántico `ObservabilityRetentionPolicyValidator` para no-go gates: remote_export=false, dry-run por defecto, raw prompts/raw outputs prohibidos, secrets prohibidos y clean_zip_excluded=true para runtime artifacts.
- Clasificación explícita runtime vs fuente versionable.
```

Límites de esta versión:

```text
- El inventario real read-only queda implementado en `POST-H-010-B`.
- No calcula plan de cleanup/rotación (`POST-H-010-C`).
- No exporta evidencia redactada (`POST-H-010-D`).
- No integra aún subgate `observability-retention` al `quality-gate hardening` (`POST-H-010-E`).
- No borra, rota, archiva ni exporta artefactos runtime.
```

Comandos de validación del micro-sprint:

```powershell
python -m pytest tests/test_observability_retention_schema.py tests/test_post_h_010_observability_retention.py -q
python -m devpilot_core schema validate --schema-id ObservabilityRetentionPolicy --instance .devpilot/observability/retention_policy.json --json
```


## 15. Avance de implementación — POST-H-010-B

Estado: `implemented-initial`.

`POST-H-010-B — Observability inventory read-only` implementa el primer inventario local de observabilidad basado en `.devpilot/observability/retention_policy.json`. La capacidad inspecciona metadatos de los targets runtime sin limpiar, rotar, exportar, leer payloads crudos ni mutar fuentes.

Artefactos implementados:

```text
src/devpilot_core/observability/inventory.py
docs/schemas/observability_inventory.schema.json
tests/test_observability_inventory.py
docs/audits/post_h_010_b_observability_inventory_report.md
docs/post_h_010_b_manifest.json
```

Capacidades implementadas:

```text
- Schema `ObservabilityInventory` registrado en `schema_catalog`.
- Builder `ObservabilityInventoryBuilder` con salida `CommandResult`.
- CLI `python -m devpilot_core observability inventory --json [--write-report]`.
- Reportes opt-in `outputs/reports/observability_inventory.json|md`.
- Inspección metadata-only: existencia, tamaño, fecha, conteo estimado, expiración, recomendación de rotación, redacción requerida, clean_zip_excluded y risk_level.
- Conteo SQLite metadata-only cuando `.devpilot/devpilot.db` existe; no se leen prompts/outputs ni payloads crudos.
```

Límites de esta versión:

```text
- No ejecuta cleanup, delete, rotate, archive ni export.
- No integra todavía `observability-retention` al `quality-gate hardening` (`POST-H-010-E`).
- Los targets ausentes en un checkout limpio son warnings operacionales, no bloqueo.
- El plan de acciones `would_rotate/would_delete/would_export` queda para `POST-H-010-C/D`.
```

Comandos de validación del micro-sprint:

```powershell
python -m devpilot_core observability inventory --json --write-report
python -m devpilot_core schema validate --schema-id ObservabilityInventory --instance outputs/reports/observability_inventory.json --json
python -m pytest tests/test_observability_inventory.py tests/test_post_h_010_observability_retention.py -q
```

## 16. Avance de implementación — POST-H-010-C

Estado: `implemented-initial`.

`POST-H-010-C — Cleanup plan dry-run` agrega un planificador local de acciones de higiene de observabilidad sin ejecutar mutaciones. Consume el inventario metadata-only de `POST-H-010-B` y calcula acciones `would_rotate`, `would_delete`, `would_archive`, `would_redact` y `would_export`, dejando explícito qué acciones destructivas requieren `PolicyEngine` y aprobación antes de cualquier ejecución futura.

Artefactos implementados:

```text
src/devpilot_core/observability/cleanup.py
docs/schemas/observability_cleanup_plan.schema.json
tests/test_observability_cleanup_plan.py
docs/audits/post_h_010_c_cleanup_plan_report.md
docs/post_h_010_c_manifest.json
```

Capacidades implementadas:

```text
- Schema `ObservabilityCleanupPlan` registrado en `schema_catalog`.
- Builder `ObservabilityCleanupPlanner` con salida `CommandResult`.
- CLI `python -m devpilot_core observability cleanup-plan --json [--write-report]`.
- Reportes opt-in `outputs/reports/observability_cleanup_plan.json|md`.
- Plan de acciones sin mutaciones: rotate/delete/archive/redact/export.
- Simulación `PolicyEngine` para acciones destructivas (`rotate`, `delete`, `archive`) con approval ids determinísticos.
- Bloqueo explícito de path escape y de targets bajo `.git/`, `src/`, `docs/`, `tests/` o metadata source-controlled.
```

Límites de esta versión:

```text
- `observability cleanup-plan` no borra, rota, archiva, redacta ni exporta.
- `--execute` funciona como safety probe y bloquea: este comando es plan-only.
- La ejecución real de export redactado queda para `POST-H-010-D`.
- La integración `observability-retention` con `quality-gate hardening` queda para `POST-H-010-E`.
- Esta versión no representa estado production-ready; es una base deterministic/local-first para evolucionar el hito.
```

Comandos de validación del micro-sprint:

```powershell
python -m devpilot_core observability cleanup-plan --json --write-report
python -m devpilot_core schema validate --schema-id ObservabilityCleanupPlan --instance outputs/reports/observability_cleanup_plan.json --json
python -m pytest tests/test_observability_cleanup_plan.py tests/test_post_h_010_observability_retention.py -q
```

