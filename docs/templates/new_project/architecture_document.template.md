---
doc_id: "NEW-PROJECT-ARCHITECTURE-DOCUMENT-TEMPLATE"
title: "Template — Architecture document for new DevPilot project"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
template_id: "architecture_document"
artifact_kind: "new_project_template"
created_by: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---

# Architecture document — {{project_name}}

## 1. Decisiones arquitectónicas iniciales

```text
Estilo arquitectónico: {{architecture_style}}
Ejecución inicial: local-first
Persistencia inicial: {{persistence_choice}}
Interfaz inicial: {{interface_choice}}
Modelo IA inicial: mock/local-first mediante ModelAdapter
```

## 2. Contexto y límites

```text
Sistema: {{system_name}}
Usuarios: {{users}}
Sistemas externos: ninguno obligatorio para MVP
Trust boundary principal: workspace local
```

## 3. Componentes propuestos

| Componente | Responsabilidad | Entrada | Salida | Riesgo |
|---|---|---|---|---|
| {{component_1}} | {{responsibility_1}} | {{input_1}} | {{output_1}} | {{risk_1}} |
| {{component_2}} | {{responsibility_2}} | {{input_2}} | {{output_2}} | {{risk_2}} |

## 4. Capa ModelAdapter

```text
ModelAdapter
  ├─ MockModelAdapter       # sin API, determinístico, pruebas y demos
  ├─ LocalModelAdapter      # modelo local futuro, sin red externa
  └─ ExternalApiAdapter     # futuro, deshabilitado por defecto y sujeto a ADR
```

El MVP no debe depender exclusivamente de un proveedor externo ni requerir credenciales de API para pruebas base.

## 5. Persistencia y estado

```text
configuración versionable: {{config_paths}}
runtime artifacts: outputs/ no versionable
base de datos local: {{local_db_choice}}
secretos: prohibidos en repo; usar placeholders no sensibles
```

## 6. ADRs requeridas

| ADR | Motivo | Estado |
|---|---|---|
| {{adr_id}} | {{decision_reason}} | draft |

## 7. Criterios PASS/BLOCK

PASS si la arquitectura define límites, componentes, datos, modelo de ejecución, ModelAdapter y riesgos.

BLOCK si habilita red, secretos, remote execution, connector write o plugin execution sin ADR y controles.
