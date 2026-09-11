---
doc_id: "DEVPL-GSDLC-10-E-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-10-E — End-to-end story cycle browser closure — post-Full corrective report"
status: "windows-full-fail-preserved/post-full-corrective-local-qualified/selective-recovery-pending"
version: "1.0.2"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "pending_windows_selective_recovery"
---
# 1. Estado de continuidad

GSDLC-10-E conserva el browser E2E ya aprobado y la única Full Regression ya consumida. La sesión `DEVPL-GSDLC-10-E-FULL-01` terminó con **3101/3101 contabilizados: 3054 PASS, 42 FAIL funcionales, 0 ERROR, 5 SKIP aprobados, 0 UNEXECUTED**. La Full original es evidencia inmutable y **no se autoriza una segunda Full**.

El corrective post-Full corrige las causas comunes de esos 42 FAIL y prepara únicamente la recuperación selectiva/composite exigida por FRX-v2.4.

# 2. Causas raíz corregidas

1. `ReleaseManifest` seguía físicamente el junction Windows `ui/web/node_modules` antes de aplicar exclusiones lógicas y podía resolver fuera del worktree. Ahora excluye primero por path lógico y trata cualquier target resuelto fuera del root como excluido, no como excepción fatal.
2. `api_route_contract_registry.schema.json`, `documentation_source_registry.schema.json` y `guided_sdlc_project_status.schema.json` no reconocían metadata/campos current-active ya emitidos por sus successors.
3. Source Registry y `local_release_candidate_criteria` mantenían punteros derivados desfasados respecto de repo419/GSDLC-10-E.
4. `ui_capability_registry` tenía contadores derivados stale (`UI-READ-ONLY=1` frente a 11 reales).
5. `package-lock.json` estaba en `0.29.0-gsdlc-09-c` mientras `package.json` estaba en `0.30.0-gsdlc-10-a`; ambos quedan sincronizados y `currentSprint=DEVPL-GSDLC-10-E`.
6. El presupuesto UI current era inferior al source real, aunque el source seguía dentro de hard ceilings ya aprobados. Se eleva únicamente `currentUiSourceBudgetBytes` a 786432 y `currentUiSingleSourceBudgetBytes` a 81920; los hard ceilings no cambian.
7. Tres tests históricos confundían hechos at-close con estado current-active mutable. Se preservan los hechos históricos en manifests/audits y las aserciones live pasan a ser successor-aware sin renombrar nodeids.

# 3. Delta acumulativo

El delta acumulativo final frente a repo419 es de **39 paths**. Test Impact v2 sobre ese delta produce **39 changed paths / 205 matched contracts / 315 recommended tests / 0 unmatched / full signal null**.

No se incluyen `.git/`, `.venv/`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`, `.devpilot/devpilot.db` ni stores runtime equivalentes.

# 4. Validación local del corrective

- contratos/punteros/schemas/históricos dirigidos: **15/15 PASS**;
- API route/Quality dependents: **11/11 PASS**;
- evidence freshness/release candidate dirigidos: **5/5 PASS**;
- ReleaseManifest: **2/2 PASS**;
- UOC011 hardening + performance smoke: **2/2 PASS**;
- performance smoke directo: **PASS**, 780609 <= 786432 y 78604 <= 81920;
- Test Impact v2: **PASS 39/205/315/0**;
- Full adicional ejecutada: **0**.

Los tests lentos que encapsulan flujos completos de Agent/Release quedan dentro del exact selective recovery de los 42 nodeids en Windows; no se reemplazan por una regresión general local.

# 5. Recovery Windows requerido

El bundle v1.0.7 debe: verificar la Full original 1/1 y sus hashes; retirar únicamente el junction runtime `ui/web/node_modules` cuando sea realmente junction/symlink; aplicar y commitear el corrective exacto; ejecutar los **42 nodeids originales completos aunque un chunk falle**; si 42/42 pasan, ejecutar bounded impact, Historical Regression Guard y gates determinísticos; luego aplicar closure, fast-forward local, empaquetar repo420/components y sellar evidencia incluyendo la sesión Full original.

# 6. Riesgos y límites

- La Full histórica seguirá mostrando FAIL; el cierre correcto es `PASS/COMPOSITE-FULL-PLUS-SELECTIVE-RECOVERY`.
- Ningún corrective puede reabrir browser E2E ni lanzar otra Full.
- Si queda un residual en los 42 exactos o en bounded impact/guard, 10-E permanece BLOCK y debe conservarse evidencia para un nuevo corrective focal.
- El ajuste de presupuesto UI consume el hard ceiling actual; crecimiento UI posterior requerirá reducción/refactor o una decisión explícita, no un aumento automático.

# 7. PASS/BLOCK

**PASS:** Full original intacta; corrective hash-bound; 42/42 exact PASS; bounded impact PASS; Historical Regression Guard PASS; gates post-recovery PASS; Full lógica total=1; segunda Full=0; S0/S1=0; closure/promotion/package coherentes.

**BLOCK:** Full original alterada o ausente; recuentos/hashes distintos; segunda Full; junction físico borrado como si fuera link; cualquier residual FAIL/ERROR; autoridad current-state incoherente; secretos/runtime stores empaquetados.
