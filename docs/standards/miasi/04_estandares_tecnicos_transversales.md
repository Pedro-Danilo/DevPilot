---
title: "DOC-AI-005 — Estándares técnicos transversales para sistemas agénticos inteligentes"
document_id: "DOC-AI-005"
model: "MIASI — Modelo de Ingeniería de Sistemas Agénticos Inteligentes"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
audience:
  - arquitectos de software
  - ingenieros de agentes IA
  - desarrolladores backend/frontend
  - responsables de seguridad
  - responsables de evaluación y operación
scope: "technical-standards"
doc_type: "reference"
created: "2026-05-31"
updated: "2026-05-31"
related_documents:
  - "docs/engineering_model/01_modelo_ingenieria_sistemas_agenticos.md"
  - "docs/engineering_model/02_arquitectura_referencia.md"
  - "docs/engineering_model/03_agentic_sdlc.md"
traceability:
  labs_range: "LAB-AI-001..LAB-AI-080"
  baseline: "local_first_operational_baseline"
  route: "local-first, multi-modelo, seguro, evaluable y trazable"
---
# DOC-AI-005 — Estándares técnicos transversales para sistemas agénticos inteligentes

## 1. Resumen ejecutivo

Este documento define los estándares técnicos mínimos que todo sistema agéntico del ecosistema **AI_agents / MIASI** debe cumplir para ser diseñado, implementado, evaluado, protegido, observado, desplegado y operado con criterios profesionales.

Su función no es explicar de forma introductoria qué es un agente. Su función es establecer **contratos técnicos reutilizables**. Cada nuevo agente, herramienta, adaptador de modelo, memoria, flujo RAG, evaluación, integración, pipeline o mecanismo de aprobación humana debe poder contrastarse contra estos estándares.

El documento consolida la experiencia acumulada en **LAB-AI-001 a LAB-AI-080** y la traduce en normas técnicas aplicables a proyectos reales como:

- **DevPilot Local**: plataforma agent-assisted SDLC personal.
- **FreelanceOps Agent**: gestión agent-assisted de oportunidades, propuestas, clientes y entregables freelance.
- **MicroVenta Agent**: sistema agent-assisted de ventas e inventario para microemprendimientos.

Estos estándares se diseñan para mantener compatibilidad con tres rutas:

| Ruta | Descripción | Requisito del estándar |
|---|---|---|
| Sin API | Mock agents, reglas, memoria local, RAG lexical, evaluación offline | Debe funcionar sin credenciales reales ni costo externo. |
| Modelos locales | Ollama, LM Studio, modelos open weights | Debe aislar proveedor/modelo mediante `ModelAdapter`. |
| APIs externas controladas | OpenAI, Gemini, Mistral, Hugging Face u otras APIs | Debe exigir API keys opcionales, cost guard, trazas y tests offline. |

> Norma central: ningún agente debe considerarse listo para operación controlada si no declara contrato, herramientas, permisos, política de ejecución, evaluación, trazas, seguridad, manejo de errores y límites de costo.

## 2. Posición dentro de MIASI

Este documento complementa:

| Documento | Rol | Relación con DOC-AI-005 |
|---|---|---|
| `01_modelo_ingenieria_sistemas_agenticos.md` | Documento rector de MIASI | Define principios y niveles de autonomía. |
| `02_arquitectura_referencia.md` | Arquitectura por capas | Define dónde vive cada estándar. |
| `03_agentic_sdlc.md` | Ciclo de vida industrial | Define cuándo se aplica cada estándar. |
| `04_estandares_tecnicos_transversales.md` | Este documento | Define contratos mínimos verificables. |

## 3. Principios normativos

Los estándares se rigen por los siguientes principios:

1. **Contratos antes que implementación**: ningún componente agentic debe implementarse sin contrato mínimo.
2. **Local-first por defecto**: toda capacidad crítica debe tener ruta offline/mock/local.
3. **Multi-modelo por diseño**: el agente no debe depender directamente de un proveedor LLM.
4. **Dry-run por defecto**: toda herramienta con efectos secundarios debe simular antes de ejecutar.
5. **Permisos explícitos**: cada herramienta debe declarar side effects, riesgo y aprobación requerida.
6. **Observabilidad obligatoria**: cada run debe poder reconstruirse mediante logs, trazas y artefactos.
7. **Evaluación antes de promoción**: toda capacidad agentic debe tener pruebas y quality gates.
8. **Seguridad desde el diseño**: secretos, SAST/SBOM, policy-as-code y human approval son controles base.
9. **Costo controlado**: todo uso de API externa debe medir, limitar y reportar consumo.
10. **Documentación ejecutable**: los estándares deben poder convertirse en validadores automáticos.

## 4. Relación con fuentes externas

Estos estándares se alinean con referencias actuales de ingeniería, seguridad, evaluación y operación de sistemas IA:

- OpenAI Agents SDK: agentes, tools, handoffs, guardrails, human review, tracing y estado.
- LangGraph: durable execution, persistence, checkpoints e interrupciones human-in-the-loop.
- MCP: herramientas, prompts y recursos como primitivas para conectar modelos con sistemas externos.
- OpenTelemetry GenAI: convenciones de spans, eventos y métricas para sistemas GenAI/agentes.
- Microsoft Foundry agent evaluators: task completion, task adherence, intent resolution, tool selection y tool call accuracy.
- OWASP LLM Top 10: riesgos específicos de aplicaciones LLM.
- NIST AI RMF / GenAI Profile: gestión de riesgos y trustworthiness.
- NIST SSDF, SLSA y CycloneDX: secure SDLC, supply-chain integrity y SBOM.

## 5. Estándar 1 — Agent Contract

### Propósito

Definir el contrato mínimo de cualquier agente del proyecto, con independencia de si usa reglas, mock model, modelo local o API externa.

### Alcance

Aplica a agentes individuales, agentes especialistas, orquestadores, revisores, ejecutores, agentes RAG, agentes CI/CD, agentes documentales y sistemas multiagente.

### Contrato mínimo

Todo agente debe declarar:

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `agent_id` | Sí | Identificador estable y versionable. |
| `name` | Sí | Nombre legible. |
| `purpose` | Sí | Propósito operacional concreto. |
| `autonomy_level` | Sí | Nivel A0..A7 según MIASI. |
| `model_strategy` | Sí | Mock/local/API/híbrido. |
| `allowed_tools` | Sí | Herramientas autorizadas. |
| `forbidden_tools` | Sí | Herramientas o acciones prohibidas. |
| `memory_policy` | Sí | Sin memoria, memoria local, memoria persistente, memoria vectorial. |
| `rag_policy` | Sí | Sin RAG, RAG lexical, RAG semántico, RAG híbrido. |
| `security_policy` | Sí | Permisos, secretos, aprobación humana, policy-as-code. |
| `eval_policy` | Sí | Evaluaciones mínimas y criterios PASS. |
| `observability_policy` | Sí | Logs, trazas, métricas, artefactos. |
| `cost_policy` | Sí | Presupuesto, límites y fallback. |
| `failure_policy` | Sí | Timeouts, errores, fallback, escalamiento. |
| `owner` | Sí | Responsable técnico. |
| `version` | Sí | Versión SemVer. |

### Formato sugerido

```yaml
agent_id: devpilot.requirements_agent
name: RequirementsAgent
version: 0.1.0
status: draft
autonomy_level: A2
purpose: Convertir solicitudes de usuario en requerimientos, historias y criterios de aceptación.
model_strategy:
  default: mock
  local: ollama
  external_api: optional
allowed_tools:
  - read_project_docs
  - write_requirements_draft
forbidden_tools:
  - delete_files
  - push_to_remote
memory_policy:
  type: sqlite
  pii_allowed: false
rag_policy:
  type: lexical_first
security_policy:
  dry_run_default: true
  approval_required_for_write: true
eval_policy:
  required_tests:
    - requirements_schema_valid
    - acceptance_criteria_present
observability_policy:
  trace_required: true
  log_level: INFO
cost_policy:
  api_budget_usd_per_run: 0.0
failure_policy:
  timeout_seconds: 60
  fallback: produce_blocked_report
owner: AI_agents
```

### Tests mínimos

| Test | Propósito |
|---|---|
| `test_agent_contract_schema` | Verificar campos obligatorios. |
| `test_agent_has_autonomy_level` | Evitar agentes sin nivel de autonomía. |
| `test_agent_tools_are_registered` | Validar que las herramientas existan. |
| `test_agent_policy_has_dry_run` | Asegurar dry-run por defecto. |
| `test_agent_has_eval_policy` | Impedir agentes sin evaluación. |

### Anti-patrones

- Agente definido solo por un prompt.
- Agente sin owner ni versión.
- Agente con herramientas implícitas.
- Agente con memoria no declarada.
- Agente que ejecuta side effects sin política.

### Criterios de cumplimiento

Un agente cumple este estándar si su contrato puede ser validado automáticamente y si ninguna herramienta, modelo, memoria o política crítica queda implícita.

### Criterios de bloqueo

Bloquear si:

- no hay `agent_id`;
- no hay `autonomy_level`;
- no hay política de herramientas;
- no hay política de evaluación;
- ejecuta acciones con side effects sin `dry_run`;
- requiere API externa sin alternativa mock/local.

### Relación con laboratorios AI_agents

| Laboratorios | Aporte al estándar |
|---|---|
| LAB-AI-001..004 | Base de agentes mock/locales y ModelAdapter. |
| LAB-AI-005..016 | RAG, embeddings, vector stores y cache. |
| LAB-AI-017..020 | Memoria, observabilidad, evaluación y seguridad. |
| LAB-AI-021..030 | MCP, multiagentes y repositorios. |
| LAB-AI-075..080 | Seguridad industrial, policy, approval, CI y baseline final. |

## 6. Estándar 2 — ModelAdapter

### Propósito

Desacoplar el agente del proveedor de modelo, permitiendo rutas sin API, modelos locales y APIs externas controladas.

### Alcance

Aplica a generación, clasificación, embeddings, tool calling, structured output y evaluación con jueces.

### Contrato mínimo

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `provider` | Sí | mock, ollama, lmstudio, openai, gemini, mistral, huggingface, custom. |
| `model_name` | Sí | Nombre del modelo o alias local. |
| `capabilities` | Sí | chat, embeddings, tool_calling, json_output, streaming. |
| `requires_api_key` | Sí | Booleano explícito. |
| `cost_policy` | Sí | Presupuesto, límite de tokens, fallback. |
| `timeout_policy` | Sí | Timeout por llamada. |
| `retry_policy` | Sí | Reintentos máximos y backoff. |
| `privacy_policy` | Sí | Qué datos pueden enviarse al proveedor. |
| `trace_policy` | Sí | Qué metadata registrar. |

### Formato sugerido

```yaml
model_adapter:
  provider: ollama
  model_name: qwen2.5:3b-instruct
  requires_api_key: false
  capabilities:
    chat: true
    embeddings: false
    tool_calling: limited
    json_output: best_effort
  cost_policy:
    max_usd_per_run: 0.0
    max_tokens_per_run: 0
  timeout_policy:
    request_timeout_seconds: 60
  retry_policy:
    max_retries: 1
  privacy_policy:
    allow_sensitive_data: false
  trace_policy:
    record_model_name: true
    record_prompts: redacted
```

### Tests mínimos

- Debe existir adaptador mock.
- Todo adaptador API debe fallar de forma controlada si falta API key.
- Ningún test unitario debe requerir credenciales reales.
- Todo adaptador debe reportar provider, modelo, latencia y error.

### Anti-patrones

- Llamar directamente al SDK del proveedor desde el agente.
- Requerir `OPENAI_API_KEY` para ejecutar tests offline.
- No registrar provider/modelo en trazas.
- Mezclar embeddings, chat y tool calling sin contrato.

### Criterios de cumplimiento

El agente debe poder cambiar de proveedor sin reescribir lógica central.

### Criterios de bloqueo

Bloquear si el agente depende directamente de una API externa sin adapter, fallback o tests mock.

### Relación con laboratorios

LAB-AI-002 a LAB-AI-004 establecen la base de ModelAdapter, Ollama y evaluación local. LAB-AI-013 a LAB-AI-015 extienden embeddings y RAG híbrido. LAB-AI-061 a LAB-AI-069 incorporan rutas con APIs externas controladas.

## 7. Estándar 3 — Tool Contract

### Propósito

Definir el contrato mínimo de cada herramienta que un agente puede invocar.

### Alcance

Aplica a herramientas de filesystem, shell, git, base de datos, APIs, RAG, CI/CD, documentación, seguridad, evaluación y despliegue.

### Contrato mínimo

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `tool_id` | Sí | Identificador estable. |
| `name` | Sí | Nombre legible. |
| `description` | Sí | Qué hace y qué no hace. |
| `input_schema` | Sí | JSON Schema o equivalente. |
| `output_schema` | Sí | Salida estructurada. |
| `side_effects` | Sí | none/read/write/network/delete/execute/deploy. |
| `risk_level` | Sí | low/medium/high/critical. |
| `dry_run_supported` | Sí | Booleano. |
| `approval_required` | Sí | Booleano o política. |
| `idempotent` | Sí | Booleano. |
| `timeout_seconds` | Sí | Límite de ejecución. |
| `rollback_strategy` | Sí | Estrategia o `not_supported`. |
| `audit_event` | Sí | Evento observable esperado. |

### Formato sugerido

```yaml
tool_id: filesystem.write_markdown
name: write_markdown_file
description: Escribe un archivo Markdown dentro de rutas permitidas.
input_schema:
  type: object
  required: [path, content, overwrite]
  properties:
    path: {type: string}
    content: {type: string}
    overwrite: {type: boolean}
output_schema:
  type: object
  required: [ok, path, bytes_written, dry_run]
side_effects: write
risk_level: medium
dry_run_supported: true
approval_required: false
idempotent: false
timeout_seconds: 30
rollback_strategy: backup_previous_version
audit_event: tool.filesystem.write_markdown
```

### Tests mínimos

- Schema de entrada valida parámetros requeridos.
- Dry-run no modifica estado.
- Execute solo escribe en rutas permitidas.
- Output nunca expone secretos.
- Error se devuelve estructurado.

### Anti-patrones

- Herramientas sin schema.
- Herramientas que aceptan comandos libres sin allowlist.
- Herramientas que escriben fuera del workspace.
- Herramientas con network access implícito.
- Herramientas que ocultan errores.

### Criterios de cumplimiento

Una herramienta cumple si puede auditarse antes, durante y después de su ejecución.

### Criterios de bloqueo

Bloquear si la herramienta puede borrar, ejecutar comandos, desplegar, enviar red o modificar datos sin política explícita.

### Relación con laboratorios

LAB-AI-001 y LAB-AI-002 introducen tool calling manual. LAB-AI-020, LAB-AI-077 y LAB-AI-078 formalizan guardrails, policy-as-code y aprobación humana.

## 8. Estándar 4 — Tool Registry

### Propósito

Centralizar el catálogo de herramientas permitidas, sus contratos, permisos, riesgos y estados.

### Contrato mínimo

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `registry_version` | Sí | Versión del catálogo. |
| `tools` | Sí | Lista de tool contracts. |
| `default_policy` | Sí | Política por defecto. |
| `allowlist` | Sí | Herramientas permitidas por agente/rol. |
| `denylist` | Sí | Herramientas prohibidas. |
| `approval_rules` | Sí | Reglas de aprobación. |
| `audit_rules` | Sí | Eventos obligatorios. |

### Formato sugerido

```yaml
tool_registry:
  registry_version: 0.1.0
  default_policy:
    unknown_tools: block
    dry_run_default: true
  allowlist:
    devpilot.requirements_agent:
      - docs.read
      - docs.write_draft
  denylist:
    all:
      - shell.raw_execute
      - filesystem.delete_recursive
  approval_rules:
    - when: side_effects in [delete, deploy, execute]
      require: human_approval
```

### Tests mínimos

- No hay herramientas desconocidas en agentes.
- Toda herramienta tiene contrato.
- Las denylist prevalecen sobre allowlist.
- Las herramientas críticas exigen approval.

### Anti-patrones

- Registrar herramientas dinámicamente sin revisión.
- Permitir herramientas por nombre textual generado por LLM.
- No versionar el registry.

### Relación con laboratorios

LAB-AI-020, LAB-AI-021, LAB-AI-077 y LAB-AI-078 son la base del registry gobernado.

## 9. Estándar 5 — Permisos y side effects

### Propósito

Definir cómo se clasifican los efectos de una herramienta o acción agentic.

### Matriz de side effects

| Side effect | Ejemplo | Riesgo base | Control mínimo |
|---|---|---:|---|
| `none` | cálculo local | Bajo | logging básico |
| `read` | leer archivo permitido | Bajo/medio | allowlist de rutas |
| `write` | crear reporte | Medio | dry-run + backup |
| `network` | llamar API externa | Alto | cost guard + redaction + allowlist |
| `execute` | ejecutar comando | Alto/crítico | policy gate + approval |
| `delete` | borrar archivo | Crítico | bloqueo por defecto |
| `deploy` | publicar release | Crítico | approval + CI + rollback |

### Contrato mínimo

Todo side effect debe declarar:

- recurso afectado;
- ambiente;
- reversibilidad;
- aprobación requerida;
- traza esperada;
- rollback;
- owner.

### Tests mínimos

- Acciones destructivas bloqueadas por defecto.
- Acciones write respetan dry-run.
- Acciones network no se ejecutan en tests offline.
- Deploy requiere entorno sandbox/controlado.

### Criterios de bloqueo

Bloquear si el agente intenta ejecutar una acción con side effect no declarado.

## 10. Estándar 6 — Dry-run y execute

### Propósito

Garantizar que toda acción con efectos pueda simularse antes de ejecutarse.

### Regla normativa

> Toda herramienta con `write`, `network`, `execute`, `delete` o `deploy` debe soportar dry-run o estar bloqueada por defecto.

### Contrato mínimo

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `dry_run` | Sí | `true` por defecto. |
| `execute` | Sí | Solo con autorización explícita. |
| `planned_changes` | Sí | Cambios que se aplicarían. |
| `affected_resources` | Sí | Recursos objetivo. |
| `approval_reference` | Condicional | Requerida para acciones críticas. |
| `rollback_plan` | Condicional | Requerido si hay modificación irreversible. |

### Ejemplo de salida

```json
{
  "ok": true,
  "dry_run": true,
  "action": "write_file",
  "planned_changes": ["create docs/devpilot/requirements.md"],
  "affected_resources": ["docs/devpilot/requirements.md"],
  "execute_hint": "rerun with --execute after review"
}
```

### Criterios de bloqueo

Bloquear si un comando cambia estado con `dry_run=true`.

## 11. Estándar 7 — RAG

### Propósito

Establecer condiciones mínimas para agentes que recuperan documentos, contexto o conocimiento externo.

### Contrato mínimo

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `retrieval_mode` | Sí | lexical, semantic, hybrid. |
| `corpus_id` | Sí | Corpus versionado. |
| `chunking_strategy` | Sí | Tamaño, solapamiento, metadatos. |
| `embedding_model` | Condicional | Requerido si hay búsqueda semántica. |
| `ranking_strategy` | Sí | Scoring/reranking. |
| `citation_policy` | Sí | Cuándo y cómo citar. |
| `grounding_policy` | Sí | Qué hacer si no hay evidencia. |
| `freshness_policy` | Sí | Vigencia y staleness. |

### RAG evaluation matrix

| Métrica | Definición | PASS mínimo |
|---|---|---:|
| Retrieval precision | Fragmentos relevantes entre recuperados | >= 0.70 en dataset de prueba |
| Recall operacional | Respuestas con evidencia suficiente | >= 0.70 |
| Groundedness | Respuesta soportada por fuentes | >= 0.80 |
| Citation correctness | Citas apuntan a evidencia real | >= 0.90 |
| Refusal correctness | Rechaza cuando no hay evidencia | >= 0.90 |

### Tests mínimos

- Corpus existe y está versionado.
- Recuperación devuelve metadatos y fuente.
- Respuesta no inventa citas.
- Si no hay evidencia, responde con insuficiencia.

### Anti-patrones

- Meter documentos completos al prompt sin recuperación.
- Responder con RAG sin citar.
- Usar embeddings sin evaluación.
- Mezclar documentos obsoletos con vigentes sin política.

### Relación con laboratorios

LAB-AI-005 a LAB-AI-016 cubren RAG lexical, generativo, embeddings, vector stores, RAG híbrido, cache e indexación incremental.

## 12. Estándar 8 — Memoria

### Propósito

Definir cómo los agentes almacenan, recuperan y gobiernan estado/memoria.

### Memory persistence matrix

| Tipo de memoria | Uso | Persistencia | Riesgo | Control mínimo |
|---|---|---|---:|---|
| Sin memoria | Tareas puramente stateless | Ninguna | Bajo | No aplica |
| Conversacional | Continuidad de sesión | Temporal | Medio | TTL y redaction |
| JSON local | Laboratorios simples | Archivo | Medio | schema + backup |
| SQLite | Historial local | BD local | Medio | migraciones + queries seguras |
| Vectorial | Recuerdo semántico | índice | Alto | grounding + borrado |
| PostgreSQL | Producción controlada | servidor | Alto | RBAC + backups |

### Contrato mínimo

- tipo de memoria;
- datos almacenados;
- datos prohibidos;
- política de retención;
- política de borrado;
- redacción de secretos;
- trazabilidad de writes;
- tests de migración.

### Tests mínimos

- No guarda secretos.
- No guarda PII sin política.
- Puede exportarse/auditarse.
- Soporta limpieza o reset en tests.

### Anti-patrones

- Memoria ilimitada.
- Guardar prompts completos con secretos.
- Usar memoria como fuente de verdad sin validación.
- No diferenciar memoria de conocimiento documental.

### Relación con laboratorios

LAB-AI-017 introduce memoria SQLite; LAB-AI-070 a LAB-AI-074 consolidan histórico AgentOps y persistencia operacional.

## 13. Estándar 9 — Evaluación

### Propósito

Definir evaluación mínima para comportamiento agentic.

### Contrato mínimo

| Evaluación | Requerida para | Métrica |
|---|---|---|
| Unit tests | Todos | Función/componente |
| Tool eval | Agentes con herramientas | tool selection, input accuracy |
| RAG eval | Agentes con RAG | retrieval, groundedness |
| Safety eval | Agentes con acciones | policy compliance |
| Regression eval | Agentes iterativos | no degradación |
| Human review eval | Acciones críticas | aprobación correcta |
| Cost eval | APIs externas | presupuesto por run |

### Eval config example

```yaml
eval:
  eval_id: devpilot_requirements_eval
  target_agent: devpilot.requirements_agent
  dataset: tests/fixtures/requirements_cases.jsonl
  metrics:
    - task_completion
    - task_adherence
    - schema_validity
    - policy_compliance
  pass_thresholds:
    task_completion: 0.85
    schema_validity: 1.0
    policy_compliance: 1.0
```

### Tests mínimos

- Dataset mínimo reproducible.
- Métricas calculables offline.
- Reporte JSON/Markdown.
- Quality gate con PASS/FAIL.

### Anti-patrones

- Evaluar por impresión subjetiva.
- Cambiar prompts sin regression tests.
- No registrar dataset ni versión.
- Usar juez LLM externo como único criterio.

### Relación con laboratorios

LAB-AI-019, LAB-AI-033, LAB-AI-039, LAB-AI-041, LAB-AI-080 consolidan evaluación automatizada y readiness.

## 14. Estándar 10 — Trazas y logs

### Propósito

Garantizar reconstrucción técnica de cada run.

### Contrato mínimo de trace event

```json
{
  "event_type": "agent.tool_call",
  "run_id": "run_20260531_001",
  "agent_id": "devpilot.requirements_agent",
  "timestamp": "2026-05-31T00:00:00Z",
  "span_id": "span_001",
  "parent_span_id": "span_root",
  "model": "mock",
  "tool": "docs.write_draft",
  "dry_run": true,
  "latency_ms": 42,
  "status": "ok",
  "redaction_applied": true
}
```

### Observability event matrix

| Evento | Cuándo emitir | Campos mínimos |
|---|---|---|
| `agent.run.started` | Inicio de run | run_id, agent_id, input_hash |
| `model.request` | Llamada a modelo | provider, model, tokens/cost si aplica |
| `tool.call.proposed` | Antes de tool call | tool_id, args_redacted, risk |
| `tool.call.completed` | Después de tool call | ok, latency, output_hash |
| `policy.decision` | Policy gate | decision, reason, rule_id |
| `approval.requested` | Acción sensible | approval_id, action, risk |
| `eval.completed` | Evaluación | metrics, passed |
| `agent.run.completed` | Fin de run | status, artifacts |

### Tests mínimos

- Todo run tiene `run_id`.
- Tool calls tienen trace event.
- Secretos son redactados.
- Errores se registran con causa estructurada.

### Anti-patrones

- Logs libres sin estructura.
- Registrar API keys o prompts sensibles completos.
- No correlacionar tool calls con run.

### Relación con laboratorios

LAB-AI-018 y LAB-AI-070..074 consolidan observabilidad, OpenTelemetry local, AgentOps histórico y exporters.

## 15. Estándar 11 — Métricas

### Propósito

Definir métricas mínimas de operación y calidad.

### Métricas mínimas

| Categoría | Métricas |
|---|---|
| Rendimiento | latencia, duración, throughput |
| Costo | tokens, USD estimado, llamadas API |
| Calidad | task completion, groundedness, policy compliance |
| Seguridad | findings, blocks, approvals, secrets redacted |
| Herramientas | tool success rate, retries, failures |
| RAG | retrieval precision, citation correctness |
| Operación | incidentes, errores, fallback rate |

### Tests mínimos

- Métricas generables offline.
- Exportables JSON.
- No contienen secretos.
- Incluyen timestamps y run_id.

### Criterios de bloqueo

Bloquear promoción si no hay métricas para decisiones críticas.

## 16. Estándar 12 — Secret management

### Propósito

Evitar exposición de secretos en código, `.env`, logs, reportes, trazas y tests.

### Contrato mínimo

- `.env.example` endurecido;
- variables obligatorias/opcionales/prohibidas;
- redacción automática;
- tests sin tokens reales;
- vault mock/local en capacitación;
- rotación y secret manager real en producción industrial.

### Tests mínimos

- Scanner de `.env` y variantes.
- Detección de patrones peligrosos.
- Redacción en reportes.
- Tests no dependen de credenciales reales.

### Anti-patrones

- Versionar `.env` real.
- Imprimir tokens en logs.
- Usar tokens reales en tests.
- Guardar secretos en memoria persistente sin cifrado.

### Relación con laboratorios

LAB-AI-075 es la base directa de este estándar.

## 17. Estándar 13 — SAST/SBOM

### Propósito

Establecer controles mínimos de análisis estático y cadena de suministro.

### Contrato mínimo

- inventario de dependencias;
- detección de dependencias sin pin;
- SBOM educativo/local como base;
- ruta futura CycloneDX/SPDX formal;
- SAST lexical/AST según madurez;
- quality gates;
- reporte JSON/Markdown.

### Tests mínimos

- Dependencias inventariadas.
- SBOM generado.
- No hay hallazgos críticos bloqueantes.
- Secret management context PASS.

### Anti-patrones

- Ignorar dependencias transitivas.
- No versionar lockfiles.
- Confundir hallazgo lexical con vulnerabilidad confirmada.
- Omitir SBOM antes de producción.

### Relación con laboratorios

LAB-AI-076 define el estándar inicial local-first.

## 18. Estándar 14 — Policy-as-code

### Propósito

Convertir permisos, bloqueos, aprobaciones y restricciones en reglas declarativas evaluables.

### Policy config example

```yaml
policy:
  policy_id: devpilot.default_policy
  default_decision: block
  rules:
    - rule_id: allow_read_only_tools
      when:
        side_effects: read
        environment: [local, test]
      decision: allow
    - rule_id: require_approval_for_write_execute
      when:
        side_effects: [write, execute, deploy]
      decision: require_approval
    - rule_id: block_delete_recursive
      when:
        side_effects: delete
      decision: block
```

### Tests mínimos

- Read-only permitido en local/test.
- Write sin execute requiere dry-run/approval.
- Delete/deploy bloqueados por defecto.
- Producción bloqueada salvo política explícita.

### Anti-patrones

- Permisos hardcodeados dispersos.
- Políticas que no se prueban.
- Allow por defecto.

### Relación con laboratorios

LAB-AI-077 define el patrón policy-as-code.

## 19. Estándar 15 — Human approval

### Propósito

Asegurar revisión humana en acciones críticas.

### Approval request example

```json
{
  "approval_id": "appr_001",
  "run_id": "run_001",
  "agent_id": "devpilot.release_agent",
  "action": "publish_release",
  "risk_level": "critical",
  "requested_by": "agent",
  "reviewer_role_required": "maintainer",
  "ttl_minutes": 60,
  "token_redacted": "appr_***",
  "status": "pending"
}
```

### Tests mínimos

- Solicitante no aprueba su propia acción.
- Approval expira.
- Token redactado.
- Producción/destructivas críticas requieren aprobación.

### Anti-patrones

- Autoaprobar acciones críticas.
- Tokens estáticos.
- Approval sin TTL.
- Ejecutar antes de aprobar.

### Relación con laboratorios

LAB-AI-078 define flujo de aprobación humana asincrónica.

## 20. Estándar 16 — CI/CD

### Propósito

Promover cambios agentic mediante pipelines reproducibles, seguros y auditables.

### CI/CD quality gate matrix

| Gate | Obligatorio | Bloquea si falla |
|---|---:|---:|
| tests unitarios | Sí | Sí |
| agent evals | Sí | Sí |
| secret scan | Sí | Sí |
| SAST/SBOM | Sí | Según severidad |
| policy tests | Sí | Sí |
| docs checks | Recomendado | No inicialmente |
| artifact report | Sí | Sí |
| approval evidence | Para acciones críticas | Sí |

### Tests mínimos

- Pipeline local ejecuta tests.
- Pipeline remoto sandbox no embebe tokens.
- Artefactos se publican en ruta segura.
- Required checks definidos para producción.

### Anti-patrones

- Pipeline que requiere secretos reales en PR.
- Ejecutar deploy desde rama no protegida.
- No publicar reportes.

### Relación con laboratorios

LAB-AI-051..053, LAB-AI-079 y LAB-AI-080 consolidan CI/CD local/remoto sandbox e integración final.

## 21. Estándar 17 — Documentación técnica

### Propósito

Asegurar documentación mínima viva y versionada.

### Contrato mínimo

Todo agente debe tener:

- Agent Card;
- Tool Cards asociadas;
- Eval Plan;
- Risk Register;
- README operativo;
- Runbook si opera fuera de laboratorio;
- ADRs para decisiones relevantes.

### Formato sugerido

Markdown con frontmatter YAML, diagramas Mermaid cuando aplique y referencias explícitas a artefactos ejecutables.

### Tests mínimos

- Documentos existen.
- Frontmatter válido.
- Links internos no rotos.
- Changelog actualizado.

### Anti-patrones

- Documentación separada del repo.
- Diagramas sin relación con código.
- README que no explica ejecución ni validación.

### Relación con laboratorios

DOC-AI-001..004 y LAB-AI-080 establecen documentación como activo operativo.

## 22. Estándar 18 — Errores y fallback

### Propósito

Evitar fallas silenciosas y definir rutas seguras de degradación.

### Contrato mínimo

- errores estructurados;
- códigos de error;
- fallback mock/local;
- retries limitados;
- timeouts;
- circuit breakers para APIs externas;
- reporte bloqueado si no hay seguridad suficiente.

### Incident event example

```json
{
  "incident_id": "inc_001",
  "run_id": "run_001",
  "severity": "medium",
  "component": "model_adapter.openai",
  "error_code": "API_KEY_MISSING",
  "safe_fallback": "mock_model",
  "user_impact": "external generation skipped",
  "status": "mitigated"
}
```

### Tests mínimos

- Falta API key no rompe tests.
- Timeout produce error estructurado.
- Fallback no ejecuta side effects.

### Anti-patrones

- Capturar excepciones y seguir como si nada.
- Reintentos infinitos.
- Fallback que cambia datos.

## 23. Estándar 19 — Costos

### Propósito

Controlar costos de modelos, APIs externas, embeddings, storage y CI.

### Contrato mínimo

- presupuesto por run;
- presupuesto por día/mes;
- límites de tokens;
- límites de requests;
- modo offline en tests;
- reporte de costo estimado;
- fallback local/mock.

### Tests mínimos

- Tests offline no generan costo.
- API externa requiere opt-in.
- Exceso de presupuesto bloquea ejecución.

### Anti-patrones

- Llamadas API en loops autónomos sin límite.
- No medir tokens.
- Usar juez LLM externo en CI sin presupuesto.

## 24. Estándar 20 — Integración con MCP/API/tools

### Propósito

Regular integraciones con sistemas externos mediante MCP, APIs directas o herramientas locales.

### Contrato mínimo

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `integration_id` | Sí | Identificador. |
| `integration_type` | Sí | mcp/api/local_tool. |
| `auth_required` | Sí | Booleano. |
| `network_required` | Sí | Booleano. |
| `allowed_resources` | Sí | Allowlist. |
| `allowed_tools` | Sí | Allowlist. |
| `prompt_injection_controls` | Sí | Sanitización, permisos, boundaries. |
| `audit_events` | Sí | Eventos esperados. |

### Tests mínimos

- No hay herramientas MCP desconocidas.
- Recursos externos están allowlisted.
- Network deshabilitada por defecto en tests.
- Prompt injection no puede elevar permisos.

### Anti-patrones

- Conectar servidores MCP sin allowlist.
- Ejecutar tools remotas sin human approval.
- Confiar en texto externo como instrucción del sistema.

### Relación con laboratorios

LAB-AI-021 y laboratorios MCP posteriores establecen bases; LAB-AI-075..079 agregan controles de seguridad necesarios.

## 25. Tool risk level matrix

| Riesgo | Descripción | Ejemplos | Controles mínimos |
|---|---|---|---|
| Low | Sin side effects o solo cálculo | calculadora, parser local | logging |
| Medium | Lectura/escritura local reversible | generar reporte, leer repo | dry-run, allowlist |
| High | Red, ejecución, BD, cambios no triviales | API externa, SQL write, shell allowlisted | policy gate, approval condicional |
| Critical | Destructivo, deploy, producción, datos sensibles | borrar, migrar, desplegar, pagar | bloqueado por defecto + human approval |

## 26. Agent autonomy matrix

| Nivel | Descripción | Herramientas | Controles requeridos |
|---|---|---|---|
| A0 | Asistente pasivo | Ninguna | disclaimer + logging mínimo |
| A1 | Recomendador | Read-only | trazas + eval básica |
| A2 | Tool dry-run | Simulación | tool contracts + dry-run |
| A3 | Ejecutor controlado | Write local | policy + tests + logs |
| A4 | Aprobación humana | Acciones críticas | human approval + TTL |
| A5 | Operacional local-first | Varias capas | AgentOps + CI + security gates |
| A6 | Producción controlada | Externas/prod | IAM + SRE + monitoreo |
| A7 | Industrial | Multiusuario/empresa | compliance + auditoría fuerte |

## 27. Model provider matrix

| Provider | Ruta | API key | Costo | Uso recomendado | Bloqueo |
|---|---|---:|---:|---|---|
| Mock | Sin API | No | 0 | tests, CI, fallback | Nunca por costo |
| Ollama | Local | No | 0 externo | prototipos locales | si modelo no instalado |
| LM Studio | Local | No | 0 externo | pruebas locales | si endpoint no existe |
| OpenAI | API | Sí | Sí | producción controlada opcional | si no hay budget/API key |
| Gemini | API | Sí | Sí/variable | integración opcional | si no hay opt-in |
| Mistral | API/local | Según ruta | variable | alternativa multi-modelo | si no hay fallback |
| Hugging Face | API/local | Opcional | variable | inferencia/experimentos | si no hay control de costo |

## 28. Security gate matrix

| Gate | Aplica a | PASS | BLOCK |
|---|---|---|---|
| Secret scan | Todo repo | sin secretos reales | secreto real detectado |
| SAST | Código | sin críticos | crítico explotable |
| SBOM | Dependencias | inventario generado | no hay inventario |
| Policy-as-code | Acciones | decisión explícita | acción sin política |
| Human approval | Críticas | aprobación válida | sin aprobación/expirada |
| RAG grounding | Respuestas documentales | citas correctas | respuesta sin evidencia |
| Cost guard | APIs | bajo presupuesto | excede presupuesto |

## 29. Ejemplos reutilizables

### 29.1 Agent Card mínimo

```markdown
---
agent_id: devpilot.code_review_agent
version: 0.1.0
status: draft
autonomy_level: A2
owner: AI_agents
---

# CodeReviewAgent

## Propósito
Revisar cambios de código en modo local-first y producir hallazgos trazables.

## Herramientas permitidas
- git.diff.read
- filesystem.read
- report.write_markdown

## Herramientas prohibidas
- git.push
- shell.raw_execute
- filesystem.delete_recursive

## Evaluación mínima
- Detecta cambios relevantes.
- No modifica archivos en dry-run.
- Produce reporte estructurado.
```

### 29.2 Tool Card mínimo

```markdown
---
tool_id: git.diff.read
version: 0.1.0
risk_level: low
side_effects: read
---

# git.diff.read

Lee el diff local del repositorio. No modifica archivos.

## Input schema
`{ "path": "string", "base": "string" }`

## Output schema
`{ "ok": "boolean", "diff": "string", "files_changed": "array" }`
```

### 29.3 Policy config mínimo

```yaml
policy_id: default_agent_policy
version: 0.1.0
default_decision: block
rules:
  - rule_id: allow_read_only_local
    decision: allow
    when:
      environment: [local, test]
      side_effects: [none, read]
  - rule_id: require_approval_for_write
    decision: require_approval
    when:
      side_effects: [write]
      dry_run: false
  - rule_id: block_critical
    decision: block
    when:
      side_effects: [delete, deploy]
```

## 30. Validadores automáticos futuros

Estos estándares deben convertirse progresivamente en validadores:

```text
validate_agent_contract
validate_model_adapter_config
validate_tool_contract
validate_tool_registry
validate_rag_config
validate_memory_policy
validate_eval_plan
validate_observability_policy
validate_security_gates
validate_ci_cd_gates
```

DevPilot Local debe poder ejecutar esos validadores como parte de sus quality gates.

## 31. Relación global con LAB-AI-001 a LAB-AI-080

| Bloque | Laboratorios | Capacidades convertidas en estándar |
|---|---|---|
| Fundamentos | 001..004 | agentes, tool calling, ModelAdapter |
| RAG y conocimiento | 005..016 | RAG, embeddings, vector stores, cache |
| Estado y calidad | 017..020 | memoria, observabilidad, evaluación, seguridad |
| Integraciones y multiagentes | 021..030 | MCP, handoffs, multiagentes |
| Repositorios y CI | 031..053 | análisis de repos, contract tests, CI/CD |
| Industrialización | 054..074 | APIs controladas, AgentOps, OpenTelemetry, exporters |
| Seguridad industrial | 075..078 | secretos, SAST/SBOM, policy, approval |
| Operación final | 079..080 | CI remoto sandbox, baseline final |

## 32. Criterios de adopción en proyectos aplicados

Un proyecto aplicado puede adoptar DOC-AI-005 si:

- todos sus agentes tienen Agent Card;
- todas sus herramientas tienen Tool Card;
- todo modelo entra por ModelAdapter;
- toda acción con side effects soporta dry-run;
- todo uso de API externa tiene cost guard;
- todo RAG tiene política de grounding;
- toda memoria persistente tiene política de retención;
- toda integración externa tiene allowlist;
- todo agente tiene evaluación mínima;
- todo flujo crítico tiene trazas;
- toda acción crítica requiere policy gate y human approval.

## 33. Checklist mínimo de cumplimiento

| Ítem | PASS |
|---|---:|
| Agent Contract completo | ☐ |
| ModelAdapter definido | ☐ |
| Tool Contracts definidos | ☐ |
| Tool Registry versionado | ☐ |
| Dry-run por defecto | ☐ |
| Política de permisos | ☐ |
| Evaluación offline | ☐ |
| Secret scan | ☐ |
| SAST/SBOM | ☐ |
| Trazas/logs | ☐ |
| Métricas | ☐ |
| Human approval para críticas | ☐ |
| CI/CD con quality gates | ☐ |
| Documentación técnica | ☐ |
| Fallback y errores estructurados | ☐ |
| Cost guard | ☐ |

## 34. Referencias

1. OpenAI. Agents SDK documentation. https://developers.openai.com/api/docs/guides/agents
2. OpenAI. Guardrails and human review. https://developers.openai.com/api/docs/guides/agents/guardrails-approvals
3. LangChain. LangGraph durable execution. https://docs.langchain.com/oss/python/langgraph/durable-execution
4. LangChain. Human-in-the-loop. https://docs.langchain.com/oss/python/langchain/human-in-the-loop
5. Model Context Protocol. Specification. https://modelcontextprotocol.io/specification/2025-06-18
6. Model Context Protocol. Resources. https://modelcontextprotocol.io/specification/2025-06-18/server/resources
7. OpenTelemetry. Semantic conventions for Generative AI systems. https://opentelemetry.io/docs/specs/semconv/gen-ai/
8. OpenTelemetry. Semantic conventions for GenAI agent spans. https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/
9. Microsoft Learn. Agent evaluators. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators
10. OWASP. Top 10 for LLM Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/
11. NIST. AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
12. NIST. Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile. https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
13. NIST. Secure Software Development Framework SP 800-218. https://csrc.nist.gov/pubs/sp/800/218/final
14. SLSA. Supply-chain Levels for Software Artifacts. https://slsa.dev/
15. CycloneDX. Software Bill of Materials standard. https://cyclonedx.org/

## 35. Changelog

| Versión | Fecha | Cambio | Estado |
|---|---|---|---|
| 0.1.0 | 2026-05-31 | Creación inicial de estándares técnicos transversales. | draft |
