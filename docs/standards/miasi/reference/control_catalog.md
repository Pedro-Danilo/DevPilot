---
title: "Catálogo de controles MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
---
# Catálogo de controles MIASI

## 1. Propósito

Crear identificadores únicos para controles de diseño, seguridad, evaluación, observabilidad, operación y documentación. Estos IDs serán usados por plantillas, checklists, DevPilot Local y futuros validadores.

## 2. Convención de IDs

```text
MIASI-<DOMINIO>-<NNN>
```

| Dominio | Significado |
|---|---|
| `AGT` | Diseño de agentes. |
| `MOD` | Modelos y adaptadores. |
| `TOOL` | Herramientas. |
| `EXEC` | Dry-run, execute e idempotencia. |
| `RAG` | Recuperación, grounding y citas. |
| `MEM` | Memoria y estado. |
| `EVAL` | Evaluación y quality gates. |
| `OBS` | Observabilidad y trazas. |
| `SEC` | Seguridad general. |
| `POL` | Policy-as-code. |
| `HITL` | Human-in-the-loop. |
| `CICD` | CI/CD y supply chain. |
| `DATA` | Datos, privacidad y retención. |
| `OPS` | Operación, incidentes y SLO/SLA. |
| `DOC` | Documentación y trazabilidad. |

## 3. Controles mínimos

| ID | Control | Obligatorio desde | Evidencia requerida | Bloquea |
|---|---|---|---|---:|
| MIASI-AGT-001 | Todo agente tiene Agent Card versionada. | A1 | `templates/agent_card.md` completada. | Sí |
| MIASI-AGT-002 | Todo agente declara nivel de autonomía A0..A7. | A1 | Campo `autonomy_level`. | Sí |
| MIASI-MOD-001 | Todo uso de LLM pasa por ModelAdapter. | A2 | Config de adapter. | Sí |
| MIASI-TOOL-001 | Toda herramienta tiene Tool Card. | A2 | `templates/tool_card.md`. | Sí |
| MIASI-TOOL-002 | Toda herramienta declara side effects. | A2 | `side_effects`. | Sí |
| MIASI-EXEC-001 | Dry-run por defecto en acciones con efectos. | A2 | Tests de dry-run. | Sí |
| MIASI-EXEC-002 | Execute requiere política y trazas. | A3 | Policy decision + trace. | Sí |
| MIASI-RAG-001 | Todo RAG declara corpus, fuentes y límites. | A2 | RAG Card. | Sí |
| MIASI-RAG-002 | Respuestas con RAG registran grounding/citas. | A2 | Eval report. | Sí |
| MIASI-MEM-001 | Toda memoria persistente declara retención. | A2 | Memory Card. | Sí |
| MIASI-EVAL-001 | Todo agente tiene evaluación mínima offline. | A2 | Eval Card + resultados. | Sí |
| MIASI-EVAL-002 | Todo agente con tools evalúa tool selection. | A2 | Dataset de tool selection. | Sí |
| MIASI-EVAL-003 | Todo release tiene regresión mínima. | A3 | CI report. | Sí |
| MIASI-OBS-001 | Toda ejecución relevante emite run_id. | A2 | JSONL/OpenTelemetry. | Sí |
| MIASI-OBS-002 | Tool calls quedan trazados con inputs redactados. | A2 | Trace event. | Sí |
| MIASI-SEC-001 | Secret scan antes de release. | A2 | Reporte LAB-AI-075 o equivalente. | Sí |
| MIASI-SEC-002 | SAST/SBOM antes de release. | A3 | Reporte LAB-AI-076 o equivalente. | Sí |
| MIASI-POL-001 | Acciones sensibles pasan por policy gate. | A3 | Policy Card + decision log. | Sí |
| MIASI-HITL-001 | Acciones críticas requieren aprobación humana. | A4 | Human Approval record. | Sí |
| MIASI-DATA-001 | Todo dato personal declara clasificación. | A2 | Data Handling Sheet. | Sí |
| MIASI-DATA-002 | Todo sistema define retención y eliminación. | A3 | Policy/data card. | Sí |
| MIASI-CICD-001 | Todo PR/MR ejecuta tests mínimos. | A3 | CI report. | Sí |
| MIASI-CICD-002 | Artefactos tienen procedencia documentada. | A5 | Release checklist. | No en MVP; sí en producción. |
| MIASI-OPS-001 | Todo agente operacional tiene runbook. | A5 | Runbook. | Sí |
| MIASI-OPS-002 | Incidentes tienen severidad y escalamiento. | A5 | Incident report. | Sí |
| MIASI-DOC-001 | Toda decisión arquitectónica relevante tiene ADR. | A3 | ADR. | No en MVP; sí en reviewed. |

## 4. Estados de control

| Estado | Significado |
|---|---|
| `pass` | Control cumplido con evidencia. |
| `fail` | Control incumplido. |
| `waived` | Excepción aprobada, temporal y justificada. |
| `not_applicable` | No aplica por alcance documentado. |

## 5. Criterios de bloqueo

- Un control obligatorio en `fail` bloquea promoción.
- Un `waived` sin responsable, expiración y mitigación se trata como `fail`.
- Un agente A4+ no puede operar sin `MIASI-HITL-001`.
