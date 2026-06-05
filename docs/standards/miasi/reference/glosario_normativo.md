---
title: "Glosario normativo MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
related_docs:
  - "../01_modelo_ingenieria_sistemas_agenticos.md"
  - "../04_estandares_tecnicos_transversales.md"
---
# Glosario normativo MIASI

## 1. Propósito

Definir términos normativos únicos para evitar ambigüedades durante el diseño, implementación, evaluación y operación de sistemas agénticos.

## 2. Reglas de uso

- Los términos de este glosario prevalecen sobre usos informales en notas, conversaciones o laboratorios.
- Todo documento MIASI nuevo debe reutilizar estas definiciones.
- Todo cambio semántico debe registrarse mediante ADR o changelog.

## 3. Términos normativos

| Término | Definición normativa | No debe confundirse con | Control asociado |
|---|---|---|---|
| Agente | Componente que recibe un objetivo, decide pasos, usa modelo o lógica determinística, puede invocar herramientas y produce resultado trazable. | Prompt aislado, script sin decisión, chatbot sin herramientas. | `MIASI-AGT-001` |
| Sistema agéntico | Sistema compuesto por uno o más agentes, herramientas, modelo, memoria, datos, evaluación, seguridad, observabilidad y operación. | Simple wrapper de API LLM. | `MIASI-ARCH-001` |
| Workflow agentic | Flujo de pasos con decisiones condicionadas por estado, herramientas, resultados, políticas o revisión humana. | Pipeline rígido sin decisión. | `MIASI-AGT-002` |
| Copiloto | Asistente que recomienda o ayuda, pero no ejecuta acciones críticas sin decisión humana. | Agente autónomo. | `MIASI-HITL-001` |
| Herramienta | Capacidad invocable por un agente con contrato de entrada, salida, side effects, riesgo y permisos. | Función interna sin contrato. | `MIASI-TOOL-001` |
| Tool Registry | Registro versionado de herramientas disponibles, permisos, contratos, riesgos y validaciones. | Lista informal de funciones. | `MIASI-TOOL-002` |
| Dry-run | Modo que simula o planifica acciones sin efectos secundarios reales. | Ejecución parcial no auditada. | `MIASI-EXEC-001` |
| Execute | Modo que permite efectos reales bajo política, trazabilidad y aprobación cuando aplique. | Ejecución libre. | `MIASI-EXEC-002` |
| Policy gate | Decisión automatizada que permite, bloquea o exige aprobación antes de continuar. | Validación opcional. | `MIASI-POL-001` |
| Human approval | Aprobación humana explícita, trazable y separada del solicitante para acciones críticas. | Confirmación informal por chat. | `MIASI-HITL-002` |
| RAG | Patrón de recuperación y generación con fuentes externas o corpus interno, evidencias y grounding. | Contexto pegado sin trazabilidad. | `MIASI-RAG-001` |
| Memoria | Persistencia de estado, preferencias, hechos o eventos relevantes para ejecuciones futuras. | Historial completo sin curaduría. | `MIASI-MEM-001` |
| Grounding | Grado en que una respuesta se apoya en evidencia recuperada o datos verificables. | Respuesta plausible sin fuente. | `MIASI-EVAL-004` |
| AgentOps | Prácticas de observabilidad, trazabilidad, evaluación, auditoría y operación continua de agentes. | Logging básico. | `MIASI-OBS-001` |
| Baseline local-first | Estado operativo verificable local/offline con tests, trazas, reportes y controles, sin equivaler a producción industrial. | Producción real. | `MIASI-OPS-001` |
| Producción controlada | Entorno real limitado, con usuarios/datos reales acotados, monitoreo, rollback, seguridad y aprobaciones. | Demo o laboratorio. | `MIASI-OPS-002` |
| Producción industrial | Operación real con gobierno completo: IAM/RBAC, SLO/SLA, monitoreo continuo, incidentes, auditoría, compliance y soporte. | Baseline local-first. | `MIASI-OPS-003` |

## 4. Criterios de cumplimiento

- Los documentos y plantillas deben usar estos términos.
- Los nombres alternativos deben registrarse como alias.
- Un término nuevo requiere definición, alcance, exclusiones y control asociado.

## 5. Criterios de bloqueo

- Se bloquea promoción documental si un término crítico se usa de forma contradictoria.
- Se bloquea avance a DevPilot MVP si no existe mapeo entre términos, plantillas y comandos CLI.
