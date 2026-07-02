---
doc_id: "POST-H-024-C-PROJECT-BOOTSTRAP-REPORT"
title: "POST-H-024-C — Project bootstrap dry-run report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-024-C"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-024-C — Project bootstrap dry-run report

## 1. Resultado

POST-H-024-C queda implementado como **implemented-initial / bootstrap-dry-run**.

Se agrega un workflow local-first para planificar y ejecutar de forma controlada el bootstrap inicial de un proyecto nuevo a partir de los templates de POST-H-024-B.

## 2. Alcance real implementado

```text
- ProjectBootstrapReport schema.
- ProjectBootstrapPlanner.
- CLI: python -m devpilot_core workspace bootstrap.
- Plan de archivos para .devpilot/project.yaml.
- Plan de documentos pre-code.
- Plan de registries MIASI iniciales.
- Modo dry-run por defecto.
- Modo execute explícito, acotado al target workspace.
- Rechazo de overwrite por defecto.
- Reporte JSON/Markdown cuando --write-report es explícito.
```

## 3. Ajuste industrial aplicado

El backlog pedía `workspace/bootstrap.py`, dry-run/execute y `project_bootstrap_report.json`. Para evitar que el comando se convirtiera en scaffolding riesgoso, el sprint se acotó así:

```text
- default target bajo outputs/bootstrap_workspaces/<project-id>;
- PathGuard sobre target y archivos planificados;
- SecretGuard sobre contenido planificado;
- no overwrite por defecto;
- no generación de código productivo;
- no uso de red, APIs externas, conectores write, plugins ni remote execution;
- ProjectBootstrapReport versionado y validable por schema.
```

## 4. Artefactos principales

```text
docs/schemas/project_bootstrap_report.schema.json
src/devpilot_core/workspace/bootstrap.py
src/devpilot_core/cli_commands/workspace.py
src/devpilot_core/cli.py
tests/test_post_h_024_project_bootstrap.py
docs/post_h_024_c_manifest.json
```

## 5. Comandos operativos

```powershell
python -m devpilot_core workspace bootstrap --project-id ventas-micro-local --project-name "Sistema agent-assisted de ventas e inventario para microemprendimientos locales" --dry-run --json --write-report
python -m devpilot_core schema validate --schema-id ProjectBootstrapReport --instance outputs/reports/project_bootstrap_report.json --json
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_024_project_bootstrap.py tests/test_post_h_024_project_templates.py tests/test_project_global_state.py -q
```

## 6. Criterios PASS/BLOCK

PASS:

```text
- dry-run no escribe archivos de workspace;
- execute escribe solo bajo el target permitido;
- execute rechaza overwrite por defecto;
- ProjectBootstrapReport valida contra schema;
- safety flags mantienen red/APIs/remote/connectors/plugins en false.
```

BLOCK:

```text
- project_id inválido;
- target fuera de prefijos permitidos por PathGuard;
- path planificado escapa del target workspace;
- archivo existente detectado en execute;
- contenido planificado contiene material tipo secreto;
- templates POST-H-024-B no son válidos.
```

## 7. Límites explícitos

```text
POST-H-024-C no implementa readiness preview.
POST-H-024-C no integra quality gate de onboarding.
POST-H-024-C no crea fixture piloto productivo.
POST-H-024-C no genera código de aplicación.
POST-H-024-C no habilita red ni APIs externas.
```

La readiness preview queda para POST-H-024-D y el quality gate/fixture piloto queda para POST-H-024-E.
