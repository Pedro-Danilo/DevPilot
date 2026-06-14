---
title: "Threat Model — API local y Web UI local DevPilot"
doc_id: "DEVPL-SEC-UI-API-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-64"
updated: "2026-06-14"
source_repo: "repo_DevPilot_Local_78.zip"
source_backlog: "docs/devpilot_backlog_fase_F_producto_visual.md"
source_adr: "docs/02_architecture/adrs/ADR-0013-web-ui-first.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_64"
---

# Threat Model — API local y Web UI local DevPilot

## Estado

`approved` para iniciar la implementación de Fase F después de `FUNC-SPRINT-64`.

Este threat model es una **primera versión implementable**. Cubre la transición de DevPilot desde CLI/Core hacia API local segura y Web UI local. No cubre todavía Web UI real pública, multiusuario, SaaS, RBAC enterprise, despliegue cloud ni Desktop shell; esos escenarios requieren ADR/threat model posteriores.

## Propósito

Definir amenazas, límites de confianza y controles mínimos antes de implementar la API local y la Web UI local de DevPilot.

El objetivo no es afirmar que localhost sea inherentemente seguro, sino impedir que una futura interfaz visual debilite los controles ya existentes: `ApplicationService`, `PolicyEngine`, MIASI, `SecretGuard`, `CostGuard`, `Approval Workflow`, `ReportEngine`, `LocalStore` y observabilidad AgentOps.

## Alcance

Incluye:

- API local futura en `127.0.0.1`.
- Web UI local futura servida o ejecutada en navegador local.
- Contratos `/api/v1` futuros.
- Respuestas basadas en `CommandResult`/`ApplicationResponse`.
- Lectura de estado, readiness, MIASI, reportes, trazas, métricas, approvals y settings.
- Acciones dry-run desde UI.
- Acciones sensibles condicionadas a PolicyEngine y Approval Workflow.

No incluye:

- Web UI real pública.
- Multiusuario real.
- RBAC industrial.
- TLS/PKI productivo.
- Exposición en red externa.
- Desktop shell, IPC nativo o auto-update.
- SaaS/cloud control plane.

## Activos

| Activo | Sensibilidad | Riesgo principal |
|---|---|---|
| `.devpilot/` | Alta | Estado local, approvals, policies, providers, SQLite. |
| `.devpilot/providers.yaml` | Alta | Exposición o activación accidental de proveedores externos. |
| `docs/` | Media-alta | Exposición de decisiones, requisitos, seguridad, prompts. |
| `outputs/reports/` | Media-alta | Findings, rutas, resúmenes, evidencia operacional. |
| `outputs/traces/` | Media-alta | Trazas, eventos, métricas, comandos y posibles metadatos sensibles. |
| Repositorios auditados | Alta | Código fuente, secretos accidentales, rutas del sistema. |
| Tokens locales API | Alta | Invocación no autorizada desde navegador/proceso local. |
| Approval decisions | Alta | Habilitación de acciones write/execute. |
| Prompt/model data | Alta | Prompt injection, fuga de prompts/completions o datos de repos. |

## Límites de confianza

```text
Browser local / Web UI local
  └── límite: origen, CORS, token, CSRF/local origin
API local 127.0.0.1
  └── límite: routing, input validation, redacción, policy binding
ApplicationService
  └── límite: contratos de operación y DTOs
DevPilot Core
  └── límite: PolicyEngine, MIASI, guards, approvals, stores
Filesystem local / repo / outputs / .devpilot
```

Principio rector: **la UI nunca es frontera de seguridad suficiente**. La API y el core deben rechazar operaciones inseguras aunque la UI esté equivocada o manipulada.

## Amenazas

| ID | Amenaza | Vector | Impacto | Control requerido |
|---|---|---|---|---|
| THREAT-UIAPI-001 | Invocación local no autorizada | Otro proceso local llama API localhost | Lectura o acción no autorizada | Token local para endpoints no públicos; allowlist de endpoints públicos mínimos. |
| THREAT-UIAPI-002 | CORS amplio | `Access-Control-Allow-Origin: *` | Sitio malicioso puede llamar API local desde browser | CORS restringido; no wildcard por defecto; origin allowlist local. |
| THREAT-UIAPI-003 | CSRF/local origin abuse | Navegador autenticado invoca API por engaño | Ejecución de acciones no deseadas | Token en header no-cookie; origin/referrer checks; no cookies auth implícitas en MVP. |
| THREAT-UIAPI-004 | Exposición por `0.0.0.0` | API escucha interfaces externas | Acceso desde LAN/VPN | Host default `127.0.0.1`; bloquear o advertir severamente bind externo. |
| THREAT-UIAPI-005 | Path traversal | Parámetros de ruta arbitraria | Lectura fuera del workspace | Resolver WorkspaceManager; PathGuard; allowlist de rutas lógicas; no filesystem browser abierto. |
| THREAT-UIAPI-006 | Secret leakage | API/UI muestra providers, env, reports o traces crudos | Exposición de API keys/tokens | SecretGuard/redacción en API y UI; tests con secretos sintéticos. |
| THREAT-UIAPI-007 | Report/trace leakage | Viewers exponen prompts, stdout, stderr o completions | Fuga de datos técnicos/sensibles | Sanitización y límites; no mostrar payloads crudos por defecto. |
| THREAT-UIAPI-008 | Acción crítica desde UI | Endpoint write/execute sin approval | Cambios destructivos | PolicyEngine + Approval Workflow + dry-run default. |
| THREAT-UIAPI-009 | Provider externo accidental | Settings habilita APIs externas | Costos/fuga externa | CostGuard; providers externos disabled por defecto; approval y presupuesto. |
| THREAT-UIAPI-010 | Prompt injection vía documentos/reports | UI muestra o reinyecta contenido no confiable | Manipulación de agentes/modelos | Treat docs/reports as untrusted; no ejecutar instrucciones desde contenido visualizado. |
| THREAT-UIAPI-011 | DoS local por payloads grandes | Reportes/trazas grandes bloquean API/UI | Degradación local | Paginación, límites, filtros y timeouts. |
| THREAT-UIAPI-012 | Confusión dry-run/execute | UX ambigua | Usuario cree que no modifica o que modificó | Etiquetas visibles; API conserva `dry_run`; execute requiere approval. |
| THREAT-UIAPI-013 | Divergencia UI/Core | UI implementa reglas propias | Falsos PASS/BLOCK | UI consume API/ApplicationService; contract tests. |
| THREAT-UIAPI-014 | Web real prematura | Exponer API en red sin auth/RBAC | Acceso no autorizado | Web real fuera de Fase F; ADR posterior obligatoria. |
| THREAT-UIAPI-015 | Desktop reintroducido sin análisis | Shell con permisos nativos inseguros | Mayor superficie e instalación riesgosa | Desktop deferred; ADR posterior obligatoria. |

## Controles

### Controles obligatorios Fase F

1. **Host local**: `127.0.0.1` por defecto.
2. **No CORS wildcard**: orígenes permitidos explícitos, inicialmente locales.
3. **Token local**: requerido para endpoints no públicos desde Sprint 68.
4. **No cookies implícitas**: evitar auth por cookie en MVP local para reducir CSRF.
5. **API-first**: UI consume `/api/v1`; no importa Python/core.
6. **ApplicationService mandatory**: endpoints delegan en ApplicationService o adapter formal.
7. **CommandResult/ApplicationResponse**: toda respuesta conserva `ok`, `exit_code`, `message`, `data`, `findings`.
8. **Dry-run default**: operaciones sensibles son dry-run o approval-gated.
9. **Approval Workflow**: write/execute requiere aprobación explícita.
10. **Secret redaction**: API/UI no muestran secretos, tokens, prompts/completions ni stdout/stderr crudos.
11. **Workspace boundary**: API resuelve rutas contra workspace y bloquea escapes.
12. **Paginación/límites**: reportes/trazas/métricas no se devuelven sin límites razonables.
13. **Auditabilidad**: acciones UI/API generan reportes/trazas/métricas cuando corresponda.
14. **Desktop out-of-scope**: ningún shell nativo en Fase F.

### Controles para Web UI real futura

La Web UI real posterior a Fase F requiere, como mínimo:

- ADR de despliegue;
- threat model de red real;
- autenticación y sesiones;
- RBAC;
- TLS;
- logs de auditoría;
- política de retención;
- hardening de headers;
- protección CSRF completa;
- separación de entornos;
- modelo de permisos para workspaces y repos.

## MIASI

El diseño de API/UI debe preservar MIASI:

| Elemento MIASI | Regla |
|---|---|
| Agent Cards | UI solo visualiza/agrega inputs; no cambia autonomía sin approval. |
| Tool Cards | Endpoints de tool deben reflejar side effect, risk level y policy rule. |
| Policy Matrix | API consulta PolicyEngine antes de acciones sensibles. |
| Eval Cards | Acciones agentic futuras deben estar evaluadas antes de UI execute. |
| Human Approval Card | UI puede mostrar/gestionar approvals, no saltarse el workflow. |
| Observability Card | UI debe consumir trazas/métricas/reportes redacted. |

## Criterios de bloqueo

Bloquear el sprint o sprint futuro si ocurre cualquiera de estos casos:

- API escucha `0.0.0.0` por defecto.
- CORS wildcard queda habilitado por defecto.
- Endpoints no públicos no exigen token o control equivalente.
- UI importa módulos Python/core directamente.
- API lee rutas arbitrarias sin WorkspaceManager/PathGuard.
- UI/API permite write/execute sin Approval Workflow.
- Se exponen secretos, tokens, prompts, completions, stdout/stderr o provider credentials.
- Se habilitan proveedores externos desde UI sin CostGuard/approval/presupuesto.
- Se implementa Desktop shell en Fase F.
- Se presenta la Web UI local como Web UI real multiusuario.

## Criterios PASS

- Este threat model pasa `validate-artifact`.
- La ADR-0013 queda aprobada y operacionalizada.
- C4 Container e internal application contract reflejan API local/Web UI local/Desktop deferred.
- No se agregan dependencias runtime ni se implementa servidor/frontend en Sprint 64.
- Las pruebas documentales de Sprint 64 pasan.

## Riesgos residuales

| ID | Riesgo residual | Tratamiento |
|---|---|---|
| RR-UIAPI-001 | Token local no protege contra malware local con acceso al perfil de usuario. | Aceptado para MVP local; documentar límite. |
| RR-UIAPI-002 | Navegador/extensiones pueden observar UI. | Aceptado; no mostrar secretos; redacción por defecto. |
| RR-UIAPI-003 | Web real futura puede requerir re-arquitectura de auth. | Diferir a ADR futura. |
| RR-UIAPI-004 | Frontend stack puede cambiar por restricciones de Node. | Mantener contratos API como fuente estable. |

## Pruebas mínimas

```powershell
python -m devpilot_core validate-artifact docs/03_security/ui_api_threat_model.md --json
python -m devpilot_core validate-artifact docs/02_architecture/adrs/ADR-0013-web-ui-first.md --json
python -m devpilot_core app contract --json
python -m pytest tests/test_sprint_64_documentation.py -q
```
