# POST-H-016-B — Workspace isolation validator

Estado: `implemented-initial`.

## Alcance

POST-H-016-B agrega `WorkspaceIsolationValidator`, un validador local read-only para comprobar que cada workspace registrado mantiene sus rutas críticas dentro de su propia frontera:

```text
- root_path
- project_file
- state_path
- reports_path / outputs_path
- traces_path
- secrets_path como referencia metadata-only
```

El validator usa `MultiworkspaceRegistryV2` como entrada compatible y `PathGuard` para confirmar que las rutas registradas no escapan del repo local permitido.

## Comando

```powershell
python -m devpilot_core workspace isolation-check --json --write-report
```

El reporte generado se escribe en:

```text
outputs/reports/workspace_isolation_report.json
outputs/reports/workspace_isolation_report.md
```

Estos outputs son evidencia runtime regenerable y no se versionan ni se incluyen en ZIPs limpios.

## Controles

```text
- No lee .devpilot/devpilot.db.
- No lee providers/secrets.
- No usa red.
- No usa APIs externas.
- No ejecuta shell.
- No habilita remote execution.
- No habilita connector write.
- No habilita plugin execution.
- No muta fuentes.
```

## BLOCK

El comando bloquea si detecta:

```text
- state_path fuera del workspace root;
- reports_path/outputs fuera del workspace root;
- traces_path fuera del workspace root;
- secrets_path fuera del workspace root;
- referencias cruzadas hacia otro workspace registrado;
- colisiones de state/reports/traces entre workspaces.
```

## Límites

Esta versión no endurece todavía `portfolio status` ni expone API dedicada. POST-H-016-C cubre portfolio status hardening y POST-H-016-D cubre integración CLI/API segura.
