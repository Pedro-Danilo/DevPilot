---
title: "Política de referencias MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
---
# Política de referencias MIASI

## 1. Propósito

Normalizar cómo MIASI usa referencias externas para mantener auditabilidad, actualización y trazabilidad.

## 2. Regla central

Toda afirmación normativa basada en estándares, especificaciones, documentación de proveedor o estado del arte debe indicar fuente, tipo de fuente, criticidad y fecha de consulta.

## 3. Tipos de fuente

| Tipo | Definición | Ejemplos | Preferencia |
|---|---|---|---|
| Primaria normativa | Estándar, especificación o documentación oficial. | NIST, ISO, OWASP, OpenTelemetry, MCP, SLSA, CycloneDX. | Alta |
| Primaria de proveedor | Documentación oficial de plataforma. | OpenAI Agents SDK, LangGraph, Microsoft Foundry. | Alta |
| Secundaria técnica | Artículo técnico confiable que explica una fuente primaria. | Blogs técnicos reconocidos. | Media |
| Opinión / análisis | Interpretación no normativa. | Ensayos, posts personales. | Baja |

## 4. Campos mínimos de referencia

| Campo | Obligatorio | Descripción |
|---|---:|---|
| `title` | Sí | Nombre de la fuente. |
| `url` | Sí | URL pública o referencia bibliográfica. |
| `source_type` | Sí | Primaria normativa, proveedor, secundaria u opinión. |
| `accessed_at` | Sí | Fecha de consulta. |
| `scope` | Sí | Sección MIASI que la usa. |
| `criticality` | Sí | Alta, media o baja. |
| `notes` | No | Restricciones, versión, advertencias. |

## 5. Ejemplo YAML

```yaml
reference:
  title: "OpenTelemetry Semantic Conventions for Generative AI Systems"
  url: "https://opentelemetry.io/docs/specs/semconv/gen-ai/"
  source_type: "primary-standard-doc"
  accessed_at: "2026-05-30"
  scope: "observability"
  criticality: "high"
  notes: "Usada para nomenclatura de spans, eventos y métricas GenAI."
```

## 6. Fuentes base

- NIST AI RMF / GenAI Profile.
- ISO/IEC 42001.
- OWASP Top 10 for LLM Applications.
- OpenTelemetry GenAI semantic conventions.
- MCP specification.
- OpenAI Agents SDK.
- LangGraph.
- Microsoft Foundry Agent Evaluators.
- NIST SSDF.
- SLSA.
- CycloneDX.
- arc42.
- C4 Model.
- Diátaxis.

## 7. Criterios de cumplimiento

- Toda fuente externa importante debe aparecer en el documento que la usa.
- Para documentos que guíen producción, se debe preferir fuente primaria.
- Las URLs vivas deben revisarse antes de promover un documento a `reviewed`.

## 8. Criterios de bloqueo

- Un documento no puede marcarse `approved` si basa controles críticos en fuentes no citadas.
- Una recomendación de seguridad no puede depender únicamente de una fuente secundaria.
