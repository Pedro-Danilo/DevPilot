# Registro de riesgos de seguridad, operación y compliance post-H

## 1. Propósito

Este documento implementa el micro-sprint `POST-H-EVAL-001-D — Registro de riesgos de seguridad, operación y compliance` del hito `POST-H-EVAL-001 — Evaluación integral del baseline DevPilot post-Fase H`.

Su propósito es convertir los hallazgos de los micro-sprints A, B y C en un **risk register industrial accionable**. No introduce nuevas capacidades runtime; no habilita ejecución remota; no habilita conectores write; no ejecuta plugins; no declara cumplimiento normativo certificado.

Este registro debe guiar la priorización de los siguientes sprints post-H, especialmente antes de ampliar autonomía, conectividad, operación enterprise, UI/API, audit packs o compliance packs.

## 2. Alcance

Incluido:

- Riesgos de seguridad local-first.
- Riesgos de operación y distribución.
- Riesgos de compliance overclaiming.
- Riesgos de conectores, plugins, RAG, UI/API, remote runner y observabilidad.
- Criterios de cierre por riesgo.
- Sprint recomendado para mitigación.

Excluido:

- Implementación de mitigaciones runtime.
- Activación de remote execution.
- Conectores write-enabled.
- Plugin execution.
- Cambios en PolicyEngine, agentes, API o UI.
- Certificación de compliance.

## 3. Fuentes de evidencia

| Fuente | Rol dentro del risk register |
|---|---|
| `docs/POST-H-EVAL-001_backlog_ejecutable.md` | Define criterios PASS/BLOCK de D. |
| `docs/audits/post_h_eval_001_baseline_assessment.md` | Baseline, snapshot y hallazgos acumulados. |
| `.devpilot/evals/post_h_eval_001_decision_matrix.json` | Matriz de madurez y prioridades de B. |
| `docs/02_architecture/post_h_current_architecture_map.md` | Mapa arquitectónico y riesgos de acoplamiento de C. |
| `.devpilot/remote/runner_registry.json` | Evidencia de remote runner experimental/disabled. |
| `.devpilot/connectors/connector_registry.json` | Evidencia de conectores read-only/deny-by-default. |
| `.devpilot/plugins/plugin_registry.json` | Evidencia de plugins metadata-only/no executable loading. |
| `.devpilot/identity/identity_registry.json` | Evidencia RBAC/actores locales. |
| `.devpilot/miasi/tool_registry.json` | Evidencia de herramientas y risk levels. |
| `.devpilot/miasi/policy_matrix.json` | Evidencia de reglas, default effects y approval gates. |
| `.devpilot/rag/docs_index.json` | Evidencia de RAG local, SecretGuard y redacciones. |

## 4. Resumen ejecutivo

DevPilot tiene un baseline industrial local-first razonablemente gobernado, pero su evolución segura exige no confundir **madurez local** con **madurez enterprise/remota**.

Resumen del registro:

| Métrica | Valor |
|---|---:|
| Riesgos registrados | 14 |
| Riesgos críticos | 1 |
| Riesgos altos | 8 |
| Riesgos media-alta | 1 |
| Riesgos medios | 4 |
| Riesgos P0 | 6 |
| Riesgos P1 | 7 |
| Riesgos P2 | 1 |

Límites de seguridad confirmados:

```text
Remote execution: no habilitada.
Connector write: bloqueado por defecto.
Plugin execution: bloqueado hasta sandbox.
Compliance: evidencia local, no certificación.
Runtime artifacts: riesgo explícito de distribución.
Secret leakage: riesgo explícito, con SecretGuard como mitigación inicial.
```

## 5. Matriz resumida de riesgos

| ID | Riesgo | Severidad | Probabilidad | Prioridad | Estado |
|---|---|---:|---:|---:|---|
| SEC-001 | Activación prematura de remote execution | Crítica | Media | P0 | open-blocking-for-remote |
| SEC-002 | Connector write accidental | Alta | Media | P0 | open-blocking-for-write-connectors |
| SEC-003 | Plugin execution insegura | Alta | Media | P0 | open-blocking-for-plugin-execution |
| SEC-004 | Actor spoofing local | Alta | Media | P1 | open |
| SEC-005 | Runtime artifacts en ZIP/audit packs | Alta | Media | P0 | open |
| SEC-006 | Secret leakage | Alta | Media | P0 | open |
| SEC-007 | UI/API sin auth robusta | Media-alta | Media | P1 | open |
| SEC-008 | Retención indefinida de traces | Media | Alta | P1 | open |
| SEC-009 | Sobreclaiming compliance | Media | Media | P2 | open |
| SEC-010 | RAG sin groundedness robusto | Media | Media | P1 | open |
| SEC-011 | Bypass de aprobación humana en acciones críticas | Alta | Media | P0 | open |
| SEC-012 | Path traversal o mutación fuera de workspace permitido | Alta | Baja-media | P1 | open |
| SEC-013 | Prompt/tool injection en agentes con herramientas | Alta | Media | P1 | open |
| SEC-014 | Confianza excesiva en evals deterministas | Media | Media | P1 | open |

## 6. Registro detallado de riesgos

## SEC-001 — Activación prematura de remote execution

- Severidad: **Crítica**
- Probabilidad: Media
- Impacto: Ejecución remota fuera de control, posible uso de shell, credenciales o red sin threat model completo.
- Estado actual: Remote runner registrado como implemented-initial / experimental=True; remote_runner_enabled=False; execution_allowed=False.
- Evidencia:
  - `.devpilot/remote/runner_registry.json`
  - `docs/02_architecture/post_h_current_architecture_map.md`
  - `src/devpilot_core/remote`
- Mitigación: Mantener remote execution disabled. Exigir ADR, threat model, sandbox, autenticación, transporte seguro, aprobación humana, evals adversariales y observabilidad antes de cualquier enablement.
- Criterio de cierre: Un ADR futuro prueba que remote execution sigue disabled por defecto y que cualquier modo execute tiene RBAC, approval, sandbox, audit trail, tests replay y kill switch.
- Sprint recomendado: `POST-H-021 — Remote Runner ADR-2`
- Prioridad: `P0`
- Estado: `open-blocking-for-remote`

## SEC-002 — Connector write accidental

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Un conector podría mutar archivos, repositorios, servicios o sistemas externos sin contrato de seguridad write-safe.
- Estado actual: Connector registry aprobado con 4 conectores, defaults deny-by-default, require_approval_for_execution=True, connector_execution_performed=False.
- Evidencia:
  - `.devpilot/connectors/connector_registry.json`
  - `src/devpilot_core/connectors`
  - `.devpilot/miasi/policy_matrix.json`
- Mitigación: Mantener conectores read-only/metadata-only. Cualquier write connector requiere policy rule específica, dry-run, replay tests, idempotency, rollback y aprobación humana.
- Criterio de cierre: Existe suite de replay tests para conectores write, deny-by-default comprobado y registro de aprobación/auditoría por cada mutación.
- Sprint recomendado: `POST-H-018 — Connector sandbox avanzado`
- Prioridad: `P0`
- Estado: `open-blocking-for-write-connectors`

## SEC-003 — Plugin execution insegura

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Carga o ejecución de código arbitrario desde plugins sin aislamiento podría romper PathGuard, SecretGuard o límites de permisos.
- Estado actual: Plugin registry aprobado con 2 plugins; executable_loading_default=False; plugin_code_loaded=False; arbitrary_code_execution_performed=False.
- Evidencia:
  - `.devpilot/plugins/plugin_registry.json`
  - `src/devpilot_core/plugins`
  - `.devpilot/miasi/tool_registry.json`
- Mitigación: Mantener plugins como metadata/manifest-only hasta diseñar sandbox, permisos, firma, allowlist, evaluación y observabilidad.
- Criterio de cierre: Plugin execution queda bloqueado por defecto y un futuro sandbox prueba aislamiento de filesystem, red, secretos, shell y permisos.
- Sprint recomendado: `POST-H-019 — Plugin sandbox design sin ejecución arbitraria`
- Prioridad: `P0`
- Estado: `open-blocking-for-plugin-execution`

## SEC-004 — Actor spoofing local

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Un actor local podría asumir identidad/rol operativo sin garantías de sesión, autenticación fuerte o separación de contexto.
- Estado actual: Identity registry local con 6 roles y 2 actores; active_actor_id=local-owner; remote_auth_used=False; credentials_stored=False.
- Evidencia:
  - `.devpilot/identity/identity_registry.json`
  - `src/devpilot_core/identity`
  - `src/devpilot_core/approval`
- Mitigación: Fortalecer RBAC/Approval con actor binding, session boundary, trazabilidad de approval_id y pruebas negativas por rol.
- Criterio de cierre: Tests cubren actor spoofing, rol inválido, aprobación caducada, aprobación reutilizada y ejecución crítica sin actor autorizado.
- Sprint recomendado: `POST-H-012 — Approval/RBAC hardening`
- Prioridad: `P1`
- Estado: `open`

## SEC-005 — Runtime artifacts en ZIP/audit packs

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Distribuir ZIPs o audit packs con bases locales, sesiones, outputs o logs puede filtrar evidencia operativa, rutas, estados o datos sensibles.
- Estado actual: La higiene Git fue corregida en micro-sprints previos; el riesgo permanece para exports manuales, audit packs y fuentes ZIP regeneradas fuera de git archive.
- Evidencia:
  - `.gitignore`
  - `docs/audits/post_h_eval_001_baseline_assessment.md`
  - `docs/02_architecture/post_h_current_architecture_map.md`
- Mitigación: Usar git archive como fuente de verdad; mantener outputs/, .devpilot/devpilot.db, .devpilot/agent_sessions/, logs y caches fuera de Git y fuera de paquetes exportables.
- Criterio de cierre: Existe export policy automatizada que falla si ZIP/audit pack contiene outputs, devpilot.db, agent_sessions, logs, caches, .venv o node_modules.
- Sprint recomendado: `Repo hygiene final / POST-H-017 — Release reproducibility pack`
- Prioridad: `P0`
- Estado: `open`

## SEC-006 — Secret leakage

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Secretos, tokens o credenciales podrían filtrarse en docs, RAG index, reports, traces, providers o logs.
- Estado actual: RAG index local reporta SecretGuard activo, raw_secrets_stored=false y redactions_total=82; aun así hay 2876 chunks indexados y múltiples flujos de reporte/traza.
- Evidencia:
  - `.devpilot/rag/docs_index.json`
  - `src/devpilot_core/security`
  - `src/devpilot_core/rag`
  - `docs/03_security/security_threat_model.md`
- Mitigación: Mantener SecretGuard en rutas de indexación/reportes/trazas; agregar scans pre-export y pruebas con fixtures de secretos sintéticos.
- Criterio de cierre: Los exports, RAG index, reports y audit packs fallan ante secretos sintéticos no redactados; proveedores reales nunca se versionan.
- Sprint recomendado: `POST-H-012 — Approval/RBAC hardening + SecretGuard export checks`
- Prioridad: `P0`
- Estado: `open`

## SEC-007 — UI/API sin auth robusta

- Severidad: **Media-alta**
- Probabilidad: Media
- Impacto: API/UI local implemented-initial podría ser usada más allá del entorno local sin hardening de sesión, token, CORS, rate limiting y auditoría.
- Estado actual: API local declara token requerido y CORS restringido, pero el producto sigue en madurez implemented-initial y no debe asumirse como plataforma multiusuario.
- Evidencia:
  - `src/devpilot_core/interfaces/api`
  - `docs/07_interfaces/openapi_v1.json`
  - `ui/web`
  - `docs/02_architecture/post_h_current_architecture_map.md`
- Mitigación: Mantener host local por defecto, documentar no-exposición a red, fortalecer session/token hardening, logs de acceso y pruebas negativas.
- Criterio de cierre: API/UI tiene tests de auth negativa, CORS, token rotation/manual, session expiry y límites de exposición local.
- Sprint recomendado: `POST-H-014 — UI/API industrial shell`
- Prioridad: `P1`
- Estado: `open`

## SEC-008 — Retención indefinida de traces

- Severidad: **Media**
- Probabilidad: Alta
- Impacto: Trazas, reportes y sesiones pueden acumular información operativa, rutas locales, decisiones, prompts o resultados sensibles.
- Estado actual: Observabilidad existe en modo local; todavía falta política productiva de retención, rotación, minimización y borrado seguro.
- Evidencia:
  - `src/devpilot_core/observability`
  - `docs/05_operations/observability_plan.md`
  - `.devpilot/rag/docs_index.json`
- Mitigación: Definir retention policy local con TTL, clasificación de evidencia, rotación, purge controlado y exclusión de secretos.
- Criterio de cierre: Existe política y tests de retención que prueban qué se conserva, qué se purga y qué nunca se serializa.
- Sprint recomendado: `POST-H-010 — Observability retention local`
- Prioridad: `P1`
- Estado: `open`

## SEC-009 — Sobreclaiming compliance

- Severidad: **Media**
- Probabilidad: Media
- Impacto: El proyecto podría presentar compliance packs como certificación real, aunque hoy son checks locales/read-only y no equivalen a cumplimiento normativo certificado.
- Estado actual: Compliance registry local-first con packs_total=1; declared_checks_only=None.
- Evidencia:
  - `.devpilot/compliance/packs.json`
  - `src/devpilot_core/compliance`
  - `docs/02_architecture/post_h_current_architecture_map.md`
- Mitigación: Etiquetar compliance packs como evidencia local no certificada; prohibir claims de auditoría/certificación externa sin proceso formal.
- Criterio de cierre: Docs, reports y dashboard distinguen compliance-evidence local de compliance-certification externa.
- Sprint recomendado: `POST-H-020 — Compliance mapping packs ampliados`
- Prioridad: `P2`
- Estado: `open`

## SEC-010 — RAG sin groundedness robusto

- Severidad: **Media**
- Probabilidad: Media
- Impacto: El RAG lexical puede recuperar evidencia útil pero no garantiza relevancia semántica, reranking, groundedness ni detección fuerte de respuestas no sustentadas.
- Estado actual: RAG local lexical con chunks_total=2876, embeddings_enabled=False, llm_used=False.
- Evidencia:
  - `src/devpilot_core/rag`
  - `.devpilot/rag/docs_index.json`
  - `docs/audits/post_h_eval_001_baseline_assessment.md`
- Mitigación: Agregar evals de groundedness, citas obligatorias, recuperación semántica opcional/local, reranking y negative cases.
- Criterio de cierre: RAG responde con evidencia trazable y falla de forma segura cuando no hay soporte documental suficiente.
- Sprint recomendado: `POST-H-011 — RAG groundedness evals`
- Prioridad: `P1`
- Estado: `open`

## SEC-011 — Bypass de aprobación humana en acciones críticas

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Herramientas de alto riesgo podrían ejecutarse sin approval_id válido o con aprobación reutilizada si los contratos no se endurecen.
- Estado actual: MIASI registra 97 tools, 28 high-risk tools y 20 reglas approval-gated sobre 97 reglas de política.
- Evidencia:
  - `.devpilot/miasi/tool_registry.json`
  - `.devpilot/miasi/policy_matrix.json`
  - `src/devpilot_core/approval`
- Mitigación: Tests negativos por herramienta crítica, approval_id único, expiración, actor binding y replay de intento sin aprobación.
- Criterio de cierre: Toda acción destructiva o de alto riesgo queda bloqueada sin aprobación explícita y trazable.
- Sprint recomendado: `POST-H-012 — Approval/RBAC hardening`
- Prioridad: `P0`
- Estado: `open`

## SEC-012 — Path traversal o mutación fuera de workspace permitido

- Severidad: **Alta**
- Probabilidad: Baja-media
- Impacto: Un agente o herramienta local podría leer o mutar rutas fuera del workspace si PathGuard no cubre nuevos flujos.
- Estado actual: PathGuard existe y quality gates reportan uso de policy/security; el riesgo crece al agregar nuevas herramientas o conectores.
- Evidencia:
  - `src/devpilot_core/security`
  - `src/devpilot_core/sandbox`
  - `.devpilot/workspaces/workspace_registry.json`
- Mitigación: Mantener allowlist de rutas, pruebas de traversal, ejecución en sandbox y deny-by-default en herramientas nuevas.
- Criterio de cierre: Cada herramienta con filesystem tiene pruebas de path traversal y bloqueo fuera de workspace.
- Sprint recomendado: `POST-H-004 — Policy/MIASI semantic validator ampliado`
- Prioridad: `P1`
- Estado: `open`

## SEC-013 — Prompt/tool injection en agentes con herramientas

- Severidad: **Alta**
- Probabilidad: Media
- Impacto: Contenido documental, prompts o entradas de usuario podrían inducir herramientas no autorizadas o saltos de política.
- Estado actual: Existen PromptInjectionGuard y ToolInjectionGuard en PolicyEngine, pero el riesgo aumenta con RAG, plugins y conectores externos futuros.
- Evidencia:
  - `src/devpilot_core/policy`
  - `src/devpilot_core/security`
  - `src/devpilot_core/agents`
  - `.devpilot/miasi/policy_matrix.json`
- Mitigación: Fortalecer fixtures adversariales, separación instruction/data, tool allowlist por contexto y evaluación de prompt injection antes de tool execution.
- Criterio de cierre: Evals adversariales prueban que contenido recuperado o input externo no puede elevar permisos ni habilitar herramientas fuera de policy.
- Sprint recomendado: `POST-H-004 — Policy/MIASI semantic validator ampliado`
- Prioridad: `P1`
- Estado: `open`

## SEC-014 — Confianza excesiva en evals deterministas

- Severidad: **Media**
- Probabilidad: Media
- Impacto: Scores 100% en suites locales pueden generar falsa sensación de cobertura si no incluyen datasets reales, casos adversariales amplios o regresión por impacto.
- Estado actual: Advanced evals safety pasa en modo determinista/local; sigue siendo preliminary y sin LLM judge ni datasets externos.
- Evidencia:
  - `evals/fixtures`
  - `src/devpilot_core/evals`
  - `docs/04_quality/test_strategy.md`
- Mitigación: Evolucionar test contracts por criticidad, ampliar datasets locales, agregar mutation/negative tests y reportar cobertura semántica explícita.
- Criterio de cierre: El dashboard distingue pass determinista de cobertura real y enlaza brechas conocidas por dominio.
- Sprint recomendado: `POST-H-003 — Test Contract Registry 2.0`
- Prioridad: `P1`
- Estado: `open`


## 7. Riesgos por prioridad

### P0 — Bloqueantes para ampliar autonomía o superficie de ejecución

- `SEC-001` — Remote execution.
- `SEC-002` — Connector write accidental.
- `SEC-003` — Plugin execution insegura.
- `SEC-005` — Runtime artifacts en ZIP/audit packs.
- `SEC-006` — Secret leakage.
- `SEC-011` — Bypass de aprobación humana.

### P1 — Hardening requerido antes de productización amplia

- `SEC-004` — Actor spoofing local.
- `SEC-007` — UI/API sin auth robusta.
- `SEC-008` — Retención indefinida de traces.
- `SEC-010` — RAG sin groundedness robusto.
- `SEC-012` — Path traversal o mutación fuera de workspace.
- `SEC-013` — Prompt/tool injection.
- `SEC-014` — Confianza excesiva en evals deterministas.

### P2 — Riesgos de reporting/compliance y expansión posterior

- `SEC-009` — Sobreclaiming compliance.

## 8. Mapeo hacia roadmap post-H

| Riesgo | Sprint recomendado | Motivo |
|---|---|---|
| `SEC-001` | `POST-H-021` | Remote runner requiere ADR-2 antes de cualquier enablement. |
| `SEC-002` | `POST-H-018` | Conectores write requieren sandbox, replay tests y approvals. |
| `SEC-003` | `POST-H-019` | Plugin execution requiere sandbox y permisos. |
| `SEC-004`, `SEC-011` | `POST-H-012` | RBAC/Approval deben endurecerse antes de acciones críticas. |
| `SEC-005` | `POST-H-017` | Release/audit packs deben ser reproducibles y limpios. |
| `SEC-006` | `POST-H-012` | SecretGuard debe cubrir exports, traces y reports. |
| `SEC-007` | `POST-H-014` | UI/API requiere shell industrial local antes de ampliar uso. |
| `SEC-008` | `POST-H-010` | Observabilidad necesita retención y minimización. |
| `SEC-009` | `POST-H-020` | Compliance packs deben evitar claims de certificación. |
| `SEC-010` | `POST-H-011` | RAG requiere groundedness evals. |
| `SEC-012`, `SEC-013` | `POST-H-004` | Policy/MIASI semantic validator debe ampliar pruebas de seguridad. |
| `SEC-014` | `POST-H-003` | Test Contract Registry 2.0 debe distinguir score local de cobertura real. |

## 9. Decisiones de seguridad derivadas

### DEC-D-001 — Remote execution sigue bloqueado

`remote execution` no puede activarse desde `POST-H-EVAL-001` ni desde `POST-H-002`. Cualquier activación futura requiere ADR, threat model, sandbox, approval, auth, observability y evals.

### DEC-D-002 — Write connectors no se habilitan por acumulación incremental

Los conectores existentes siguen en modo read-only/deny-by-default. Un conector write requiere sprint específico, contrato de idempotencia, replay tests, rollback y aprobación humana.

### DEC-D-003 — Plugins siguen metadata-only

La existencia de un plugin registry no autoriza carga ni ejecución de código. Plugin execution queda bloqueado hasta diseño formal de sandbox.

### DEC-D-004 — Compliance packs son evidencia local, no certificación

DevPilot puede generar evidencia local de compliance, pero no debe declarar certificación ni cumplimiento externo sin proceso formal.

### DEC-D-005 — Export hygiene es control de seguridad, no solo limpieza operativa

`git archive` y exclusión de runtime artifacts se consideran controles de seguridad para evitar filtración de estado local.

## 10. Criterios PASS/BLOCK de este micro-sprint

### PASS

```text
PASS si hay al menos 10 riesgos.
PASS si remote execution queda como riesgo crítico.
PASS si connectors write queda bloqueado por defecto.
PASS si plugin execution queda bloqueado hasta sandbox.
PASS si runtime artifacts quedan como riesgo de distribución.
PASS si secret leakage queda documentado y asociado a SecretGuard/export checks.
PASS si compliance se declara evidencia local no certificada.
```

### BLOCK

```text
BLOCK si se permite remote execution real.
BLOCK si se propone write connector sin nueva ADR/sandbox/tests.
BLOCK si se declara compliance certificada.
BLOCK si se ignora secret leakage.
BLOCK si se omite runtime artifact leakage.
```

## 11. Relación con POST-H-002

El dashboard de madurez `POST-H-002` debe consumir este risk register como fuente para mostrar:

- Riesgos por severidad.
- Riesgos por prioridad.
- Riesgos bloqueantes para remote/connectors/plugins.
- Riesgos de distribución y compliance.
- Mitigaciones pendientes por sprint.

`POST-H-002` no debe convertir estos riesgos en indicadores ornamentales. Debe exponerlos como restricciones operativas del baseline DevPilot post-H.

## 12. Estado final del micro-sprint D

```text
Micro-sprint: POST-H-EVAL-001-D
Estado: implemented
Mutaciones runtime: ninguna
Remote execution: no habilitada
Connector write: no habilitado
Plugin execution: no habilitada
Compliance certification: no declarada
Siguiente micro-sprint: POST-H-EVAL-001-E — Evaluación de testing, costos y contratos
```
