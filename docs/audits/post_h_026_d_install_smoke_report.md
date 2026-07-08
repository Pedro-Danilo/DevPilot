---
doc_id: "DEVPL-AUDIT-POST-H-026-D-INSTALL-SMOKE"
title: "POST-H-026-D — Local install and run verification report"
version: "1.0.0"
status: "approved"
owner: "Ordóñez"
phase: "POST-FASE-H"
sprint: "POST-H-026-D"
updated: "2026-07-08"
---

# POST-H-026-D — Local install and run verification report

## Decisión

`POST-H-026-D` queda implementado como `implemented-initial / read-only-install-run-preflight`.

## Alcance implementado

Se agregó `LocalInstallSmokeRunner` para validar instalabilidad y arranque local sin crear entornos, ejecutar instaladores ni abrir sockets. El smoke revisa metadata Python, entrypoint `python -m devpilot_core`, receta editable, checklist operador, perfil RC, Web UI smoke local, política de paquete limpio y no-go gates.

## Comando operativo

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core release-candidate install-smoke --json
python -m devpilot_core release-candidate install-smoke --json --write-report
python -m devpilot_core schema validate --schema-id LocalInstallSmokeReport --instance outputs/reports/local_install_smoke_report.json --json
```

## Seguridad

- No ejecuta `pip`.
- No ejecuta `npm`.
- No ejecuta subprocess.
- No abre sockets.
- No usa red ni APIs externas.
- No habilita remote execution, connector write ni plugin execution.
- No muta fuentes.
- Los reportes runtime se escriben solo con `--write-report`.

## Límites

Esta primera versión no publica wheel/sdist, no crea instalador MSI/EXE, no ejecuta matriz OS y no resuelve upgrade/rollback. Esas actividades se reservan para POST-H-027. POST-H-026-E sigue siendo responsable del reporte RC final PASS/BLOCK.
