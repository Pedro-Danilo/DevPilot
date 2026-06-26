---
doc_id: "POST-H-008-BACKLOG"
id: "POST-H-008"
title: "POST-H-008 — Runtime state lifecycle policy"
status: "approved"
version: "0.4.0"
owner: "Ordóñez"
updated: "2026-06-26"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_runtime_features_added_by_backlog: false
no_remote_execution_enabled: true
implementation_status: "closed"
approval: "internal"
---

# POST-H-008 — Runtime state lifecycle policy

## 1. Objetivo

Definir e implementar una **política local de ciclo de vida para el estado runtime de DevPilot**, cubriendo generación, clasificación, retención, limpieza, exportación, redacción, exclusión de ZIPs limpios y verificación de higiene de artefactos.

El objetivo es evitar que trazas, SQLite local, sesiones de agentes, reportes generados, caches o outputs temporales se mezclen con la fuente de verdad del repositorio o filtren información sensible.

## 2. Contexto y justificación

DevPilot genera evidencia local en varios lugares:

```text
outputs/reports/
outputs/traces/
outputs/evals/
outputs/drafts/
.devpilot/devpilot.db
.devpilot/agent_sessions/
.devpilot/rag/docs_index.json
.pytest_cache/
__pycache__/
ui/web/dist/
```

Durante `POST-H-EVAL-001` se reforzó la regla de ZIP limpio mediante `.gitignore`, `git archive` y exclusión de runtime artifacts. Sin embargo, aún falta una política ejecutable que diga:

```text
qué es source-of-truth;
qué es runtime state;
qué puede versionarse;
qué debe excluirse;
cuánto tiempo conservarlo;
cómo limpiar sin perder evidencia crítica;
cómo exportar evidencia para auditoría;
cómo redactar secretos o payloads sensibles.
```

Este hito formaliza esa disciplina.

## 3. Alcance

Incluye:

```text
- Taxonomía de runtime artifacts.
- Runtime state policy declarativa.
- Validador de higiene de runtime state.
- Comandos dry-run para inspección/limpieza/export.
- Reporte de cumplimiento.
- Reglas de redacción y retención mínima.
- Integración con quality gate y release hygiene.
```

No incluye:

```text
- Borrado automático destructivo por defecto.
- Cifrado completo de audit packs.
- Signing/encryption de packs; queda para POST-H-013.
- Observability retention completa; queda para POST-H-010.
- Remote backup.
- Cloud storage.
```

## 4. Fuentes de entrada obligatorias

```text
.gitignore
src/devpilot_core/store/local_store.py
src/devpilot_core/observability/events.py
src/devpilot_core/observability/trace_store.py
src/devpilot_core/agents/session.py
src/devpilot_core/release/package.py
src/devpilot_core/auditpack/
docs/05_operations/runbook.md
docs/audits/post_h_eval_001_closure_report.md
docs/post_h_eval_001_manifest.json
docs/backlogs/post_h_prioritized_roadmap.md
```

## 5. Entregables

```text
src/devpilot_core/runtime_state/models.py
src/devpilot_core/runtime_state/policy.py
src/devpilot_core/runtime_state/inventory.py
src/devpilot_core/runtime_state/cleanup.py
src/devpilot_core/runtime_state/export.py
src/devpilot_core/runtime_state/report.py
src/devpilot_core/runtime_state/__init__.py
.devpilot/runtime_state_policy.json
docs/schemas/runtime_state_policy.schema.json
docs/schemas/runtime_state_inventory.schema.json
docs/05_operations/runtime_state_lifecycle_policy.md
outputs/reports/runtime_state_inventory.json        # generado, no versionar
outputs/reports/runtime_state_lifecycle_report.md   # generado, no versionar
tests/test_post_h_008_runtime_state_lifecycle.py
tests/test_runtime_state_policy_schema.py
```

## 6. Modelo de datos mínimo

### Policy

```json
{
  "schema_version": "1.0",
  "policy_id": "devpilot-runtime-state-policy",
  "default_mode": "dry-run",
  "artifact_classes": [
    {
      "class_id": "trace-events",
      "paths": ["outputs/traces/**/*.jsonl"],
      "source_of_truth": false,
      "versionable": false,
      "sensitive": true,
      "retention_days": 30,
      "cleanup_allowed": true,
      "export_allowed": true,
      "redaction_required": true
    }
  ],
  "zip_hygiene": {
    "must_exclude": ["outputs/", ".devpilot/devpilot.db", ".devpilot/agent_sessions/"],
    "git_archive_required": true
  },
  "safety": {
    "destructive_cleanup_default": false,
    "requires_execute_flag": true
  }
}
```

### Inventory

```json
{
  "schema_version": "1.0",
  "generated_at_utc": "...",
  "artifacts_total": 0,
  "by_class": {},
  "violations": [
    {
      "violation_id": "RUNTIME_STATE_VERSIONED",
      "path": "outputs/reports/example.json",
      "severity": "block",
      "recommended_action": "remove from git tracking or regenerate outside source archive"
    }
  ]
}
```

## 7. Reglas de clasificación

| Clase | Ejemplos | Versionable | Limpieza |
|---|---|---:|---:|
| Source-of-truth | `src/`, `tests/`, `docs/`, `.devpilot/*.json` seleccionado | Sí | No |
| Generated reports | `outputs/reports/*` | No | Sí, con política |
| Trace events | `outputs/traces/*` | No | Sí, con retención |
| Local DB | `.devpilot/devpilot.db` | No | Export/backup controlado |
| Agent sessions | `.devpilot/agent_sessions/*` | No | Sí, redactado |
| RAG index | `.devpilot/rag/docs_index.json` | Condicional | Regenerable |
| Caches | `.pytest_cache`, `__pycache__`, `node_modules` | No | Sí |
| Release evidence | manifests/changelog versionados | Sí, si son fuente | No automático |

## 8. Micro-sprints propuestos

### POST-H-008-A — Taxonomía y policy schema

Objetivo: definir taxonomía formal y schema de policy.

Tareas:

```text
1. Crear runtime_state_policy.schema.json.
2. Crear runtime_state_inventory.schema.json.
3. Registrar schemas.
4. Crear .devpilot/runtime_state_policy.json.
5. Documentar taxonomía en docs/05_operations/runtime_state_lifecycle_policy.md.
```

Criterios PASS:

```text
PASS si la policy valida contra schema.
PASS si must_exclude incluye outputs, devpilot.db y agent_sessions.
PASS si destructive_cleanup_default=false.
```

Criterios BLOCK:

```text
BLOCK si se permite borrar source-of-truth.
BLOCK si cleanup destructivo queda habilitado por defecto.
```

### POST-H-008-B — Runtime state inventory read-only

Objetivo: inventariar estado runtime sin modificar archivos.

Tareas:

```text
1. Implementar scanner de rutas según policy.
2. Clasificar artefactos por clase.
3. Detectar archivos generados accidentalmente versionables.
4. Detectar DB/sessions/traces/outputs.
5. Generar inventory JSON/Markdown.
```

Comando propuesto:

```powershell
python -m devpilot_core runtime-state inventory --json
python -m devpilot_core runtime-state inventory --write-report --json
```

Criterios PASS:

```text
PASS si inventory es read-only.
PASS si detecta runtime artifacts conocidos.
PASS si reporta violaciones sin borrar nada.
```

### POST-H-008-C — Cleanup plan dry-run

Objetivo: generar plan de limpieza sin ejecutar.

Tareas:

```text
1. Implementar RuntimeStateCleanupPlanner.
2. Calcular archivos elegibles para cleanup.
3. Separar safe-cleanup, requires-approval, never-delete.
4. Generar cleanup plan JSON/Markdown.
5. Agregar --execute solo para limpieza segura y explícita.
```

Comandos propuestos:

```powershell
python -m devpilot_core runtime-state cleanup-plan --json
python -m devpilot_core runtime-state cleanup --dry-run --json
python -m devpilot_core runtime-state cleanup --execute --json
```

Criterios PASS:

```text
PASS si dry-run no borra nada.
PASS si source-of-truth aparece como never-delete.
PASS si --execute exige confirmación/flag explícito.
```

Criterios BLOCK:

```text
BLOCK si --execute puede borrar docs/src/tests.
BLOCK si se borra .devpilot project state sin backup/approval.
```

### POST-H-008-D — Export y redacción de evidencia runtime

Objetivo: permitir exportar evidencia sin filtrar secretos o payloads sensibles.

Tareas:

```text
1. Implementar export de trazas/reportes/sesiones con redacción.
2. No incluir raw prompts/raw outputs.
3. Generar manifest de export.
4. Calcular checksums.
5. Integrar con auditpack/release como fuente opcional.
```

Comando propuesto:

```powershell
python -m devpilot_core runtime-state export --dry-run --json
python -m devpilot_core runtime-state export --execute --output outputs/runtime_exports/<id> --json
```

Criterios PASS:

```text
PASS si export genera manifest y checksums.
PASS si secretos conocidos se redactan.
PASS si no requiere red ni APIs externas.
```

### POST-H-008-E — Gate de higiene runtime y release archive

Objetivo: bloquear ZIPs/repos sucios con runtime artifacts.

Tareas:

```text
1. Agregar subgate runtime-state-hygiene a quality gate o industrial readiness.
2. Validar que git archive excluye outputs, DB, sessions, caches.
3. Agregar tests focales.
4. Documentar en runbook.
5. Registrar test contract.
```

Criterios PASS:

```text
PASS si quality-gate detecta runtime artifacts versionados.
PASS si git archive basado en HEAD queda limpio.
PASS si test-contracts validate pasa.
```

## 9. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_008_runtime_state_lifecycle.py -q
python -m pytest tests/test_runtime_state_policy_schema.py tests/test_schema_registry.py -q
python -m devpilot_core runtime-state inventory --write-report --json
python -m devpilot_core runtime-state cleanup-plan --json
python -m devpilot_core runtime-state export --dry-run --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Borrar evidencia útil | Alta | Dry-run por defecto, retention y export. |
| Borrar source-of-truth | Crítica | never-delete y tests de bloqueo. |
| Filtrar secretos en export | Alta | Redaction required y SecretGuard. |
| Confundir RAG index con fuente | Media | Clasificación condicional/regenerable. |
| Overhead operacional | Media | Comandos simples y reportes claros. |

## 11. No-go gates

```text
NO-GO si cleanup destructivo queda habilitado por defecto.
NO-GO si se permite borrar src/docs/tests sin approval y backup.
NO-GO si export incluye secretos o raw prompts/raw outputs.
NO-GO si se versionan outputs, devpilot.db o agent_sessions.
NO-GO si se habilita backup remoto o cloud no gobernado.
```

## 12. Entregable verificable

```text
Runtime state policy versionada.
Inventory read-only.
Cleanup plan dry-run.
Export redactado opcional.
Gate de higiene runtime.
Tests focales PASS.
Quality gate hardening PASS.
```


## 13. Avance de implementación — POST-H-008-A

Estado: `implemented-initial`.

`POST-H-008-A — Taxonomía y policy schema` eleva este backlog a `approved` e implementa la primera base gobernada del runtime state lifecycle.

Artefactos creados:

```text
docs/schemas/runtime_state_policy.schema.json
docs/schemas/runtime_state_inventory.schema.json
.devpilot/runtime_state_policy.json
docs/05_operations/runtime_state_lifecycle_policy.md
docs/audits/post_h_008_a_runtime_state_policy_schema_report.md
docs/post_h_008_a_manifest.json
tests/test_runtime_state_policy_schema.py
tests/test_post_h_008_runtime_state_lifecycle.py
```

Criterios PASS cubiertos:

```text
- La policy valida contra `RuntimeStatePolicy`.
- `must_exclude` incluye `outputs/`, `.devpilot/devpilot.db` y `.devpilot/agent_sessions/`.
- `destructive_cleanup_default=false`.
- Source-of-truth queda como `never_delete` y `cleanup_allowed=false`.
- RuntimeStateInventory queda registrado como contrato estructural para `POST-H-008-B`.
```

Límites explícitos de esta versión:

```text
- No implementa todavía scanner read-only.
- No implementa cleanup-plan.
- No implementa export/redacción.
- No integra todavía runtime-state-hygiene al quality gate.
```

## 14. Avance de implementación — POST-H-008-B

Estado: `implemented-initial`.

`POST-H-008-B — Runtime state inventory read-only` implementa el scanner local de inventario runtime sin modificar archivos fuente ni ejecutar cleanup/export.

### Implementado

```text
- src/devpilot_core/runtime_state/models.py
- src/devpilot_core/runtime_state/policy.py
- src/devpilot_core/runtime_state/inventory.py
- src/devpilot_core/runtime_state/report.py
- src/devpilot_core/runtime_state/__init__.py
- Comando CLI: python -m devpilot_core runtime-state inventory --json
- Reporte opcional: outputs/reports/runtime_state_inventory.json
- Reporte opcional: outputs/reports/runtime_state_lifecycle_report.md
- Tests focales: tests/test_runtime_state_inventory.py
- Manifest: docs/post_h_008_b_manifest.json
- Auditoría: docs/audits/post_h_008_b_runtime_state_inventory_report.md
```

### Capacidades adicionadas

```text
- Inventario basado en artifact_classes de .devpilot/runtime_state_policy.json.
- Resumen por clase con artifacts_total, bytes_total, versionable, cleanup_allowed y redaction_required.
- Detección de runtime artifacts conocidos: outputs, traces, evals, drafts, devpilot.db, agent_sessions, RAG index y caches.
- Detección bloqueante de runtime artifacts no versionables rastreados por Git.
- Reportes JSON/Markdown generados solo bajo --write-report.
- Registro declarativo de runtime-state.inventory en CLI registry para no violar el no-growth gate.
```

### Criterios PASS cubiertos

```text
PASS si inventory es read-only.
PASS si detecta runtime artifacts conocidos.
PASS si reporta violaciones sin borrar nada.
```

### Límites de esta versión

```text
- No implementa cleanup plan.
- No implementa cleanup --execute.
- No implementa export/redacción.
- No integra aún runtime-state-hygiene al quality gate.
```

### Siguiente micro-sprint

`POST-H-008-D — Export y redacción de evidencia runtime`.


## 15. Avance de implementación — POST-H-008-C

Estado: `implemented-initial`.

`POST-H-008-C — Cleanup plan dry-run` implementa el planificador local de limpieza runtime basado en `RuntimeStateInventory` y `.devpilot/runtime_state_policy.json`. El objetivo sigue siendo conservador: planificar primero, ejecutar solo limpieza segura explícita y nunca permitir borrado automático de source-of-truth.

### Implementado

```text
- src/devpilot_core/runtime_state/cleanup.py
- Comando CLI: python -m devpilot_core runtime-state cleanup-plan --json
- Comando CLI: python -m devpilot_core runtime-state cleanup --dry-run --json
- Ejecución explícita: python -m devpilot_core runtime-state cleanup --execute --confirm-cleanup --json
- Reporte opcional: outputs/reports/runtime_state_cleanup_plan.json
- Reporte opcional: outputs/reports/runtime_state_cleanup_plan.md
- Schema: docs/schemas/runtime_state_cleanup_plan.schema.json
- Tests focales: tests/test_runtime_state_cleanup_plan.py
- Manifest: docs/post_h_008_c_manifest.json
- Auditoría: docs/audits/post_h_008_c_cleanup_plan_report.md
```

### Capacidades adicionadas

```text
- Clasificación safe-cleanup / requires-approval / never-delete / retained.
- Cálculo de elegibilidad por retention_days y edad del archivo.
- Bloqueo de docs/src/tests/.devpilot project state/runtime policy/TCR como never-delete.
- --execute bloqueado sin --confirm-cleanup.
- --execute limitado a safe-cleanup.
- RuntimeStateCleanupPlan registrado como contrato estructural.
```

### Criterios PASS cubiertos

```text
PASS si dry-run no borra nada.
PASS si source-of-truth aparece como never-delete.
PASS si --execute exige confirmación/flag explícito.
```

### Límites de esta versión

```text
- No implementa export/redacción de payloads runtime.
- No implementa cuotas por tamaño ni rotación industrial avanzada.
- No integra todavía runtime-state-hygiene al quality-gate hardening.
- La ejecución real solo cubre safe-cleanup y debe usarse con revisión previa del plan.
```

### Siguiente micro-sprint

`POST-H-008-D — Export y redacción de evidencia runtime`.


## 16. Avance de implementación — POST-H-008-D

Estado: `implemented-initial`.

`POST-H-008-D — Export y redacción de evidencia runtime` implementa export local de evidencia runtime con redacción, manifest y checksums. El diseño conserva dry-run por defecto y exige salida explícita bajo `outputs/runtime_exports/` para cualquier ejecución que escriba archivos.

### Implementado

```text
- src/devpilot_core/runtime_state/export.py
- Comando CLI: python -m devpilot_core runtime-state export --dry-run --json
- Ejecución explícita: python -m devpilot_core runtime-state export --execute --output outputs/runtime_exports/<id> --json
- Manifest generado: outputs/runtime_exports/<id>/runtime_state_export_manifest.json
- Checksums generados: outputs/runtime_exports/<id>/checksums.sha256
- Schema: docs/schemas/runtime_state_export_manifest.schema.json
- Tests focales: tests/test_runtime_state_export.py
- Manifest: docs/post_h_008_d_manifest.json
- Auditoría: docs/audits/post_h_008_d_runtime_state_export_report.md
```

### Capacidades adicionadas

```text
- Export plan dry-run sin escritura.
- Export execute con salida explícita gobernada bajo outputs/runtime_exports/.
- Redacción recursiva de JSON/JSONL con SecretGuard.
- Eliminación de campos raw prompt/raw output.
- Metadata-only para `.devpilot/devpilot.db` y payloads binarios no redactables.
- Manifest estructural RuntimeStateExportManifest con checksums SHA-256.
- Registro declarativo de runtime-state.export en CLI registry.
```

### Criterios PASS cubiertos

```text
PASS si export genera manifest y checksums.
PASS si secretos conocidos se redactan.
PASS si no requiere red ni APIs externas.
```

### Límites de esta versión

```text
- No implementa integración automática con auditpack/release.
- No implementa signing/cifrado de export packs.
- No integra todavía runtime-state-hygiene al quality-gate hardening.
- La redacción textual es conservadora y no sustituye un DLP industrial completo.
```

### Siguiente micro-sprint

`POST-H-009-A — Documentation governance canonical source registry`.


## 17. Avance de implementación — POST-H-008-E

Estado: `implemented-initial`.

`POST-H-008-E — Gate de higiene runtime y release archive` implementa el cierre operativo del ciclo runtime-state: el repositorio y los archives de release quedan protegidos contra mezcla accidental de outputs, trazas, SQLite local, agent sessions, caches, builds o dependencias generadas.

### Implementado

```text
- src/devpilot_core/runtime_state/hygiene.py
- Comando CLI: python -m devpilot_core runtime-state hygiene --json
- Reporte opcional: outputs/reports/runtime_state_hygiene_report.json
- Reporte opcional: outputs/reports/runtime_state_hygiene_report.md
- Schema: docs/schemas/runtime_state_hygiene_report.schema.json
- Subgate quality-gate: runtime-state-hygiene en perfiles hardening e industrial
- Tests focales: tests/test_runtime_state_hygiene.py
- Manifest: docs/post_h_008_e_manifest.json
- Auditoría: docs/audits/post_h_008_e_runtime_state_hygiene_report.md
```

### Capacidades adicionadas

```text
- Detección bloqueante de runtime artifacts no versionables rastreados por Git.
- Inspección de git archive HEAD en memoria cuando .git está disponible.
- Fallback determinista de source archive plan para ZIPs limpios sin .git.
- Bloqueo de outputs, devpilot.db, agent_sessions, caches, builds y dependencias en archive.
- Integración con quality-gate hardening/industrial.
- Contrato RuntimeStateHygieneReport y TCR v1/v2.
```

### Criterios PASS cubiertos

```text
PASS si quality-gate detecta runtime artifacts versionados.
PASS si git archive basado en HEAD queda limpio.
PASS si test-contracts validate pasa.
```

### Límites de esta versión

```text
- No firma ni cifra archives.
- No implementa DLP semántico completo.
- No crea release ZIPs; valida higiene de archive en modo read-only.
- En ZIPs sin .git, git archive se reemplaza por un plan determinista equivalente; en checkout Git real sí se inspecciona HEAD.
```

## 18. Cierre del backlog — POST-H-008

Estado: `closed` como baseline `implemented-initial`.

POST-H-008 queda cerrado con las capacidades mínimas requeridas para una política local de runtime state lifecycle:

```text
- POST-H-008-A: taxonomía y RuntimeStatePolicy.
- POST-H-008-B: RuntimeStateInventory read-only.
- POST-H-008-C: cleanup plan dry-run y ejecución segura explícita.
- POST-H-008-D: export redactado, manifest y checksums.
- POST-H-008-E: runtime-state-hygiene en quality gate y release archive hygiene.
```

La solución sigue marcada como `implemented-initial`: signing, cifrado, DLP semántico, rotación avanzada por cuotas y supply-chain release governance quedan para sprints posteriores.
