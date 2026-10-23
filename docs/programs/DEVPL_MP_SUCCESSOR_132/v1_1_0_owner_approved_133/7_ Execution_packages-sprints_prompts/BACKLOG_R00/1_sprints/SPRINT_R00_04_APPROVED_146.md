---
doc_id: SPRINT-MP132-R00-04-134
version: 1.0.1
status: SPRINT_EXECUTION_APPROVED
approval_scope: R00_04_AUDIT_ONLY_OWNER_EXPLICIT_APPROVAL
program_authority: DEVPL-MP-SUCCESSOR-132/OWNER-133
requires_owner_sprint_approval: false
execution_authority: true
source_mutation_authorized: false
---
# R00-04 — Auditoría focal de Configuración, UX-P1, métricas y hardware

## A. Objetivo

Producir un diagnóstico reutilizable para R1/R2 sobre autoridad efectiva de Settings, políticas/modelos/proveedores, hallazgos UX y disponibilidad local real, **sin refactorizar ni ejecutar modelos**. La auditoría comienza con el HEAD sucesor acreditado en R00-03: si no existe `G-R00-03 PASS`, **BLOCK**. Este sprint no sustituye los futuros ADRs/contratos aprobados ni les asigna implementaciones sin revisión focal.

## B. Entradas y cobertura del backlog

`MP132-R0-08`, `MP132-R0-09`, `MP131-R0-05` y policy `MP131-R0-04`; programa v132 Owner-133, ADR-007/ADR-011, `CONFIGURATION_AUTHORITY_MATRIX_132.md`, `MODEL_CAPABILITY_AND_EVAL_CONTRACT_132.md`, `3_gobernanza/03_LEDGER_UX_Y_POLITICA_DE_ABSORCION_132.md`, ledger v1.32 **sin convertirlo automáticamente en bug actual**. Hardware/OS/provider health inspección read-only local, cero solicitudes de inferencia o red externa.

## C. Secuencia de auditoría

1. Registrar HEAD actual, ruta de trabajo B o A y paridad remota; abrir fuente `SettingsView.ts`, `settings_service.py`, Project/Policy/Providers, runtime controls, endpoints, schemas, RBAC, approvals, tests y UI Guided/Expert. Seguir `UI → API → application → store/policy/runtime → traces`.
2. Construir una **matriz por setting**: scope (`installation/workspace/project/session/runtime`), origen/default/valor efectivo, precedencia, owner, persistencia, control UI, permiso, efectos, restart, rollback, secretos y deny global no sobreescribible.
3. Reproducir **siempre que sea seguro** evidencias UX S2 registradas: `UX-P1-02-B01-004`, `UX-P1-02-B01-006`, `CAP-13B01-SETTINGS-001`, `UX-P1-MP0F-001`; identificar correctivo MP-0F progressive disclosure ya implementado y **no marcar pendiente como si no existiera**. No exigir screenshots si no hay superficie disponible; registrar `NOT_REPRODUCED` y causa en lugar de concluir PASS.
4. Contrastar estado pre-proyecto y setup global, Model Gateway, local providers health, Agent Runtime, RAG/evals, runtime kill/revoke y configuración de proyecto. Separar vista informativa, ajuste persistent, plan-only y acción runtime.
5. Medir en ambiente disponible, sin inventar hardware ni latencias: versión SO, RAM/CPU/GPU detectables con permiso, Python/Node, presencia **sin ejecución** de Ollama/LM Studio, modelos declarados, build cache, baseline de pytest/tests existentes (sin full regression), tamaño del bundle UI, navegación/scroll y evidencia browser si el owner lo autoriza.
6. Recopilar ledger UX v1.32 por IDs con `CLOSED_HISTORICAL`, `OPEN_REPRODUCED`, `NOT_REPRODUCED`, `NOT_TESTED`, `CAPABILITY_GAP`; identificar S0/S1 funcional nuevos y **bloquear con corrective específico** cuando exista una violación contractual real.
7. Proponer slices R1 Settings: IA nav/readiness, effective configuration y persistence, model health/selection; señalar riesgos de ejecutar todo el UI refactor en una unidad y no aprobar cambios aquí.

## D. Entregables

`R00_04_SETTINGS_AUTHORITY_MATRIX.md`, `R00_04_SETTINGS_REUSE_DELTA_MAP.md`, `R00_04_UX_FINDINGS_RECONCILIATION.md` con IDs originales, `R00_04_HARDWARE_AND_MODEL_AVAILABILITY.json` (NOT_AVAILABLE permitido), `R00_04_BASELINE_METRICS.md`, `R00_04_R1_READINESS_RECOMMENDATIONS.md`, checkpoint, ZIP evidencia SHA y guía única si aplica operador. Evidencia sin claves ni tokens, sin fingerprint personal innecesario ni datos de cliente.

## E. Gate

`G-R00-04 SETTINGS_RISK_AUDITED`: PASS si cada hallazgo tiene estado justificado, los boundaries Settings han sido auditados sobre código real, métricas tienen método y entorno o `NOT_MEASURED`, riesgos P0 están priorizados y se propone **NO-OP** cuando corresponda. Puede cerrarse aunque no haya modelo local instalado: registrar `LOCAL_MODEL_NOT_AVAILABLE`, sin declarar L aceptado; si hay defecto funcional S0/S1, BLOCK y abrir corrective acotado, no realizarlo furtivamente en R00-04.

No hay source writes, network, installs, API paid, activación agents, DB writes, Git promotion ni Full Regression por defecto. R00-05 usa el informe resultante para el gate M0.

---
## Rebind de ejecución COR-146 (siguiente al G-R00-03)

- Aprobación individual Owner otorgada explícitamente en el prompt del 14-10-2026; limita ejecución a la auditoría focal, sin source writes.
- Baseline exacto acreditado: `77cdf9af323decc09e33cebad2169863e3b86e1a`, `evolution/multiprovider-v2`, `D:\Projects\DevPilot_Local`.
- `G-R00-03 AUTHORITY_REBOUND_WINDOWS_PASS` precede R00-04; validación incluye evidencia COR-145 y los ZIP/SHA.
- Configuración y ADR-007/011 de Owner-133 permanecen contratos de diseño; la auditoría no los convierte en funciones implementadas.
- `ledger_v1_32_MP0F_REB117_INTEGRADO.md` no fue identificado por esa ruta en el Git archive R00-03; se usan los IDs y el ledger 13-B presentes y se declara fuente histórica pendiente de localización, sin inventar contenido.
- Implementación de R00-04: auditor `audit146.py` en carpeta externa, fases inspect/inventory/verify/package, validación focal, evidencia fuera del repositorio; no se hacen commits/push.
- Windows valida estado Git vivo y revisiones humanas cuando sean posibles; si UI no está disponible, registrar NOT_TESTED, nunca PASS de UX.
- Gate de salida sigue pendiente de evaluación Owner de la evidencia Windows.
