---
title: "Auditoría de sincronización — Estrategia Web UI first Fase F"
doc_id: "DEVPL-AUDIT-PHASE-F-WEB-FIRST-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
updated: "2026-06-14"
source_repo: "repo_DevPilot_Local_77.zip"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# Auditoría de sincronización — Estrategia Web UI first Fase F

## Propósito

Registrar la decisión de alinear Fase F con una estrategia visual web-first: Web UI local como interfaz canónica, evolución futura a Web UI real y Desktop diferido fuera de Fase F.

## Estado

Veredicto: `PASS`.

La decisión es profesionalmente conveniente para DevPilot porque reduce duplicación, protege el core local-first, mantiene la CLI como ruta técnica, aprovecha `ApplicationService` y deja Desktop sujeto a evidencia futura.

## Cambios aplicados

- Se crea `ADR-0013 — Estrategia visual Web UI first`.
- Se actualiza `docs/devpilot_backlog_fase_F_producto_visual.md` a versión `1.1.0` y `source_repo: repo_DevPilot_Local_77.zip`.
- Se ajusta el propósito de Fase F hacia `API local segura + Web UI local web-ready`.
- Se elimina Desktop como objetivo de implementación de Fase F.
- Se mantiene Desktop como posibilidad futura condicionada a ADR posterior.
- Se sincronizan README, product vision, roadmap, MVP scope, architecture document, C4 Container, internal application contract, runbook y functional backlog.

## Criterios PASS

```text
Web UI local queda declarada como interfaz visual canónica de Fase F.
Web UI real queda declarada como evolución posterior.
Desktop queda diferido fuera de Fase F.
No se implementa servidor, frontend ni shell desktop.
Los artefactos conservan local-first, dry-run y ApplicationService como frontera.
```

## Criterios BLOCK

```text
Fase F intenta construir dos UI independientes.
Desktop queda como entregable obligatorio de Fase F.
La Web UI local consume core directamente.
La API local se expone públicamente por defecto.
Operaciones críticas se ejecutan sin PolicyEngine y Approval Workflow.
```

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Confundir Web UI local con SaaS | Documentar que es local, localhost y sin red externa por defecto. |
| Reabrir Desktop prematuramente | Requerir ADR posterior con evidencia de conveniencia. |
| Diseñar Web local sin evolución a Web real | Usar contratos API versionados y separación ApplicationService. |
| Duplicar lógica frontend/core | Prohibir imports directos al core desde UI. |

## Verificación recomendada

```powershell
python -m devpilot_core validate-artifact docs/02_architecture/adrs/ADR-0013-web-ui-first.md --json
python -m devpilot_core validate-artifact docs/devpilot_backlog_fase_F_producto_visual.md --json
python -m devpilot_core validate-artifact docs/audits/phase_f_web_first_ui_strategy_audit.md --json
python -m pytest tests/test_phase_f_web_first_strategy.py -q
pytest -q
```
