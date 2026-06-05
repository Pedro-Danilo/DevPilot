---
title: "Taxonomía de incidentes, SLO/SLA y playbooks mínimos MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
---
# Taxonomía de incidentes, SLO/SLA y playbooks mínimos MIASI

## 1. Propósito

Definir severidades, escalamiento, tiempos objetivo y playbooks mínimos para operación de agentes.

## 2. Severidades

| Severidad | Descripción | Ejemplos | Respuesta objetivo MVP | Bloqueo |
|---|---|---|---|---:|
| SEV-1 | Incidente crítico con daño real o exposición sensible. | Secreto filtrado, acción destructiva ejecutada, datos personales expuestos. | Contención inmediata, desactivar agente. | Sí |
| SEV-2 | Incidente alto sin daño irreversible. | Tool crítica bloqueada, error de policy, outputs inseguros. | Revisar en la misma jornada. | Sí para release |
| SEV-3 | Degradación funcional. | Eval regression, RAG sin citas, latencia alta. | Priorizar en backlog. | No siempre |
| SEV-4 | Incidente menor/documental. | Link roto, typo, warning no crítico. | Corregir en mantenimiento. | No |

## 3. SLO/SLA iniciales por fase

| Fase | SLO/SLA mínimo |
|---|---|
| Laboratorio | Tests reproducibles, trazas generadas, sin secretos. |
| MVP local | 95% comandos core ejecutan sin fallo en entorno controlado. |
| Beta personal | 99% de acciones read-only exitosas; 0 acciones críticas sin approval. |
| Producción controlada | SLO por endpoint/comando, alertas y rollback documentado. |
| Industrial | SLO/SLA formal por servicio, soporte, escalamiento y error budget. |

## 4. Playbooks mínimos

| Incidente | Acción inmediata | Evidencia | Seguimiento |
|---|---|---|---|
| Secreto detectado | Revocar/rotar, limpiar logs, bloquear release. | Security report. | Postmortem. |
| Acción destructiva no aprobada | Detener agente, restaurar backup, revisar policy. | Trace + policy log. | Patch gate. |
| Prompt injection exitosa | Aislar corpus/input, reforzar filtros, reevaluar. | Eval report. | Dataset adversarial. |
| RAG con respuesta no grounded | Bloquear fuente, reindexar, ajustar eval. | Retrieval logs. | Regression test. |
| CI/CD fallido | Bloquear merge/release. | CI logs. | Fix + rerun. |

## 5. Criterios de bloqueo

- Todo SEV-1 bloquea operación.
- Todo incidente de secreto bloquea release hasta remediación.
- Toda acción crítica sin approval se considera SEV-1 o SEV-2.
- Un agente sin runbook no puede pasar a A5+.
