---
doc_id: "POST-H-019-PLUGIN-METADATA-RUNBOOK"
title: "POST-H-019 — Runbook metadata-only para plugins"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
local_first: true
dry_run: true
plugin_execution_enabled: false
---

# POST-H-019 — Runbook metadata-only para plugins

## 1. Propósito

Este runbook define la operación segura del ecosistema de plugins de DevPilot al cierre de `POST-H-019`.

El estado vigente es **metadata-only / validator-only / dry-run**. Un plugin registrado puede describir capacidades, permisos declarativos y vínculos de metadatos, pero no puede ejecutar código, instalar dependencias, acceder a red, escribir archivos ni operar como extensión runtime.

## 2. Estado de cierre

| Capacidad | Estado | Observación |
|---|---|---|
| Plugin registry | `implemented-initial` | Metadata declarativa local. |
| Threat model | `approved` | Amenazas y no-go gates definidos. |
| Sandbox design | `approved` | Diseño metadata-only, sin ejecución. |
| Permission model | `implemented-initial` | Deny-by-default; permisos críticos bloqueados. |
| Install dry-run | `implemented-initial` | Simulación metadata-only. |
| Exposure report | `implemented-initial` | Evidencia local; no autorización de ejecución. |
| Quality gate | `implemented-initial` | Subgate `plugin-sandbox-design`. |
| Plugin execution | `blocked-by-design` | Requiere ADR futura. |

## 3. Operación segura

Comandos permitidos:

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core plugin validate --json
python -m devpilot_core plugin dry-run --all --dry-run --json --write-report
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
```

Los reportes generados bajo `outputs/reports/` son evidencia operacional local y no son fuente versionable.

## 4. No-go gates

```text
NO-GO si se ejecuta código de plugin.
NO-GO si se importa dinámicamente un módulo de plugin con importlib.
NO-GO si se inicia subprocess/shell desde un plugin.
NO-GO si se ejecuta pip install o un package manager para plugins.
NO-GO si se habilita marketplace o descarga de plugins.
NO-GO si se usa red o API externa para descubrir/ejecutar plugins.
NO-GO si un plugin escribe archivos de workspace, estado o outputs por sí mismo.
NO-GO si un manifest válido se interpreta como permiso de ejecución.
NO-GO si el exposure report se interpreta como autorización de ejecución.
```

## 5. ADR trigger para futura ejecución de plugins

Cualquier propuesta futura para habilitar `plugin execution` debe crear una ADR nueva antes de implementar código. Esa ADR debe incluir, como mínimo:

| Requisito | Criterio mínimo |
|---|---|
| Sandbox técnico | Aislamiento explícito del runtime, límites de CPU/memoria/tiempo y filesystem. |
| RBAC | Roles autorizados por acción, plugin, workspace e interfaz. |
| Approvals | Aprobación humana fuerte con binding a actor, acción, plugin, comando y hash de alcance. |
| Permission model | Deny-by-default, permisos mínimos, permisos críticos con `blocked_until` removido solo por ADR. |
| Tests | Unit, integration, red-team, evals plugin-ecosystem, rollback y fixtures negativos. |
| Observabilidad | Eventos auditables, redacción de secretos, trazas de ejecución y retención definida. |
| Rollback | Desactivación del plugin, reversión de estado, cuarentena y plan de recuperación. |
| Seguridad de supply chain | Pinning, checksums, firma local o mecanismo equivalente, sin marketplace implícito. |
| Operación | Runbook de incidentes, límites de costo, dry-run y kill-switch. |
| Quality gate | Subgate actualizado que bloquee cualquier no-go incumplido. |

Sin ADR aprobada, `plugin.code.execute`, `plugin.dynamic_import`, `plugin.subprocess.run`, `plugin.network.access`, `plugin.filesystem.write` y `plugin.dependency.install` deben permanecer `effect=deny`.

## 6. Criterios PASS

```text
PASS si plugin validate termina ok.
PASS si plugin dry-run --all produce execution_allowed_total=0.
PASS si quality-gate hardening incluye plugin-sandbox-design y pasa.
PASS si test-contracts validate y validate-v2 reconocen el contrato post-h-019-plugin-sandbox-design.
PASS si project-state apunta a POST-H-020 después del cierre.
PASS si README, runbook general, backlog y changelog declaran POST-H-019 cerrado como implemented-initial.
```

## 7. Criterios BLOCK

```text
BLOCK si cualquier documento declara plugin execution disponible.
BLOCK si el runbook contiene pasos de ejecución real de plugins.
BLOCK si se sugiere pip install automático o marketplace.
BLOCK si se omite ADR futura para plugin execution.
BLOCK si quality-gate hardening no evalúa plugin registry, permission model y exposure report.
BLOCK si TCR v1/v2 no cubre el cierre del hito.
```

## 8. Riesgos y limitaciones

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Sobredeclarar plugins ejecutables | Crítica | Runbook y quality gate declaran metadata-only. |
| Dependency confusion | Alta | `pip install` y marketplace bloqueados. |
| Exfiltración de secretos | Alta | Red/API externa bloqueadas; SecretGuard sigue siendo requisito futuro. |
| Escritura no controlada | Alta | Filesystem write por plugins bloqueado. |
| Drift documental | Media | Docs governance, TCR y project-state sincronizados. |

Esta versión es `implemented-initial`. No reemplaza un sandbox real de ejecución, ni una revisión de seguridad externa, ni un sistema formal de firma/certificación de plugins.
