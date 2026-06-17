---
doc_id: DEVPL-AUDIT-FUNC-SPRINT-83
title: Auditoría FUNC-SPRINT-83 — Backup, restore y upgrade local
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-06-17
approval: approved_after_func_sprint_83_validation
sprint: FUNC-SPRINT-83
phase: FASE-G-PRODUCTIZACION-RELEASE
---

# Auditoría FUNC-SPRINT-83 — Backup, restore y upgrade local

## Estado

`FUNC-SPRINT-83` queda implementado como primera versión `implemented-initial`. No ejecuta upgrade automático y mantiene restore en dry-run por defecto.

## Propósito

Auditar la incorporación de capacidades locales de backup, restore y upgrade check para proteger el estado operativo antes de releases, instalación o actualización local.

## Alcance implementado

- Módulo `src/devpilot_core/release/backup.py`.
- Módulo `src/devpilot_core/release/upgrade.py`.
- CLI `backup create/list/restore`.
- CLI `upgrade check`.
- Documento operativo `docs/05_operations/backup_restore_upgrade.md`.
- Manifest `docs/functional_sprint_83_manifest.json`.
- Pruebas `tests/test_backup_upgrade.py`.
- Sincronización de README, runbook, backlog Fase G, changelog, release manifest y artifacts matrix.

## Funcionamiento

`backup create` genera plan dry-run por defecto y crea artefactos locales solo con `--execute`. `backup list` lee manifests locales sin extraer ZIPs. `backup restore` inspecciona el ZIP y bloquea sobrescrituras salvo ejecución explícita con confirmación. `upgrade check` produce un plan local sin mutar estado.

## Criterios PASS

- Backup dry-run no escribe archivos.
- Backup execute crea `.devpilot/backups/<id>.zip` y `.manifest.json`.
- Restore dry-run no sobrescribe.
- Restore execute requiere `--confirm-restore`.
- Upgrade check no muta estado.
- PathGuard impide rutas fuera del workspace.
- SecretGuard redacted contenido sensible textual.
- Tests focalizados PASS.

## Criterios BLOCK

- Restore sin confirmación que sobrescriba archivos.
- Backup por defecto de `.git`, `.venv`, `node_modules`, `outputs` o caches.
- Backup de secretos sin redacción/advertencia.
- Upgrade automático o remoto.
- Uso de red o APIs externas.

## Riesgos

- La redacción puede dejar un archivo restaurable pero no inmediatamente operativo si contenía secretos reales.
- SQLite se respalda como artefacto binario local; no hay migraciones de esquema automáticas en este sprint.
- No hay cifrado ni firma del backup en esta primera versión.

## Comandos de verificación

```powershell
python -m devpilot_core backup create --dry-run --json
python -m devpilot_core backup create --execute --json --write-report
python -m devpilot_core backup list --json
python -m devpilot_core backup restore --backup-id <backup-id> --dry-run --json
python -m devpilot_core upgrade check --json --write-report
python -m pytest tests\test_backup_upgrade.py tests\test_sprint_83_documentation.py -q
```

## Veredicto

PASS focalizado. La capacidad cumple el alcance de Fase G para backup/restore/upgrade local con controles conservadores. Debe evolucionar con cifrado, firma, restore selectivo y migraciones versionadas.
