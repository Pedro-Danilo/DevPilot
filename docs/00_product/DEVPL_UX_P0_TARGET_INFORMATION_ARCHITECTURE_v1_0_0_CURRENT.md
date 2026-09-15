---
doc_id: "DEVPL-UX-P0-TARGET-IA"
title: "DevPilot UX-P0 — Target information architecture and shell contract"
status: "current"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "derived_from_approved_DEVPL-UX-P0-A"
source_repo: "repo_DevPilot_Local_431_DEVPL_UX_P0_A_AUTHORITY_DESIGN_SYSTEM_FOUNDATION_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "013cc84f0df9eff1fb750b542644bfd0c7dc8717"
source_repo_sha256: "be80b6490cbbbfc7b5827fa896cbe5528a2b2d3676fb6c2ceef672820ee2f097"
route_policy: "preserve-current-paths-and-route-ids"
---

# Target information architecture — UX-P0

## Principio

UX-P0 reorganiza cómo se presentan las rutas; no cambia su autoridad ni necesita renombrar paths/route IDs.

## Grupos

| Grupo | Rutas | Label Guided sugerido |
|---|---|---|
| Start | `/`, `/project/entry` | Inicio / Crear o abrir |
| Understand & Plan | `/project/status`, `/pre-code`, `/workspace/documents`, `/planning/roadmap` | Estado / Ingeniería / Documentos / Planificación |
| Build & Validate | `/story/code`, `/approvals`, `/jobs`, `/quality` | Implementar / Aprobaciones / Ejecuciones / Calidad |
| Release | `/release/readiness`, `/release/package`, `/release/lifecycle`, `/release/metadata`, `/release/closure` | Preparar / Empaquetar / Instalar o revertir / Versionar / Cerrar release |
| Recover | `/recovery`, `/reconciliation` | Recuperar / Resolver cambios externos |
| AI | `/ai` | IA y contexto |
| Diagnostics | `/reports`, `/traces` | Reportes / Trazas |
| Global | `/settings`, `/account`, `/help` | Configuración / Cuenta / Ayuda |

## App Shell contract

Toda ruta autenticada debe renderizar, según scope y estado:

1. Global navigation por grupos.
2. Project Context Strip cuando exista proyecto activo.
3. Breadcrumb/location.
4. Current stage/state.
5. Authoritative next action o explicación fail-closed de por qué no existe.
6. Workbench content.
7. Evidence/Diagnostics progressive disclosure.
8. Notification/recovery feedback cuando exista operación larga, stale state o revalidation.

## Guided vs Expert

Guided muestra primero:

- qué está pasando;
- qué falta;
- blocker y razón comprensible;
- acción siguiente;
- efecto de la acción.

Expert añade:

- route ID/path;
- reason codes;
- policy/authority diagnostics;
- hashes/evidence/provenance;
- runtime/TTL/technical metadata.

La autoridad es idéntica.

## No-go

- no duplicate routes para Guided/Expert;
- no browser-only project state;
- no ocultar blockers;
- no cambiar route IDs para obtener labels mejores;
- no crear un dashboard paralelo que duplique Project Status.

## Risks and limitations

- UX-P0-B implements this grouping in the authenticated App Shell while preserving the current route IDs/paths and guards.
- UX-P0-C/D may refine labels and content hierarchy without changing authority.
- Changing labels/groupings must never change route IDs, guards, RBAC or server authority.

## PASS/BLOCK

**PASS:** every proposed group maps only to existing current routes and preserves route IDs/paths.

**BLOCK:** target IA implies new authority, bypasses a project/auth guard, or silently removes a critical surface.

## Verification commands

```text
cd ui/web && npm run test:route-enforcement
python -m pytest tests/test_devpl_ux_p0_a_foundation_contracts.py -q
```

