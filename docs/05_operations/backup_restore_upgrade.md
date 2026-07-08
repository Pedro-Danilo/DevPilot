---
doc_id: DEVPL-OPS-BACKUP-RESTORE-UPGRADE-001
title: DevPilot Local — Backup, restore y upgrade local
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-07-08
approval: approved_after_func_sprint_83_validation
sprint: POST-H-027-E
phase: POST-FASE-H
---

## POST-H-027-E — Upgrade/rollback dry-run

POST-H-027-E formaliza un dry-run local de upgrade/rollback sobre la infraestructura existente de backup/restore y upgrade check. El flujo recomendado es:

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core package build --kind all --version 0.1.0 --execute --json --write-report
python -m devpilot_core release artifact-manifest --version 0.1.0 --verify-checksums --json --write-report
python -m devpilot_core backup create --execute --json --write-report
python -m devpilot_core release upgrade-rollback-dry-run --from-version 0.1.0 --to-version 0.1.1 --json --write-report
python -m devpilot_core backup restore --backup-id <backup-id> --dry-run --json
```

El reporte `UpgradeRollbackDryRunReport` exige manifest/checksums en PASS, backup ZIP con SHA-256 consistente, restore policy segura, restore dry-run sin entradas fuera del workspace, plan de upgrade no mutante y acciones explícitas de rollback. El dry-run no ejecuta restore real ni upgrade real; un restore efectivo sigue requiriendo `--execute --confirm-restore`.

Esta versión es `implemented-initial`: suficiente para gate local de packaging, no suficiente para auto-update, migraciones automáticas, instalador empresarial, descargas remotas o recuperación ante desastre fuera del equipo local.


# DevPilot Local — Backup, restore y upgrade local

## Estado

`FUNC-SPRINT-83` implementa una primera versión `implemented-initial` de backup, restore y upgrade local. La capacidad es local-first, gobernada, auditable y conservadora: crea respaldo local solo con `--execute`, restaura en dry-run por defecto y no implementa auto-upgrade ni migraciones destructivas automáticas.

## Propósito

Proteger configuración y estado local de DevPilot antes de upgrades, pruebas de instalación o cambios de versión. El objetivo no es reemplazar un sistema de backup empresarial, sino entregar una línea base verificable para:

- respaldar `.devpilot/project.yaml`;
- respaldar MIASI registries;
- respaldar `providers.yaml.example` y `providers.yaml` con redacción de secretos cuando aplique;
- respaldar SQLite local de forma explícita;
- listar backups locales;
- planificar restore sin sobrescritura accidental;
- generar un plan de upgrade local.

## Alcance

Incluye:

- `backup create` en dry-run por defecto;
- `backup create --execute` para escribir ZIP y sidecar manifest en `.devpilot/backups`;
- `backup list` para consultar backups locales;
- `backup restore --dry-run` para simular restauración;
- `backup restore --execute --confirm-restore` para restauración explícita;
- `upgrade check` para planificar actualización sin mutar el workspace.

No incluye:

- cifrado de backup;
- backup remoto;
- auto-update;
- migraciones de esquema automáticas;
- firma de backups;
- sincronización cloud;
- restore silencioso.

## Comandos principales

```powershell
python -m devpilot_core backup create --dry-run --json
python -m devpilot_core backup create --execute --json --write-report
python -m devpilot_core backup list --json
python -m devpilot_core backup restore --backup-id <backup-id> --dry-run --json
python -m devpilot_core backup restore --backup-id <backup-id> --execute --confirm-restore --json
python -m devpilot_core upgrade check --json --write-report
```

## Artefactos generados

Cuando se ejecuta `backup create --execute`, DevPilot genera:

```text
.devpilot/backups/<backup-id>.zip
.devpilot/backups/<backup-id>.manifest.json
```

Cuando se usa `--write-report`, DevPilot genera reportes regenerables bajo:

```text
outputs/reports/backup_create.json
outputs/reports/backup_create.md
outputs/reports/backup_list.json
outputs/reports/backup_list.md
outputs/reports/backup_restore.json
outputs/reports/backup_restore.md
outputs/reports/upgrade_check.json
outputs/reports/upgrade_check.md
```

Los reportes en `outputs/` no deben versionarse como fuente; se regeneran en cada entorno.

## Funcionamiento técnico

`backup create` usa una lista controlada de rutas locales, no recorre todo el repo. El alcance se limita a estado operativo y configuración de `.devpilot`. Por defecto excluye `.git`, `.venv`, `node_modules`, `outputs`, `dist`, `__pycache__` y `.pytest_cache`.

`SecretGuard` se aplica a archivos textuales antes de empaquetar. Si detecta contenido con apariencia de secreto, guarda contenido redacted y registra finding `BACKUP_SECRET_REDACTED`. Esto evita filtrar tokens en backups compartibles, con la limitación de que un restore de un archivo redacted puede requerir reconfiguración manual.

`PathGuard` se usa para validar límites del workspace y operaciones de escritura. Restore inspecciona cada entrada del ZIP antes de planificar o ejecutar.

## Política de restore

Restore es dry-run por defecto. Un restore real requiere ambos flags:

```powershell
--execute --confirm-restore
```

Sin esa doble condición, DevPilot retorna BLOCK y no sobrescribe archivos. Esta decisión evita pérdida accidental de datos.

## Upgrade check

`upgrade check` no modifica archivos. Genera una secuencia operacional recomendada:

1. correr regresión;
2. validar contratos;
3. crear backup local;
4. generar paquete local;
5. verificar release;
6. revisar plan de instalación;
7. ensayar restore en dry-run.

## Criterios PASS

- `backup create --dry-run --json` retorna PASS sin escribir backup.
- `backup create --execute --json` crea ZIP y manifest local.
- `backup list --json` lista manifests locales.
- `backup restore --dry-run --json` no sobrescribe archivos.
- `backup restore --execute` bloquea si falta `--confirm-restore`.
- `upgrade check --json` genera plan local no mutante.
- Backup excluye `.git`, `.venv`, `node_modules`, `outputs`, `dist` y caches por defecto.
- SecretGuard redacted contenido sensible o lo reporta con warning.

## Criterios BLOCK

- Restore sobrescribe sin `--execute --confirm-restore`.
- Backup incluye `.venv` o `.git` por defecto.
- Backup incluye outputs/caches sin opción explícita futura.
- Backup guarda secretos sin redacción o advertencia.
- Upgrade check intenta modificar archivos.
- Cualquier ruta de restore escapa del workspace.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Pérdida de datos por restore accidental | Dry-run por defecto y confirmación explícita. |
| Exposición de secretos | SecretGuard y redacción por defecto. |
| Backup incompleto | Manifest auditable con lista de entradas. |
| Falsa sensación de backup industrial | Declarar `implemented-initial`; no hay cifrado ni backup remoto. |
| Upgrade incompatible | `upgrade check` planifica y exige backup previo. |

## Evolución pendiente

Para nivel industrial posterior se recomienda agregar:

- cifrado local opcional;
- firma/checksum del backup;
- restore selectivo por archivo;
- migraciones versionadas de SQLite;
- backup diff/incremental;
- verificación post-restore;
- integración con ReleaseAgent;
- política explícita para incluir o excluir secretos reales según entorno.
