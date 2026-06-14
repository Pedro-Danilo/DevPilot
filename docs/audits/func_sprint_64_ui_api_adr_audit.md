---
title: "Auditoría FUNC-SPRINT-64 — ADR UI/API local y threat model de interfaz"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-64"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-64"
updated: "2026-06-14"
source_repo: "repo_DevPilot_Local_78.zip"
source_backlog: "docs/devpilot_backlog_fase_F_producto_visual.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_64"
---

# Auditoría FUNC-SPRINT-64 — ADR UI/API local y threat model de interfaz

## 0. Estado

Veredicto: `PASS`.

`FUNC-SPRINT-64` queda implementado como **implemented-initial**. El sprint cierra decisión arquitectónica y threat model antes de construir servidor o frontend. No implementa API HTTP activa, Web UI, Desktop shell, dependencias runtime, red externa ni cambios destructivos; no hay servidor activo en Sprint 64.

## 1. Propósito

Auditar que DevPilot inicia Fase F con una decisión UI/API explícita, coherente con la estrategia Web UI first y con controles de seguridad antes de implementar la API local y la Web UI local.

## 2. Alcance implementado

| Entregable | Estado | Comentario |
|---|---|---|
| ADR-0013 Web UI/API first | Implementado | Ratifica FastAPI como API local futura, Web UI local como interfaz canónica y Desktop diferido. |
| Threat model UI/API | Implementado | Cubre localhost, token, CORS, CSRF/local origin, secrets, reports, traces, path traversal y acciones críticas. |
| C4 Container actualizado | Implementado | API local/Web UI local planned-fase-f; Desktop deferred. |
| Internal Application Contract actualizado | Implementado | Contrato runtime y documento sincronizados con Web UI/API first. |
| Manifiesto Sprint 64 | Implementado | `docs/functional_sprint_64_manifest.json`. |
| Pruebas documentales | Implementado | `tests/test_sprint_64_documentation.py`. |

## 3. Decisión arquitectónica

La decisión es:

```text
CLI técnica estable → ApplicationService → API local segura → Web UI local → Web UI real futura
```

Desktop queda diferido fuera de Fase F y solo podrá reabrirse por ADR posterior.

## 4. Funcionamiento e integración

Sprint 64 funciona como gate arquitectónico:

1. define stack objetivo y límites;
2. actualiza `ApplicationService.application_contract()` para que la frontera runtime refleje Web UI/API first;
3. documenta amenazas y controles antes de Sprint 67/68;
4. mantiene Sprint 65 como próximo paso para ampliar ApplicationService por dominios;
5. evita implementar servidor/frontend antes de contratos y threat model.

## 5. Archivos creados

| Archivo | Rol |
|---|---|
| `docs/03_security/ui_api_threat_model.md` | Threat model de API local/Web UI local. |
| `docs/audits/func_sprint_64_ui_api_adr_audit.md` | Auditoría de implementación del sprint. |
| `docs/functional_sprint_64_manifest.json` | Manifiesto funcional del sprint. |
| `tests/test_sprint_64_documentation.py` | Pruebas de sincronización documental y contrato. |

## 6. Archivos modificados

| Archivo | Cambio |
|---|---|
| `README.md` | Actualiza último hito a Sprint 64 y próximo hito a Sprint 65. |
| `docs/05_operations/runbook.md` | Agrega operación/verificación Sprint 64. |
| `docs/devpilot_backlog_fase_F_producto_visual.md` | Marca Sprint 64 implementado y próximo Sprint 65. |
| `docs/functional_backlog_after_precode.md` | Actualiza transición y `next_sprint`. |
| `docs/02_architecture/adrs/ADR-0013-web-ui-first.md` | Operacionaliza estrategia UI/API Web first. |
| `docs/02_architecture/c4_container.md` | Sincroniza contenedores Fase F. |
| `docs/07_interfaces/internal_application_contract.md` | Sincroniza contrato interno con Web UI/API first. |
| `src/devpilot_core/application/services.py` | Ajusta app contract runtime a Web UI/API first y Desktop deferred. |
| `src/devpilot_core/application/dtos.py` | Ajusta comentarios de DTOs para no presentar Desktop como ruta actual. |
| `tests/test_application_services.py` | Ajusta expectativas de contrato runtime. |

## 7. Comandos de verificación

```powershell
python -m devpilot_core validate-artifact docs/02_architecture/adrs/ADR-0013-web-ui-first.md --json
python -m devpilot_core validate-artifact docs/03_security/ui_api_threat_model.md --json
python -m devpilot_core validate-artifact docs/audits/func_sprint_64_ui_api_adr_audit.md --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_64_manifest.json --json
python -m devpilot_core app contract --json
python -m pytest tests/test_sprint_64_documentation.py -q
python -m pytest tests/test_application_services.py -q
python -m devpilot_core validate all --json
```

## 8. Criterios PASS

- ADR aprobada y operacionalizada.
- Threat model aprobado.
- C4/internal contract sincronizados.
- App contract runtime declara `visual_strategy=web_ui_first`, `api_local_planned=true`, `web_ui_local_planned=true`, `desktop_deferred=true`.
- No hay servidor, frontend, Desktop shell ni dependencias nuevas.
- Próximo sprint queda `FUNC-SPRINT-65`.

## 9. Criterios BLOCK

- API o frontend implementados en Sprint 64.
- Desktop reintroducido como alcance de Fase F.
- CORS wildcard, red externa o `0.0.0.0` autorizados por defecto.
- UI autorizada a saltarse ApplicationService.
- Threat model ausente o sin controles de secrets/actions.

## 10. Riesgos y limitaciones

| Riesgo | Estado | Tratamiento |
|---|---|---|
| Seguridad local incompleta | Pendiente Sprint 68 | Token/CORS/policy binding se implementarán después. |
| ApplicationService aún limitado | Pendiente Sprint 65 | Expandir dominios antes de API real. |
| API no implementada | Esperado | Sprint 64 solo decide y modela amenazas. |
| Web UI no implementada | Esperado | Sprint 69 inicia UI después de API/seguridad. |
| Web real no implementada | Futuro | Requiere ADR y controles de producción. |

## 11. Conclusión

Sprint 64 queda cerrado como gate arquitectónico de Fase F. La implementación evita sobreconstrucción temprana, elimina ambigüedad Desktop/Web y deja condiciones verificables para avanzar hacia ApplicationService v2, contratos API, API local segura y Web UI local.


Nota Sprint 64: Desktop queda diferido fuera de Fase F.
