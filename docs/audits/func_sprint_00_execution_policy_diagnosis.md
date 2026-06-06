---
title: "DevPilot Local — Diagnóstico de ExecutionPolicy en script de limpieza"
doc_id: "DEVPL-FUNC-00-EXECUTION-POLICY-DIAG"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-00"
updated: "2026-06-06"
approval: "approved_by_owner_direction"
---

# Diagnóstico de ExecutionPolicy en `func_sprint_00_cleanup.ps1`

## 1. Propósito

Este documento registra el diagnóstico del error observado al ejecutar:

```powershell
.\scriptsunc_sprint_00_cleanup.ps1
.\scriptsunc_sprint_00_cleanup.ps1 -Execute
```

## 2. Error observado

PowerShell bloquea la carga del archivo porque el script `.ps1` no está firmado digitalmente.

## 3. Causa

La causa no es un bug del script de limpieza. El bloqueo ocurre antes de que PowerShell ejecute cualquier instrucción interna del script. El entorno local aplica una ExecutionPolicy que no permite ejecutar scripts locales no firmados o marcados como provenientes de Internet.

## 4. Decisión técnica

Se mantiene el script PowerShell por utilidad en entornos Windows, pero se agrega una implementación Python equivalente:

```text
scripts/func_sprint_00_cleanup.py
```

La versión Python es la ruta recomendada para evitar fricción con ExecutionPolicy y mantener compatibilidad local-first.

## 5. Comandos recomendados

Dry-run:

```powershell
python scriptsunc_sprint_00_cleanup.py
```

Ejecución real:

```powershell
python scriptsunc_sprint_00_cleanup.py --execute
```

## 6. Opciones PowerShell si se decide usar `.ps1`

Después de revisar el contenido del script:

```powershell
Unblock-File .\scriptsunc_sprint_00_cleanup.ps1
.\scriptsunc_sprint_00_cleanup.ps1
```

O solo para la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scriptsunc_sprint_00_cleanup.ps1
```

## 7. Criterio de seguridad

No se recomienda cambiar la ExecutionPolicy global del equipo para ejecutar este helper. La ruta preferida es usar la alternativa Python.

## 8. Estado

```text
Diagnóstico: PASS
Script PowerShell: funcional pero bloqueado por política local del sistema
Alternativa Python: creada
Riesgo residual: bajo
```
