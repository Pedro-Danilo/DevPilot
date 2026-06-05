---
title: "Manifiesto MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model"
updated: "2026-05-31"
doc_type: "explanation"
audience:
  - "equipo AI_agents"
  - "arquitectos y desarrolladores de agentes IA"
related_labs:
  - "LAB-AI-001..LAB-AI-080"
---
# Manifiesto MIASI

## 1. Declaración central

MIASI existe para convertir la experiencia acumulada en **AI_agents LAB-AI-001 a LAB-AI-080** en un modelo profesional de ingeniería de sistemas agénticos inteligentes. Su propósito es evitar que la construcción de agentes reales dependa de improvisación, prompts aislados, scripts sin control, integraciones frágiles o proveedores únicos.

Un sistema agéntico profesional debe diseñarse como software crítico: con arquitectura explícita, límites de autonomía, contratos de herramientas, evaluación, trazabilidad, seguridad, gobierno de datos, control de costos y operación verificable.

## 2. Principios no negociables

### 2.1 Local-first por defecto

Todo sistema debe funcionar en una ruta local o offline siempre que sea razonable. Las APIs externas son rutas opcionales, no requisitos para pasar pruebas básicas.

### 2.2 Multi-modelo por diseño

Ningún agente debe quedar acoplado de forma irreversible a un único proveedor LLM. Todo agente que use modelos debe comunicarse mediante una capa de adaptación.

### 2.3 API keys opcionales y seguras

Las claves de proveedores externos no deben ser requeridas para tests offline, no deben versionarse y no deben aparecer en logs, reportes, trazas o ejemplos.

### 2.4 Dry-run por defecto

Toda acción con efectos secundarios debe ejecutarse primero en modo simulación. El paso a ejecución real requiere intención explícita, policy gate y, si aplica, aprobación humana.

### 2.5 Herramientas con contrato explícito

Toda herramienta debe declarar entradas, salidas, side effects, riesgo, permisos, idempotencia, errores esperados, timeout y modo dry-run.

### 2.6 Seguridad desde el diseño

La seguridad no se agrega al final. Debe incorporarse desde el diseño de agente, herramienta, memoria, RAG, integración, despliegue y operación.

### 2.7 Evaluación antes de promoción

Ningún agente debe promoverse a operación controlada sin evaluación mínima de tarea, selección de herramientas, precisión de tool calls, seguridad, trazabilidad y regresión.

### 2.8 Observabilidad obligatoria

Todo agente operacional debe producir logs, trazas y reportes suficientes para reconstruir qué hizo, por qué lo hizo, qué herramientas usó, qué política aplicó y qué resultado obtuvo.

### 2.9 Human-in-the-loop para acciones críticas

Acciones destructivas, costosas, externas, sensibles o de producción requieren revisión humana o política equivalente antes de ejecutarse.

### 2.10 Documentación como activo operativo

La documentación no es un subproducto. Es parte del sistema. Cada agente debe tener Agent Card, Tool Cards, Eval Plan, Risk Register y Runbook cuando corresponda.

## 3. Distinción fundamental

| Categoría | Definición | Nivel esperado |
|---|---|---|
| Laboratorio | Ejercicio controlado para aprender o validar una capacidad. | Educativo. |
| Baseline local-first | Sistema integrado, trazable y evaluado localmente. | Operacional local. |
| Producción controlada | Sistema desplegado con usuarios reales, monitoreo, seguridad, CI/CD y soporte. | Profesional. |
| Producción industrial | Sistema con SLO/SLA, IAM, auditoría fuerte, cumplimiento, incident response, gobernanza y operación continua. | Industrial. |

## 4. Mínimo ético y técnico

MIASI no debe usarse para construir agentes opacos, inseguros o sin control humano cuando existan efectos relevantes sobre datos, dinero, reputación, clientes, infraestructura o decisiones sensibles.

## 5. Regla de diseño operacional

```text
Primero simular.
Luego evaluar.
Después trazar.
Luego aprobar.
Solo entonces ejecutar.
```

## 6. Reglas de bloqueo

Un agente no puede pasar a operación controlada si:

- no tiene propósito explícito;
- no declara límites de autonomía;
- no tiene pruebas mínimas;
- no registra trazas;
- no aplica policy gates;
- expone secretos;
- ejecuta herramientas sin contrato;
- depende de credenciales reales para pruebas;
- realiza acciones destructivas sin aprobación;
- no tiene estrategia de fallback;
- no diferencia outputs generados, verificados y aprobados.

## 7. Relación con estándares externos

MIASI se inspira en marcos reconocidos, pero no pretende reemplazarlos. Integra prácticas de gestión de riesgos de IA, sistemas de gestión de IA, seguridad de aplicaciones LLM, observabilidad GenAI, documentación de arquitectura y supply chain security.


## Referencias externas base

- ISO/IEC 42001:2023 — Artificial intelligence management systems. https://www.iso.org/standard/42001
- NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI 600-1 — Generative AI Profile. https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- OWASP Top 10 for Large Language Model Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OpenTelemetry Semantic conventions for generative AI systems. https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Model Context Protocol Specification. https://modelcontextprotocol.io/specification/2025-06-18
- OpenAI Agents SDK — Agents, handoffs, guardrails and human review. https://developers.openai.com/api/docs/guides/agents
- LangGraph durable execution and persistence. https://docs.langchain.com/oss/python/langgraph/durable-execution
- Microsoft Foundry Agent Evaluators. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators
- arc42 Architecture Documentation. https://arc42.org/
- C4 Model. https://c4model.com/
- Diátaxis documentation framework. https://diataxis.fr/
- NIST SP 800-218 Secure Software Development Framework. https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA — Supply-chain Levels for Software Artifacts. https://slsa.dev/
- OWASP CycloneDX. https://cyclonedx.org/
