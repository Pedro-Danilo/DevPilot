---
doc_id: "NEW-PROJECT-MVP-SCOPE-TEMPLATE"
title: "Template — MVP scope for new DevPilot project"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
template_id: "mvp_scope"
artifact_kind: "new_project_template"
created_by: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---

# MVP scope — {{project_name}}

## 1. Objetivo del MVP

```text
Objetivo: {{mvp_objective}}
Usuario principal: {{primary_user}}
Escenario principal: {{primary_scenario}}
```

## 2. Alcance incluido

| Capability | Usuario beneficiado | Entregable verificable | Evidencia requerida |
|---|---|---|---|
| {{capability_1}} | {{user_1}} | {{deliverable_1}} | {{evidence_1}} |
| {{capability_2}} | {{user_2}} | {{deliverable_2}} | {{evidence_2}} |

## 3. Fuera de alcance

```text
- Integraciones externas no aprobadas.
- Deploy real.
- Connector write.
- Plugin execution.
- Remote execution.
- Automatización destructiva.
```

## 4. Historias candidatas

```text
Como {{actor}}, quiero {{action}}, para {{benefit}}.
Como {{actor}}, quiero {{action}}, para {{benefit}}.
```

## 5. Backlog semilla

| ID | Tipo | Descripción | Criterio PASS | Riesgo |
|---|---|---|---|---|
| MVP-001 | feature | {{feature_description}} | {{pass_criterion}} | {{risk}} |
| MVP-002 | quality | {{quality_description}} | {{pass_criterion}} | {{risk}} |

## 6. Gates mínimos antes de código

```text
[ ] Product vision aprobado.
[ ] Requirements specification aprobado.
[ ] Architecture document aprobado.
[ ] Security threat model aprobado.
[ ] Test strategy aprobado.
[ ] MIASI registries mínimos definidos para proyectos agent-assisted.
[ ] Readiness estricta ejecutada en modo local/dry-run.
```

## 7. Criterios PASS/BLOCK

PASS si el alcance es pequeño, verificable, no mágico y tiene entregables observables.

BLOCK si el MVP requiere datos sensibles, secretos, red obligatoria, automatización destructiva o decisiones arquitectónicas no documentadas.
