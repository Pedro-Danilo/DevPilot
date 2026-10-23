---
doc_id: DEVPL-MP-132-ADRS-INSTALLED-AUDIT-133
status: AUDITED_FOR_OWNER_ARCHITECTURE_ACCEPTANCE
baseline_head: "8db5b44694abcced3231183e05731e732f5b8f24"
baseline_zip_sha256: "fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8"
prior_adr_package_sha256: "b0136f245556b05687204e8ef4c3226547bb485d318e3485740e1e9d5fc94231"
---
# Auditoría focal de ADRs 132 contra código instalado y ADRs históricos

## Método y evidencia

- Snapshot código: `repo_MP_POST_G5_REBIND_8db5b44694ab_CLEAN(1).zip`, SHA `fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8`, 4510 entradas y CRC validado. Es una extracción Git limpia, **no** acceso de ejecución Windows ni prueba de remoto vivo.
- ADRs previos: `DEVPL_MULTIPROVIDER_V2_1_APPROVED_PACKAGE-AJUSTAR.zip`, ADR-001…009 APPROVED, ADR-010 DEFERRED. Leídos literalmente. Las nuevas decisiones deben convivir con controles antiguos compatibles.
- Fuentes de estándar y política inspeccionadas por rutas reales; presencia de archivo/símbolo no equivale a aceptación funcional vertical. No se ejecutó ningún test ni API ni Git sobre Windows.

## Matriz individual de compatibilidad

| Nuevo ADR | Contrato o ADR anterior | Evidencia de implementación presente | Adjudicación |
|---|---|---|---|
| ADR-MP-132-001 | ADR-MP-V2-004; estándares MIPSoftware/MIASI | `docs/standards/mipsoftware/02_ciclo_vida_software.md`, `docs/standards/miasi/03_agentic_sdlc.md`, `.devpilot/miasi/applicability_policy.json` | EXTEND: existe aplicabilidad MIASI, PESP transversal no probado implementado |
| ADR-MP-132-002 | ADR-MP-V2-003/004; ADR-MIASI-0001/0002 | `.devpilot/docs_governance/source_registry.json`, `.devpilot/docs_governance/documentation_authority_graph.json` | EXTEND: registro/autoridad existentes, Markdown durable y versionado aún no acreditados E2E |
| ADR-MP-132-003 | ADR-MP-V2-003/004; contrato lifecycle | `src/devpilot_core/application/artifact_lifecycle_service.py`, `.devpilot/artifacts/artifact_lifecycle_policy.json` | EXTEND: inmutabilidad y lineage probados parcialmente, impact graph completo pendiente |
| ADR-MP-132-004 | ADR-MP-V2-002/005/007 | `src/devpilot_core/generation/runtime.py`, `src/devpilot_core/generation/contracts.py`, `src/devpilot_core/modeling/provider_credentials.py` | KEEP+ADAPT: matriz provider existente; L real y equivalente fallback no aceptados E2E |
| ADR-MP-132-005 | ADR-MP-V2-001/003/007 | `src/devpilot_core/generation/contracts.py`, `src/devpilot_core/application/story_implementation_candidate_service.py`, `src/devpilot_core/application/workspace_git_operations_service.py` | ADAPT: historia compatibilidad y kernel candidato no integrados universalmente |
| ADR-MP-132-006 | ADR-MP-V2-009 | `src/devpilot_core/interfaces/api/routers/project_entry.py`, `src/devpilot_core/generation/dependencies.py` | EXTEND: proyecto neutral/scaffold gobernado; layout portátil objetivo no probado |
| ADR-MP-132-007 | ADR-MP-V2-005/007; security/policy | `src/devpilot_core/application/settings_service.py`, `src/devpilot_core/application/model_gateway_settings_service.py`, `ui/web/src/pages/SettingsView.ts` | ADAPT: Settings existente denso read-only/plan-only y runtime control mezclados |
| ADR-MP-132-008 | ADR-MP-V2-008 (supuesto fork/sync obsoleto) | `docs/02_architecture/adrs/ADR-DEVPL-MP-POST-SYNC1-130.md`, `.devpilot/project_state.json` | SUPERSEDE supuesto futuro de fork/sync; aprobación B condicional a preflight |
| ADR-MP-132-009 | ADR-MP-V2-001/006/007 | `src/devpilot_core/multiagent/coordinator.py`, `.devpilot/agents/tool_call_policy.json`, `.devpilot/agents/agent_runtime_boundary.json` | KEEP+EXTEND: agentes gobernados, no habilitar acciones directas |
| ADR-MP-132-010 | ADR-MP-V2-010 DEFERRED; ADR-MP-V2-005/007 | `src/devpilot_core/modeling/provider_credentials.py`, `.devpilot/agents/tool_call_policy.json` | ACCEPT ARCHITECTURE/KEEP DEFERRED activation; egress real no acreditado |
| ADR-MP-132-011 | GSDLC UX ledger v1.32; determinismo de ADR-MP-V2-007 | `ui/web/src/pages/QualityOperationsView.ts`, `ui/web/src/pages/SettingsView.ts`, `ui/web/src/pages/ApprovalCenterView.ts` | ADAPT: divergencia visual de estados sin cambiar authority backend |

## Consecuencias de autoridad tras la aceptación

1. ADR-132-004 mantiene la **matriz D/L/E** de ADR-MP-V2-002, el fallback explícito de ADR-MP-V2-005 y los permisos determinísticos de ADR-MP-V2-007. No crear un segundo motor de apply.
2. ADR-132-008 sucede únicamente los supuestos **operativos y futuros** de ADR-MP-V2-008 sobre fork/sync previo; no borra la historia Git ni altera commits.
3. ADR-132-010 acepta fronteras de seguridad, **no** habilita E. El ADR-MP-V2-010 previo conserva `DEFERRED` en activación hasta revisión explícita de datos, costos y proveedor.
4. ADRs 001/002/003/006/007/009/011 amplían contratos existentes; su ejecución requiere Reuse/Delta Map para evitar duplicaciones, paths exactos, prueba UI/API y revisiones sucesoras si hay conflicto.
5. ADR-132-008 lleva `OWNER_ACCEPTED_CONDITIONAL_B` para la migración; preflight Windows es condición precedente a cualquier acción Git.

## Huellas SHA-256 de piezas auditadas

- `.devpilot/agents/tool_call_policy.json`: `833e01f09fa7b025a94f793533c16ea691b5509a97756cba7cf85f6de2a1b4c0`
- `.devpilot/artifacts/artifact_lifecycle_policy.json`: `a3b712f57d4acb02f633d61cb2abedf3a0d931f8523b24e616b800916b741609`
- `.devpilot/miasi/applicability_policy.json`: `0169247b776a18c0a49f058d1a65ad2197751e4793ede52202cee3510b05373e`
- `.devpilot/project_state.json`: `a08154190cc122034c31f9ea553cfffc6ca2dd1465b5ba8094fc1149de798076`
- `src/devpilot_core/application/settings_service.py`: `632bcfb5ee37845ef237ea1316d2ecf55bb8b4c1c79e3447524ad04222addceb`
- `src/devpilot_core/application/story_implementation_candidate_service.py`: `afd56f0d84f0bfce749a2b0dc7eb656f07b0d2c13be84a9f71c84de29e4082ff`
- `src/devpilot_core/generation/contracts.py`: `176e1a4ddaa677ae75e04c9c5ae1005818429d0bcb264ce1401a55ba46927347`
- `src/devpilot_core/generation/runtime.py`: `70090152e17d4b1ea48eaf9d6d141b53ec4206ef616a18675650783b4c1f23f4`

## Límites y resultado

`ADR_REVIEW_PASS_WITH_IMPLEMENTATION_GAPS`: las decisiones resultan compatibles en diseño con las fuentes examinadas; **no** se demuestra que estén implementadas. El cierre de auditoría habilita aceptación arquitectónica, no releases, providers E o source writes. Un futuro gate A0/A1 debe inspeccionar HEAD y stores Windows actuales antes del primer delta.


---

## Actualización de alcance — 15-10-2026

Este inventario describe ADRs instaladas en el HEAD original de su auditoría 133. R01-01..15 incorporó ADRs/decisiones adicionales documentadas en los bundles R01, y el gate M1 está implementado en `src/devpilot_core/maturity/r01_m1_gate.py` (no se ha inventado una nueva ADR M1). Antes de implementar R02-01 la auditoría literal debe comparar ADRs vivas del HEAD `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` con el catálogo documental y publicar el mapa de autoridad/vigencia. No actualizar historia ni completar por inferencia.
