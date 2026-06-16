---
title: "Cierre Fase F — Producto visual web-first"
doc_id: "DEVPL-AUDIT-PHASE-F-VISUAL-CLOSURE"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-73"
updated: "2026-06-16"
approval: "approved_after_visual_product_quality_gate"
---

# Cierre Fase F — Producto visual web-first

## 0. Estado

Veredicto: `PASS`.

`FUNC-SPRINT-73 — Cierre Fase F web-first y decisión de evolución` cierra la Fase F con un producto visual MVP local, API-first, web-ready y gobernado. La fase queda cerrada como `closed_visual_mvp_web_first`.

## 1. Propósito

Cerrar formalmente la Fase F, consolidar el estado real del producto visual y registrar la decisión de evolución: **Web UI local como interfaz visual canónica**, evolución futura hacia **Web UI real** y **Desktop diferido** fuera de la Fase F.

## 2. Alcance cerrado

La Fase F entrega:

- ADR y threat model para API local/Web UI local.
- ApplicationService v2 por dominios como frontera de integración.
- contrato API v1 y OpenAPI 3.1.
- API local FastAPI protegida por token local, CORS restringido y policy binding.
- Web UI local MVP bajo `ui/web`.
- dashboard de workspace/readiness/standards/MIASI.
- Report Viewer y Trace Viewer.
- Approval Center y Action Launcher dry-run.
- Settings UI para workspace, providers y policy en modo read-only/plan-only.
- Visual Product Quality Gate.
- release manifest visual MVP.

## 3. Decisión de evolución

La ruta aprobada es:

```text
CLI soportada + API local segura + Web UI local
  -> Web UI real futura cuando existan RBAC, sesiones, despliegue y hardening adicional
```

Desktop queda diferido. No se implementa Tauri, Electron, Textual ni shell nativo en Fase F. Cualquier reapertura de Desktop requiere ADR posterior y threat model específico sobre permisos nativos, auto-update, empaquetado, filesystem y distribución.

## 4. Estado de capacidades

| Capacidad | Estado | Evidencia |
|---|---|---|
| CLI local | Implementada | `python -m devpilot_core validate all --json` |
| ApplicationService v2 | Implementada | `python -m devpilot_core app contract --json` |
| API local segura | Implementada inicial | `/api/v1`, token, CORS restringido, policy binding |
| Web UI local | Implementada inicial | `ui/web`, `npm test` |
| Dashboard visual | Implementado inicial | Workspace/readiness/standards/MIASI |
| Report Viewer | Implementado inicial | `/api/v1/reports` |
| Trace Viewer | Implementado inicial | `/api/v1/traces`, `/api/v1/metrics/summary` |
| Approval Center | Implementado inicial | `/api/v1/approvals` |
| Settings UI | Implementado inicial | `/api/v1/settings/*` |
| Web UI real pública | Pendiente | Requiere Fase posterior |
| Desktop shell | Diferido | Fuera de Fase F |
| RBAC/login empresarial | Pendiente | Requiere Fase posterior |
| Packaging/release industrial | Pendiente | Entrada natural de Fase G |

## 5. Evidencia de calidad

La Fase F queda respaldada por:

- `scripts/visual_product_smoke.py`.
- `docs/release/release_manifest_visual_mvp.json`.
- `docs/functional_sprint_73_manifest.json`.
- pruebas Sprint 64 a Sprint 73.
- OpenAPI sincronizado con `ApplicationService`.
- Web UI smoke test local.

## 6. Límites explícitos

Esta es una versión **MVP visual local** y no un producto SaaS/multiusuario. No incluye:

- RBAC multiusuario.
- sesiones web reales.
- despliegue remoto.
- publicación de paquetes.
- Desktop shell.
- auto-update.
- ejecución crítica desde UI sin Approval Workflow.

## 7. Riesgos

| Riesgo | Estado | Mitigación |
|---|---|---|
| Confundir MVP local con producto SaaS | Controlado | Documentar límites y evolución. |
| Desktop prematuro | Controlado | Diferido por decisión explícita. |
| UI ejecutando acciones críticas | Controlado | Action Launcher dry-run y policy binding. |
| Secretos en UI/logs | Mitigado | Redacción, token local no persistido, exclusión de logs en ZIP. |
| Dependencias frontend | Mitigado | `ui/web/package-lock.json` y smoke test. |

## 8. Criterios PASS

- Visual Product Quality Gate pasa.
- CLI/API/UI quedan sincronizados.
- Web UI no importa core Python.
- Web UI no lee `outputs/` ni `.devpilot/` directamente.
- API/UI no habilitan acciones críticas sin approval.
- Desktop queda diferido y documentado.
- Release manifest visual MVP existe.

## 9. Criterios BLOCK

- Se implementa Desktop sin ADR posterior.
- UI requiere cloud o API externa.
- UI lee filesystem local directamente.
- API expone rutas `patch/apply`, `rollback/execute`, `refactor/execute`, `git push` o `deploy`.
- No existe reporte de cierre o release manifest.

## 10. Comandos de verificación

```powershell
python scripts/visual_product_smoke.py --dry-run --json
python -m devpilot_core app contract --json
python -m devpilot_core agentops status --json
cd ui\web
npm test
cd ..\..
python -m pytest tests/test_visual_product_smoke.py tests/test_sprint_73_documentation.py -q
python -m pytest -q
```

## 11. Próximo paso

La siguiente fase natural es `FUNC-SPRINT-74 — ADR de release, versionado y productización`, perteneciente a Fase G.
