---
doc_id: "DEVPL-GSDLC-11-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-11-B — Reproducibility, source package, checksum and SBOM implementation report"
status: "implemented/local-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-11"
approval: "local_qualification_candidate"
---

# 1. Objetivo

Implementar un workbench local de package reproducible ligado a commit/tree exactos, checksum SHA-256 y SBOM baseline, componiendo la maquinaria POST-H-017/026/027 existente y sin crear una segunda pila de packaging.

# 2. Baseline y política FRX-v2.4

- Fuente de ejecución: `repo_DevPilot_Local_421_DEVPL_GSDLC_11_A_RELEASE_READINESS_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Commit: `01c28e73994b74699802dcbac9bb06d686841b89`.
- SHA-256: `e105736c539f37ea3ad81b96ad571149035c5bb77602e0303018f304c04e8955`.
- GSDLC-11-A permanece `CLOSED/PASS/WINDOWS-VALIDATED`.
- GSDLC-11-B usa focal + acumulativa + Test Impact; Full Regression = **0**.
- Budget de la ola: **0/1**, reservado para 11-E salvo hard trigger owner-approved.
- FRX-v2.4-A: facts históricos se congelan en snapshots/`*_at_close`; no se fuerzan contra punteros current-active.
- FRX-v2.4-B: el profile `frx-v2.4-current` sigue siendo la autoridad de la única Full futura; 11-B no la consume.

# 3. Arquitectura implementada

`ReleasePackageJobApplicationService` expone operaciones tipadas `status → plan(dry-run) → execute(exact-plan-bound)`. El servicio resuelve la autoridad Git limpia, bloquea drift commit/tree entre plan y execute, y compone `PackageBuildBuilder`, SourceZip policy, `ReleaseManifestBuilder`, `ReleaseSbomBuilder`, artifact manifest y reproducibility verifier. No acepta shell arbitrario ni paths/commits suministrados por browser.

`PackageBuildBuilder` se endurece para ZIP byte-reproducible mediante orden estable, timestamps/metadatos ZIP canónicos y bloqueo fail-closed de symlink/junction/path escape incluido. La ejecución escribe solo artefactos locales excluidos de source (`dist/` y `outputs/`).

# 4. Artefactos de release

La ejecución gobernada produce `release_artifact_manifest.json`, sidecars SHA-256, SBOM baseline, release manifest y comparison report de reproducibilidad. Dos derivaciones equivalentes del mismo source authority deben producir el mismo SHA-256 del package; SBOM se compara semánticamente excluyendo noise temporal permitido.

El SBOM es una **primera versión/baseline de inventario de dependencias**: no equivale a SCA, certificación de vulnerabilidades, licencias, compliance o supply-chain attestation completa. Estas capacidades requieren evolución posterior.

# 5. API/UI y autoridad

- API: `GET /api/v1/release/package`, `POST /api/v1/release/package/plan`, `POST /api/v1/release/package/execute`.
- Session humana + workspace scope server-side.
- Plan/execute: solo `owner` o `release-manager`.
- UI: `/release/package`, con estado, plan dry-run, commit/tree, checksum, SBOM, reproducibilidad y provenance.
- Browser no obtiene source/Git/publish/deploy/tag/signing authority.
- No network ni API externa.

# 6. Reconciliación documental y contractual

El backlog/prompt se rebindean a repo421. Project State, Source Registry, README, roadmap, release criteria, route/RBAC/UI/capability registries, schemas y TCR/Test Impact evolucionan conjuntamente. El contrato de cierre de 11-A se convierte en `historical-freeze` sobre facts `*_at_close` en vez de pinnear punteros current-active.

Durante la calificación local se detectó y corrigió drift determinista antes del bundle Windows: los nuevos POST `/release/package/*` carecían inicialmente de `mutation_exception_justification`, el OpenAPI estático aún no incluía los tres endpoints y los source markers `ui.release-package` faltaban en client/types. Todos fueron reconciliados y los guards de API/UI pasan.

# 7. Validación local

- GSDLC-11-B funcional/contract: **8/8 PASS**.
- API security: **21/21 PASS**.
- API route contracts: **6/6 PASS**.
- API contract drift: **8/8 PASS**.
- UI route enforcement: **8/8 PASS**.
- PackageBuilder: **4/4 PASS**.
- ReleaseManifest: **11/11 PASS**.
- Release SBOM: **4/4 PASS**.
- POST-H-017 reproducibility pack/schema/verify: **19/19 PASS**.
- POST-H-027 artifact-manifest/checksum: **7/7 PASS**.
- POST-H-027 source ZIP policy: **8/8 PASS** en ejecuciones segmentadas; el test de build/policy es costoso y no se duplicó después de acreditar PASS.
- UI static smoke GSDLC-11-B: **8/8 PASS**.
- Full Regression: **0**.

# 8. Riesgos y limitaciones

1. 11-B es la primera UI gobernada de reproducible package/SBOM; instalación/upgrade/rollback pertenecen a 11-C.
2. SBOM baseline no hace análisis de vulnerabilidades/licencias/compliance.
3. Signing/publication/remote distribution continúan fuera de alcance.
4. La aceptación browser Windows debe demostrar plan-before-execute, exact commit binding, checksum/SBOM/reproducibility visibles y ausencia de publish/deploy.
5. Packaging del repo completo puede ser costoso; el operador debe reutilizar evidencia PASS hash-bound y no repetir ejecución por correctives que no cambien esta superficie.

# 9. PASS/BLOCK

**PASS local:** focal/contratos/guards/UI smoke/impact y reconciliación sin S0/S1, Full=0.

**PASS Windows pendiente:** browser real + package job exact-plan PASS + artifacts/hash/SBOM/reproducibility evidence + clean Git + package final.

**BLOCK:** forbidden/secret/path escape, commit/tree drift, hash mismatch, package no reproducible, SBOM inválido, role/scope bypass, publish/network, S0/S1 o Full ejecutada en 11-B.
