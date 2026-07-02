---
doc_id: "NEW-PROJECT-REQUIREMENTS-SPECIFICATION-TEMPLATE"
title: "Template — Requirements specification for new DevPilot project"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
template_id: "requirements_specification"
artifact_kind: "new_project_template"
created_by: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---

# Requirements specification — {{project_name}}

## 1. Actores y contexto

| Actor | Necesidad | Permisos esperados | Riesgo |
|---|---|---|---|
| {{actor_1}} | {{need_1}} | {{permissions_1}} | {{risk_1}} |
| {{actor_2}} | {{need_2}} | {{permissions_2}} | {{risk_2}} |

## 2. Requisitos funcionales

| ID | Requisito | Prioridad | Criterio de aceptación | Evidencia |
|---|---|---|---|---|
| FR-001 | {{functional_requirement}} | P1 | {{acceptance_criterion}} | {{evidence}} |
| FR-002 | {{functional_requirement}} | P2 | {{acceptance_criterion}} | {{evidence}} |

## 3. Requisitos no funcionales

```text
NFR-SEC-001: No almacenar secretos en repo, plantillas, fixtures ni logs.
NFR-OPS-001: Operar local-first y dry-run-first durante el MVP.
NFR-QA-001: Toda capacidad debe tener prueba focal o contrato de validación.
NFR-TRACE-001: Cada decisión relevante debe enlazar a documento fuente o ADR.
NFR-COST-001: Toda ruta con API externa futura debe tener límite de costo y alternativa local.
```

## 4. Multi-model y ModelAdapter

El proyecto no debe acoplarse a un proveedor LLM específico. Si necesita modelos, documentar tres rutas:

```text
Ruta sin API: {{mock_or_rule_based_path}}
Ruta local: {{local_model_path}}
Ruta con API externa futura: {{external_api_path_requiring_approval}}
```

## 5. Datos y privacidad

| Dato | Sensibilidad | Retención | Redacción requerida | Responsable |
|---|---|---|---|---|
| {{data_item}} | {{sensitivity}} | {{retention}} | {{redaction}} | {{owner}} |

## 6. Criterios PASS/BLOCK

PASS si los requisitos son trazables, verificables y separan funcional, seguridad, calidad, costo y privacidad.

BLOCK si hay requisitos ambiguos, secretos embebidos, dependencias externas obligatorias o acciones destructivas sin aprobación.
