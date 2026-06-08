---
title: "FUNC-SPRINT-09 — Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos"
doc_id: "DEVPL-AUDIT-FUNC-009"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-08"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-09"
---

# FUNC-SPRINT-09 — Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos

## 1. Propósito

Este sprint introduce la primera capa ejecutable de seguridad operativa de DevPilot Local. Su objetivo es bloquear por defecto acciones inseguras, evitar filtraciones evidentes de secretos sintéticos, impedir uso de APIs externas sin política local de presupuesto y generar decisiones auditables antes de habilitar agentes, Git avanzado, aplicación de patches, refactor automático o proveedores LLM externos.

La implementación es local-first, determinística y sin dependencias externas. No llama APIs, no usa LLMs, no requiere API keys reales y no ejecuta la acción simulada. `policy check` evalúa una intención, produce una decisión y registra evidencia; no modifica archivos de usuario ni llama servicios externos.

## 2. Estado de cierre del sprint anterior

`FUNC-SPRINT-08 — Workspace Manager mínimo` queda cerrado porque la evidencia de consola reporta `pytest -q -> 51 passed`, `workspace status --json -> ok=true`, `workspace init --dry-run --json -> ok=true`, `workspace init --execute` bloqueando sobrescritura cuando `.devpilot/project.yaml` existe, y comandos anteriores sin regresión.

## 3. Componentes creados

### 3.1. `.devpilot/policy.yaml`

**Propósito:** contrato local mínimo de política de seguridad/costo del workspace.

**Funcionamiento:** declara política por defecto para dry-run, bloqueo de acciones peligrosas, redacción obligatoria de secretos y presupuesto externo en cero. La configuración actual bloquea APIs externas por defecto:

```yaml
cost:
  external_api_allowed: false
  budget_limit_usd: 0.0
  budget_used_usd: 0.0
```

**Integración:** `load_cost_policy()` lee este archivo desde `CostGuard` para que `policy check` use una política local versionada, no valores implícitos dispersos.

**Rol dentro de DevPilot:** primera configuración ejecutable de seguridad/costo para futuras integraciones con agentes, ModelAdapter, APIs y herramientas.

**Comandos de uso:**

```powershell
python -m devpilot_core policy check external-api --external-api --provider openai --estimated-cost-usd 0.01 --json
```

**Criterios PASS:** el archivo existe, bloquea APIs externas por defecto y se interpreta sin dependencias YAML externas.

**Criterios BLOCK:** permitir API externa con presupuesto cero, omitir redacción de secretos o depender de un servicio remoto para decidir.

**Riesgos:** primera versión; no incluye firma, RBAC, perfiles por usuario, cifrado ni aprobación humana persistente.

### 3.2. `src/devpilot_core/policy/decisions.py`

**Propósito:** definir `PolicyEffect` y `PolicyDecision` como contrato común de decisión.

**Funcionamiento:** modela efectos `allow`, `warn`, `deny` y `block`; cada decisión contiene guard, regla, razón, subject y metadata. Puede convertirse en `Finding` para mantener compatibilidad con `CommandResult`.

**Integración:** usado por `PathGuard`, `SecretGuard`, `CostGuard` y `PolicyEngine`.

**Rol dentro de DevPilot:** base común para que futuras políticas MIASI, aprobaciones humanas, registries de herramientas y agentes compartan un contrato de decisión auditable.

**Comandos de uso:** indirectamente mediante `policy check`.

**Criterios PASS:** cada guard devuelve decisiones normalizadas y trazables.

**Criterios BLOCK:** devolver booleanos opacos sin razón, rule_id o severidad.

**Riesgos:** vocabulario inicial; puede requerir extensión cuando se integren aprobaciones humanas y policy matrices MIASI.

### 3.3. `src/devpilot_core/policy/path_guard.py`

**Propósito:** bloquear rutas inseguras y acciones destructivas.

**Funcionamiento:** resuelve rutas contra el project root, bloquea escapes fuera del workspace, bloquea prefijos internos como `.git`, `.venv`, `__pycache__`, `.pytest_cache`, bloquea archivos tipo `.env` y bloquea acciones destructivas como `delete`, `remove`, `rm`, `rmdir`, `overwrite`.

**Integración:** llamado por `PolicyEngine.evaluate()` y cubierto por tests unitarios.

**Rol dentro de DevPilot:** control previo para cualquier herramienta que lea/escriba archivos, aplique patches, haga refactors o inspeccione repos.

**Comandos de uso:**

```powershell
python -m devpilot_core policy check read --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check delete --path docs/00_product/product_vision.md --json
```

**Criterios PASS:** rutas internas seguras son permitidas; rutas externas, `.env`, `.git` y acciones destructivas son bloqueadas.

**Criterios BLOCK:** permitir traversal fuera del root o acciones destructivas por defecto.

**Riesgos:** primera versión con allowlist/denylist estática; requerirá política configurable por tipo de herramienta y aprobación humana.

### 3.4. `src/devpilot_core/policy/secrets.py`

**Propósito:** centralizar redacción y detección de secretos sintéticos.

**Funcionamiento:** `SecretGuard` escanea textos y payloads anidados, redacta claves sensibles (`api_key`, `token`, `secret`, `password`, `authorization`) y patrones sintéticos frecuentes (`sk-*`, `ghp_*`, `hf_*`, tokens Slack y bearer tokens). Si detecta un secreto en `policy check`, emite BLOCK.

**Integración:** se usa directamente en `PolicyEngine` y también fue integrado por compatibilidad en `EventLogger` y `ReportEngine` para centralizar redacción.

**Rol dentro de DevPilot:** evita filtraciones obvias en reportes, trazas, findings y payloads antes de habilitar agentes y APIs.

**Comandos de uso:**

```powershell
python -m devpilot_core policy check read --path docs/file.md --text "api_key=sk-1234567890abcdef" --json --write-report
```

**Criterios PASS:** el secreto no aparece en reportes o trazas; aparece `[REDACTED]`; la política bloquea la solicitud.

**Criterios BLOCK:** persistir secretos sin redacción o permitir una acción con secreto detectado.

**Riesgos:** no reemplaza scanners industriales como gitleaks/trufflehog; no detecta todos los formatos reales; debe evolucionar con entropy checks, allowlists y firmas.

### 3.5. `src/devpilot_core/policy/cost_guard.py`

**Propósito:** bloquear costos externos no autorizados.

**Funcionamiento:** `CostGuard` evalúa si una solicitud usa API externa, proveedor, costo estimado y política local de presupuesto. Por defecto bloquea APIs externas porque `.devpilot/policy.yaml` declara `external_api_allowed: false` y presupuesto `0.0`.

**Integración:** `PolicyEngine` usa `CostGuard`; CLI permite simular presupuesto con flags, pero aun así acciones `external-api` quedan bloqueadas por `PolicyEngine` hasta que exista aprobación humana real.

**Rol dentro de DevPilot:** base del futuro control de costos para `ModelAdapter`, proveedores externos, LLMs, embeddings remotos y agentes con herramientas pagas.

**Comandos de uso:**

```powershell
python -m devpilot_core policy check external-api --external-api --provider openai --estimated-cost-usd 0.01 --json
```

**Criterios PASS:** local/mock sin costo pasa; API externa sin presupuesto bloquea; presupuesto explícito genera advertencia, no ejecución.

**Criterios BLOCK:** permitir API externa sin presupuesto local o sin aprobación.

**Riesgos:** no mide consumo real; no consulta facturación; no persiste histórico de costos. Eso queda para sprints posteriores.

### 3.6. `src/devpilot_core/policy/engine.py`

**Propósito:** orquestar PathGuard, SecretGuard y CostGuard.

**Funcionamiento:** recibe `PolicyRequest`, evalúa acciones peligrosas, rutas, secretos y costos, y devuelve `CommandResult` con summary, decisions y findings. Falla cerrado cuando hay BLOCK o DENY.

**Integración:** expuesto por CLI mediante `policy check` y usado por tests.

**Rol dentro de DevPilot:** primer punto central de enforcement antes de agentes, herramientas, Git, patches y refactors.

**Comandos de uso:**

```powershell
python -m devpilot_core policy check read --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check delete --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check external-api --external-api --provider openai --estimated-cost-usd 0.01 --json
```

**Criterios PASS:** safe read pasa; delete bloquea; secret bloquea; external API bloquea; findings son auditables.

**Criterios BLOCK:** acción peligrosa permitida por defecto; API externa permitida sin CostGuard; secreto persistido sin redacción.

**Riesgos:** aún no hay aprobación humana persistente ni policy matrix MIASI ejecutable completa.

### 3.7. `src/devpilot_core/policy/__init__.py`

**Propósito:** exponer API pública del paquete policy.

**Funcionamiento:** reexporta `PolicyEngine`, `PolicyRequest`, guards, policies y helpers de redacción.

**Integración:** usado por CLI, EventLogger, ReportEngine y tests.

**Rol dentro de DevPilot:** boundary público para seguridad operativa.

**Criterios PASS:** imports estables desde `devpilot_core.policy`.

**Criterios BLOCK:** ciclos de importación o API pública inconsistente.

**Riesgos:** API inicial; puede expandirse con MIASI Policy Matrix.

### 3.8. `tests/test_policy_engine.py`

**Propósito:** validar seguridad determinística de Sprint 09.

**Funcionamiento:** cubre PathGuard, SecretGuard, CostGuard, PolicyEngine, CLI JSON, redacción de reportes y bloqueo de APIs externas.

**Integración:** se ejecuta con `pytest -q`.

**Rol dentro de DevPilot:** quality gate de seguridad operativa.

**Criterios PASS:** todas las pruebas pasan y la suite completa queda en PASS.

**Criterios BLOCK:** cualquier regresión que permita path escape, secretos, acciones destructivas o API externa sin política.

**Riesgos:** no cubre aún fuzzing, red teaming, concurrencia ni reglas configurables avanzadas.

### 3.9. `docs/functional_sprint_09_manifest.json`

**Propósito:** manifiesto máquina-legible del sprint.

**Funcionamiento:** lista archivos, comandos, criterios PASS/BLOCK, pruebas y riesgos.

**Integración:** complementa este audit y el backlog funcional.

**Rol dentro de DevPilot:** trazabilidad docs-as-code.

**Criterios PASS:** JSON válido y coherente con código.

**Criterios BLOCK:** inconsistencia entre manifiesto, código y pruebas.

**Riesgos:** debe mantenerse si el sprint se endurece después.

## 4. Componentes modificados

### 4.1. `src/devpilot_core/cli.py`

Agrega comando `policy check`, flags de PathGuard/SecretGuard/CostGuard y emisión de reportes/eventos. Mantiene compatibilidad con comandos previos.

### 4.2. `src/devpilot_core/observability/events.py`

Centraliza redacción a través de `SecretGuard`, manteniendo wrappers compatibles con Sprint 07.

### 4.3. `src/devpilot_core/reports/report_engine.py`

Redacta payload JSON y Markdown antes de persistir evidencia.

### 4.4. `.devpilot/project.yaml`

Agrega referencia a `.devpilot/policy.yaml` dentro de `paths.policy`.

### 4.5. `src/devpilot_core/workspace/manager.py`

Actualiza el renderizado inicial de `project.yaml` para incluir `paths.policy`.

### 4.6. `README.md`, `docs/05_operations/runbook.md`, `docs/functional_backlog_after_precode.md`

Sincronizan el estado funcional, comandos nuevos, riesgos, criterios PASS/BLOCK y siguiente sprint.

## 5. Comandos de verificación

```powershell
python -m pytest -q
python -m devpilot_core --version
python -m devpilot_core workspace status --json
python -m devpilot_core standards status --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core policy check read --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check delete --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check read --path docs/file.md --text "api_key=sk-1234567890abcdef" --json --write-report
python -m devpilot_core policy check external-api --external-api --provider openai --estimated-cost-usd 0.01 --json
```

## 6. Resultado de pruebas

```text
pytest -q -> 63 passed, 0 failed, 0 errors, 0 skipped
```

## 7. Decisión ADR

No se abre nueva ADR porque el sprint implementa una capacidad prevista explícitamente en el backlog y no introduce dependencias externas, APIs reales, nuevos proveedores, persistencia estructural, agentes, herramientas destructivas ni cambio arquitectónico. Sí deberá evaluarse ADR futura si se agregan RBAC/IAM, firma de políticas, configuración cifrada, aprobación humana persistente, integración real con proveedores o budgets persistentes.

## 8. Limitaciones y evolución industrial

Esta es una primera versión de seguridad operativa determinística. Para un nivel industrial debe evolucionar hacia:

- policy matrix MIASI ejecutable;
- aprobación humana persistente;
- SecretGuard con entropy checks y scanner especializado;
- CostGuard con histórico local, presupuestos por proveedor y reconciliación;
- PathGuard configurable por tool/agent;
- pruebas de red teaming y fuzzing;
- persistencia SQLite/EventStore;
- integración con Agent/Tool Registry.
