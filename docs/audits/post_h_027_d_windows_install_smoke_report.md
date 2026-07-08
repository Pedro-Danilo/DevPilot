---
doc_id: "POST-H-027-D-WINDOWS-INSTALL-SMOKE-AUDIT"
title: "POST-H-027-D — Windows install guide and smoke"
status: "approved"
owner: "Ordóñez"
created: "2026-07-08"
updated: "2026-07-08"
version: "1.0.0"
approval: "approved-by-owner"
sprint: "POST-H-027-D"
source_of_truth: true
machine_readable_pair: "docs/post_h_027_d_manifest.json"
---

# POST-H-027-D — Windows install guide and smoke

## Resultado

Estado: `implemented-initial`.

POST-H-027-D agrega un smoke local-first para la ruta de instalación Windows del operador. El nuevo comando:

```powershell
python -m devpilot_core install windows-smoke --mode editable --json --write-report
```

produce `WindowsInstallSmokeReport` bajo `outputs/reports/windows_install_smoke_report.json` solamente cuando se solicita `--write-report`.

## Alcance verificado

- Flujo editable, wheel y ZIP documentados en `docs/05_operations/install_guide.md`.
- Validación de artefactos wheel/ZIP locales dentro del workspace.
- CLI mínima documentada: version, schema list, project-state, docs-governance y artifact manifest.
- API local documentada con token y host `127.0.0.1`.
- `npm --prefix ui/web test` queda como smoke frontend; si Node/npm no están disponibles, se clasifica como advisory y no bloquea core Python.
- Runtime artifacts no versionables documentados: `node_modules`, `outputs/`, `dist/`, `.venv/`, `.pytest_cache` y `__pycache__`.

## Safety

El smoke no crea venv, no ejecuta `pip`, no ejecuta `npm`, no abre sockets, no requiere privilegios elevados, no publica, no despliega, no llama red ni APIs externas y no muta archivos fuente. Los únicos archivos opcionales se generan bajo `outputs/reports` con `--write-report`.

## Limitaciones

Esta es una primera versión operativa para Windows. No crea MSI, no instala Python/Node, no configura servicios Windows, no implementa auto-update y no cubre upgrade/rollback. El dry-run de upgrade/rollback permanece en POST-H-027-E.
