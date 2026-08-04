---
doc_id: "DEVPL-UOC-000-UI-CAPABILITY-REGISTRY"
title: "UI Capability Registry — UOC-000"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
approval: "approved_by_owner"
updated: "2026-08-04"
created_by: "UOC-000"
source_of_truth: ".devpilot/interfaces/ui_capability_registry.json"
preliminary: false
---

# UI Capability Registry — UOC-000

## 1. Propósito

Este documento explica el registro ejecutable que clasifica la superficie CLI,
API y UI de DevPilot. La fuente de verdad machine-readable es:

```text
.devpilot/interfaces/ui_capability_registry.json
```

UOC-000 no añade rutas, no ejecuta comandos y no habilita escrituras. Congela
las reglas que deben cumplir los sprints posteriores.

## 2. Baseline

```text
Branch canónico: eval/post-h-eval-002-02-a-onboarding
Commit: 43254e3e61cdafe65e0ed2d773fe9032b0a81f05
CLI commands: 193
API routes: 39
UI routes: 5
```

## 3. Resultados de clasificación

### Por estado de paridad

| Estado | Total |
|---|---:|
| `CLI-BRIDGE-REGISTERED` | 181 |
| `PLANNED` | 3 |
| `POLICY-BLOCKED` | 5 |
| `UI-READ-ONLY` | 4 |

### Por clase de riesgo

| Clase | Total |
|---|---:|
| `forbidden` | 5 |
| `mutating` | 130 |
| `read-only` | 2 |
| `sensitive` | 56 |

### Por dominio propietario

| Dominio | Total |
|---|---:|
| `interface.cli` | 27 |
| `release` | 26 |
| `documentation.governance` | 13 |
| `quality.gate` | 12 |
| `operations.observability` | 11 |
| `agentic.runtime` | 10 |
| `governance.testing` | 10 |
| `agentic.modeling` | 10 |
| `operations.workspace` | 9 |
| `product.api` | 8 |
| `governance.schemas` | 6 |
| `governance.miasi` | 5 |
| `operations.runtime_state` | 5 |
| `operations.audit` | 4 |
| `integration.connectors` | 4 |
| `security.rbac` | 4 |
| `security.approval` | 3 |
| `governance.compliance` | 3 |
| `agentic.multiagent` | 3 |
| `extensibility.plugins` | 3 |
| `governance.project_state` | 3 |
| `knowledge.rag` | 3 |
| `product.operator` | 2 |
| `governance.policy` | 2 |
| `workspace.portfolio` | 2 |
| `enterprise.remote` | 2 |
| `application.service` | 1 |
| `enterprise.reporting` | 1 |
| `security.guards` | 1 |

## 4. Reglas de clasificación

- `read-only`: no muta estado ni genera archivos.
- `mutating`: escribe reportes/evidencia y requiere policy más dry-run para UI.
- `sensitive`: puede escribir archivos, mutar estado o ejecutar subprocess; exige policy, dry-run y approval antes de exposición UI.
- `forbidden`: riesgo crítico o potencial de red bajo no-go gates actuales; queda `POLICY-BLOCKED`.

`write-report` se trata como mutación operacional aunque no modifique código
fuente. Esto evita que una UI futura escriba outputs sin policy ni evidencia.

## 5. Capacidades actuales con superficie UI

- `operator.dashboard`
- `portfolio.status`
- `standards.status`
- `workspace.status`

## 6. Capacidades bloqueadas por policy

- `plugin.dry-run`
- `plugin.list`
- `plugin.validate`
- `remote.runner.readiness`
- `remote.runner.status`

## 7. Mapeo de rutas UI

- `ui.approvals` `/approvals` → 7 API routes; 1 CLI capabilities equivalentes.
- `ui.dashboard` `/` → 7 API routes; 4 CLI capabilities equivalentes.
- `ui.reports` `/reports` → 4 API routes; 1 CLI capabilities equivalentes.
- `ui.settings` `/settings` → 6 API routes; 1 CLI capabilities equivalentes.
- `ui.traces` `/traces` → 4 API routes; 1 CLI capabilities equivalentes.

## 8. Contrato para paridad futura

Toda promoción debe conservar:

```text
UI intent
→ API tipada
→ Application Service
→ Policy/PathGuard/CostGuard
→ plan o dry-run
→ approval cuando aplique
→ job gobernado
→ postcondición
→ trace/report/evidence
→ commit o rollback
```

No se considera paridad válida invocar una cadena CLI arbitraria desde el
navegador.

## 9. Budgets

- page size por defecto: 50; máximo: 250.
- timeout duro de lectura: 15000 ms.
- preview inline máximo: 1048576 bytes.
- timeout de job por defecto: 900 s; máximo: 7200 s.
- máximo de reintentos: 2.

## 10. Gate UOC-000

```text
CLI classified: 193/193
UI routes mapped: 5/5
Mutating without policy: 0
Sensitive UI-NATIVE without approval: 0
New UI routes: 0
Runtime execution enabled: false
```
