---
title: "Human Approval Card — DevPilot Local"
doc_id: "DEVPL-MIASI-HUMAN_APPROVAL"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIASI"
parent_standard: "MIPSoftware"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-27"
approval: "approved_by_owner_direction"
source_baseline: "security approved + policy card reviewed"
change_policy: "controlled_changes_allowed_until_precode_baseline"
baseline_role: "precode_approved_baseline"
---

# Human Approval Card — DevPilot Local

## 1. Propósito

Este documento define cuándo y cómo DevPilot Local debe solicitar aprobación humana para acciones propuestas por agentes, herramientas o flujos automatizados.

La regla central es:

> Ninguna acción con impacto material sobre archivos, repositorios, costos, datos sensibles, configuración, despliegue o historial Git puede ejecutarse sin aprobación humana explícita y trazable.

## 2. Estados de aprobación

| Estado | Descripción |
|---|---|
| `not_required` | La acción es de lectura/validación sin riesgo. |
| `required` | La acción necesita revisión humana. |
| `pending` | La solicitud fue creada y espera decisión. |
| `approved` | El owner autorizó la acción. |
| `rejected` | El owner rechazó la acción. |
| `expired` | La solicitud venció. |
| `revoked` | Una aprobación previa fue anulada. |

## 3. Acciones que requieren aprobación

| Acción | Fase | Motivo |
|---|---|---|
| Escribir o sobrescribir documento fuente | MVP | Riesgo de pérdida de contenido. |
| Crear borrador en zona versionable | MVP | Cambio en repo. |
| Aplicar patch | MVP+ | Riesgo de modificación de código. |
| Ejecutar pruebas con comandos no triviales | MVP+ | Riesgo operacional. |
| Crear commit/tag/branch | MVP+ | Impacto en trazabilidad. |
| Enviar código o docs a API externa | MVP/MVP+ | Privacidad/costo. |
| Usar modelo externo con costo | MVP/MVP+ | CostGuard. |
| Activar tool de alto riesgo | MVP+ | Side effects. |
| Modificar policies | MVP+ | Cambio de seguridad. |
| Desplegar o publicar artefactos | Post-MVP | Impacto externo. |

## 4. Formato de solicitud

```json
{
  "approval_id": "APR-0001",
  "workspace_id": "devpilot-local",
  "requested_by": "ArchitectureAgent",
  "action_type": "apply_patch",
  "risk_level": "high",
  "summary": "Aplicar patch de refactor sobre módulo de validación",
  "affected_files": ["src/devpilot_core/validators.py"],
  "policy_checks": ["dry_run_passed", "no_secret_detected"],
  "cost_estimate": null,
  "rollback_plan": "git restore src/devpilot_core/validators.py",
  "expires_at": "2026-06-05T23:59:59-05:00"
}
```

## 5. Criterios de revisión humana

Antes de aprobar, el owner debe verificar:

- propósito de la acción;
- archivos afectados;
- diff o descripción del cambio;
- riesgo declarado;
- policy checks;
- resultados de pruebas;
- plan de rollback;
- impacto en secretos/datos;
- costo si usa API;
- trazabilidad en Git.

## 6. Registro de decisión

Toda decisión debe registrar:

```json
{
  "approval_id": "APR-0001",
  "decision": "approved",
  "decided_by": "owner",
  "decided_at": "2026-06-05T10:00:00-05:00",
  "conditions": ["run_pytest_after_apply"],
  "notes": "Aprobado solo si el patch coincide con el diff revisado."
}
```

## 7. Matriz de aprobación

| Riesgo | Ejemplo | Aprobación |
|---|---|---:|
| Bajo | Validar frontmatter | No |
| Medio | Generar reporte | No si ruta segura |
| Medio | Crear borrador documental | Sí si escribe en docs |
| Alto | Aplicar patch | Sí |
| Alto | Llamar API externa con código | Sí |
| Crítico | Desplegar, borrar, reescribir Git history | Bloqueado en MVP/MVP+ |

## 8. Criterios PASS

El flujo de aprobación es aceptable si:

- define triggers;
- genera solicitud estructurada;
- conserva evidencia;
- permite rechazo;
- permite condiciones;
- exige rollback para acciones críticas;
- no permite autoaprobación del agente.

## 9. Criterios BLOCK

Bloquear acción si:

- falta aprobación requerida;
- el agente intenta aprobarse a sí mismo;
- no hay plan de rollback;
- no hay diff o evidencia;
- se detectan secretos;
- el costo no está estimado;
- el riesgo declarado es menor al riesgo real.


## Actualización FUNC-SPRINT-85 — Fase H agentic/enterprise

`FUNC-SPRINT-85` sincroniza esta tarjeta MIASI con `ADR-0016 — Arquitectura avanzada agentic/enterprise` y `advanced_agentic_threat_model.md`.

Estados aplicables a Fase H:

| Estado | Uso permitido |
|---|---|
| `implemented` | Capacidad funcional y cubierta por pruebas. |
| `implemented-initial` | Primera versión operacional con límites explícitos. |
| `planned` | Diseñada, no operativa. |
| `experimental` | Solo con controles, flags y ADR futura cuando aplique. |
| `disabled` | Bloqueada por política. |
| `future` | Fuera del alcance actual. |

Reglas obligatorias:

- Multiagente requiere handoffs explícitos, trazas, policy y evals.
- RAG requiere fuentes, citas o metadatos de evidencia.
- MCP/conectores requieren registry, schema, policy y deny-by-default.
- Plugins requieren manifest, permisos, policy binding y loader no arbitrario.
- Multiworkspace requiere aislamiento de estado, reportes y secretos.
- RBAC debe influir en decisiones, no ser decorativo.
- Remote runners quedan `experimental/future` y disabled-by-default.

Criterio BLOCK: ninguna capacidad avanzada puede saltarse `PolicyEngine`, MIASI, Approval cuando aplique, trazas, evals y ReportEngine.


## Actualización POST-H-012-E — Approval/RBAC hardening operativo

`POST-H-012-E` sincroniza esta tarjeta MIASI con el hardening local de aprobaciones y RBAC. El ciclo operativo vigente para acciones sensibles es:

```text
approval request -> approval approve | approval deny -> optional approval revoke -> policy check -> quality-gate approval-rbac-hardening
```

Reglas obligatorias:

- `approval request` debe declarar `actor`, `tool`, `action`, `subject`, expiración y scope exacto.
- Las acciones críticas deben incluir `role_at_decision`, `command_id` y `tool_call_id` en el scope cuando el catálogo lo requiere.
- `approval approve` no convierte una acción bloqueada por catálogo en ejecutable.
- `approval deny` debe usarse cuando el scope, evidencia o riesgo no es aceptable.
- `approval revoke` debe usarse si cambia el diff, sujeto, actor, herramienta, interfaz o contexto de riesgo.
- `interface` debe evaluarse explícitamente en `PolicyEngine`; API/UI/agent/remote/connector/plugin permanecen bloqueadas para acciones no expuestas.
- No approvals globales permanentes para acciones críticas.
- No remote execution, connector write ni plugin execution.

Ejemplo seguro de verificación:

```powershell
python -m devpilot_core policy check publish_deploy_tag `
  --tool release.manager `
  --subject v1.2.3 `
  --actor local-owner `
  --role-at-decision owner `
  --command-id cmd-demo `
  --tool-call-id tool-call-demo `
  --interface cli `
  --json
```

Criterio PASS: el request anterior bloquea si no hay approval válido y conserva findings normalizados como `APPROVAL_REQUIRED`, `RBAC_DENIED`, `APPROVAL_SCOPE_MISMATCH` o bloqueos del `SensitiveActionCatalog`.

Criterio BLOCK: cualquier ruta que omita actor, rol, expiración, revocación, interfaz o binding de comando/tool-call para acciones críticas.
