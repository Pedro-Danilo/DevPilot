---
title: "Auditoría FUNC-SPRINT-94 — Multiworkspace Manager y portfolio local"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-94"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-19"
approval: "implemented-initial"
---

# Auditoría FUNC-SPRINT-94 — Multiworkspace Manager y portfolio local

## Estado

`implemented-initial`. La implementación habilita registro local de workspaces, validación de aislamiento y portfolio status read-only. No habilita SaaS, RBAC, autenticación remota, sincronización cloud, lectura cruzada de bases SQLite ni lectura de secretos.

## Propósito

Permitir que DevPilot administre un portfolio local de workspaces registrados sin mezclar configuración, estado, reportes, trazas ni secretos entre proyectos.

## Alcance implementado

- Multiworkspace Registry local en `.devpilot/workspaces/workspace_registry.json`.
- Schema `docs/schemas/multiworkspace_registry.schema.json`.
- CLI `workspace register`, `workspace list`, `workspace select`, `workspace registry-validate`.
- CLI `portfolio status` en modo read-only.
- Suite de evaluación `multiworkspace-isolation`.
- Bindings MIASI para registry, selección, portfolio e aislamiento.
- Sin lectura de `.env`, providers reales, secretos ni `.devpilot/devpilot.db`.

## Funcionamiento

El registry define workspaces explícitos y deny-by-default. Cada entrada declara rutas de estado, reportes y trazas, pero `portfolio status` solo inspecciona presencia de marcadores mínimos como `.devpilot/project.yaml`, `docs/` y `.devpilot/miasi/`. El estado SQLite se reporta como path aislado, pero no se abre ni se lee.

## Integración

La capacidad se integra con `WorkspaceManager`, `PathGuard`, `PolicyEngine`, `SecretGuard`, `SchemaValidator`, `EventLogger`, MIASI y `EvalRunner`. El quality gate consume la suite `multiworkspace-isolation` dentro del subgate de safety avanzada.

## Criterios PASS

- `workspace registry-validate --json` retorna `ok=true`.
- `workspace register --path . --json` registra de forma idempotente.
- `workspace list --json` lista metadatos públicos.
- `workspace select --workspace-id devpilot-local --json` actualiza selección local.
- `portfolio status --json` retorna read-only sin leer secretos ni DB.
- `multiworkspace-isolation` alcanza `safety_score >= 90` sin falsos negativos.

## Criterios BLOCK

- Ruta fuera del root gobernado sin política explícita.
- Workspace no registrado.
- Colisión de `.devpilot/devpilot.db` entre workspaces.
- Lectura de secretos o providers reales.
- Mezcla de reports/traces/outputs entre workspaces.
- Portfolio status con mutaciones.

## Riesgos

La versión es preliminar. No resuelve todavía identidad/RBAC, multiusuario, registry global, verificación criptográfica, locking concurrente, sincronización remota ni permisos por actor. Es una base segura para Sprint 95.

## Comandos de verificación

```powershell
python -m devpilot_core workspace registry-validate --json
python -m devpilot_core workspace register --path . --json
python -m devpilot_core workspace list --json
python -m devpilot_core workspace select --workspace-id devpilot-local --json
python -m devpilot_core portfolio status --json
python -m devpilot_core eval run --suite multiworkspace-isolation --json
python -m pytest tests\test_multiworkspace.py tests\test_sprint_94_documentation.py -q
```

## Veredicto

`FUNC-SPRINT-94` queda implementado como primera versión gobernada, local-first y read-only para portfolio. La evolución industrial debe continuar con RBAC local, actores de aprobación y audit packs.
