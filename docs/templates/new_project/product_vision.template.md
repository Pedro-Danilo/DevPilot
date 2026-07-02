---
doc_id: "NEW-PROJECT-PRODUCT-VISION-TEMPLATE"
title: "Template — Product vision for new DevPilot project"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
template_id: "product_vision"
artifact_kind: "new_project_template"
created_by: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---

# Product vision — {{project_name}}

## 1. Contexto de negocio

```text
Idea inicial: {{project_idea}}
Usuario objetivo: {{target_user}}
Problema observable: {{business_problem}}
Resultado esperado: {{expected_outcome}}
```

## 2. Visión de producto

DevPilot debe tratar este documento como la fuente inicial de alineación entre negocio, producto e ingeniería. La visión debe explicar por qué el proyecto existe, qué cambio produce y cómo se reconocerá que el primer MVP aporta valor.

```text
Enunciado de visión:
{{vision_statement}}
```

## 3. Propuesta de valor

```text
Beneficio principal: {{primary_value}}
Diferenciador técnico o operativo: {{differentiator}}
Usuarios que se benefician primero: {{early_adopters}}
```

## 4. Restricciones iniciales

```text
local_first=true
dry_run=true por defecto
no_external_apis_required=true
no_secrets_allowed=true
no_remote_execution_enabled=true
no_connector_write_enabled=true
no_plugin_execution_enabled=true
```

El proyecto puede evolucionar hacia integraciones externas solo mediante ADR, threat model, controles de seguridad, presupuesto de costo y aprobación humana.

## 5. Métricas de éxito

| Métrica | Línea base | Objetivo MVP | Cómo se mide |
|---|---:|---:|---|
| {{metric_1}} | {{baseline_1}} | {{target_1}} | {{measurement_1}} |
| {{metric_2}} | {{baseline_2}} | {{target_2}} | {{measurement_2}} |

## 6. No objetivos iniciales

```text
- No generar código productivo automáticamente.
- No usar APIs externas como dependencia base.
- No almacenar secretos reales en documentos, plantillas, fixtures o repositorios.
- No prometer production-ready sin quality gates y evidencia local.
```

## 7. Criterios PASS/BLOCK

PASS si la visión define problema, usuario, valor, restricciones y métricas verificables.

BLOCK si la visión depende de conocimiento conversacional no documentado, secrets, vendor lock-in, red obligatoria o generación automática de código sin revisión.
