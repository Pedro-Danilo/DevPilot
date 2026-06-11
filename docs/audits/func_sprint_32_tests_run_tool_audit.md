---
title: "Auditoría FUNC-SPRINT-32 — tests.run como herramienta MIASI controlada"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-32-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-B-SEGURIDAD-OPERACIONAL"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-32 — tests.run como herramienta MIASI controlada

## 1. Propósito

Auditar la implementación inicial de `tests.run` como herramienta MIASI controlada, approval-gated y observable. Este sprint convierte la capa `SafeSubprocessRunner` del Sprint 31 en una capacidad operativa limitada para ejecutar perfiles pytest locales.

## 2. Estado

Estado: `implemented-initial`.

La implementación es funcional y verificable, pero no constituye CI/CD, sandbox completo ni ejecución arbitraria de comandos.

## 3. Funcionamiento técnico

La implementación agrega `src/devpilot_core/testing/` con:

- `TestProfile`;
- `TestProfileRegistry`;
- `TestsRunTool`.

El usuario selecciona un perfil fijo (`smoke`, `unit` o `all`). `TestsRunTool` evalúa primero `PolicyEngine` con `tool_id=tests.run`, `action=execute`, `subject=<profile>` y `approval_id`. Si la política bloquea, no hay subprocess. Si la política permite, ejecuta `python -m pytest` mediante `SafeSubprocessRunner`, sin `shell=True`, con cwd seguro, allowlist, timeout, captura de salida y redacción.

## 4. Integración con DevPilot

`tests.run` se integra con:

- `ApprovalService` y `ApprovalStore` para approval_id scoped;
- `ApprovalPolicyChecker` y `PolicyEngine` para autorización;
- `SafeSubprocessRunner` para ejecución controlada;
- `ReportEngine` para evidencia JSON/Markdown;
- `EventLogger` y `LocalStore` para eventos/persistencia;
- MIASI Tool Registry para pasar `tests.run` de `planned` a `implemented-initial`.

## 5. Comandos de uso

```powershell
$approval = python -m devpilot_core approval request `
  --tool tests.run `
  --action execute `
  --subject smoke `
  --reason "Run smoke tests" `
  --actor owner `
  --json | ConvertFrom-Json

$approvalId = $approval.data.approval.approval_id

python -m devpilot_core approval approve $approvalId `
  --actor owner `
  --reason "Approved local controlled tests" `
  --json

python -m devpilot_core tests profiles --json
python -m devpilot_core tests run --profile smoke --approval-id $approvalId --json --write-report
```

## 6. Criterios PASS

- `tests.run` aparece en MIASI como `implemented-initial`.
- Ejecuta solo perfiles allowlisted.
- No acepta comandos arbitrarios.
- No usa `shell=True`.
- Requiere approval si `PolicyEngine` lo exige.
- Captura exit code, stdout, stderr, timeout y redacciones.
- Genera reportes y eventos.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- Ejecutar sin approval válida cuando policy lo exige.
- Aceptar argumentos arbitrarios desde CLI.
- Saltarse `SafeSubprocessRunner`.
- Perder el exit code de pytest.
- Imprimir secretos crudos.
- Presentar esta versión como CI/CD o sandbox industrial completo.

## 8. Riesgos

- Ejecutar pytest puede ejecutar código local de pruebas; por eso el flujo está approval-gated.
- La allowlist no sustituye aislamiento de procesos ni sandbox completo.
- La versión no implementa rollback automático ni integración CI remota.
- La redacción de salida es conservadora y debe evolucionar con el hardening de Sprint 33.

## 9. Veredicto

`FUNC-SPRINT-32` queda apto para cierre si la suite completa pasa, MIASI valida y los artefactos de ingeniería quedan sincronizados.
