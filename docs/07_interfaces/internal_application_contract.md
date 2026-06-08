---
title: "Contrato interno de Application Services para Desktop/Web"
doc_id: "DEVPL-INTERFACES-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-18"
updated: "2026-06-08"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---
# Contrato interno de Application Services para Desktop/Web

## 1. Propósito

Este artefacto define el contrato interno que permitirá que el CLI, una futura aplicación de escritorio y una futura interfaz web consuman el mismo **DevPilot Core** sin duplicar reglas de negocio, validadores, gates, políticas ni trazabilidad.

`FUNC-SPRINT-18` no implementa una UI completa, no inicia un servidor web, no abre una ventana de escritorio y no agrega dependencias externas. Su alcance es preparar una frontera de servicios testeable y serializable.

## 2. Contexto técnico

DevPilot nació como CLI local-first para madurar primero el core, las políticas, los validadores, los reportes, la observabilidad y los agentes. La evolución a desktop/web debe respetar esa decisión: las interfaces visuales deben ser shells sobre servicios de aplicación, no implementaciones paralelas.

La decisión es compatible con una futura arquitectura tipo:

```text
CLI / Desktop Shell / Web Shell
          ↓
ApplicationService + DTOs
          ↓
DevPilot Core: validators, policies, reports, traces, state, MIASI, agents
```

## 3. Componentes implementados

```text
src/devpilot_core/application/dtos.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
```

## 4. DTOs serializables

### ApplicationRequest

Representa una solicitud futura desde CLI, desktop o web.

Campos principales:

```text
operation
payload
client
dry_run
```

Criterios PASS:

```text
JSON serializable.
No contiene secretos reales.
No contiene estado de transporte.
Mantiene dry_run=true por defecto.
```

Criterios BLOCK:

```text
Transportar API keys o secretos crudos.
Acoplarse a HTTP, Tauri, Electron o cualquier framework concreto.
Permitir ejecución con side effects por defecto.
```

### ApplicationResponse

Envuelve `CommandResult` en un contrato consumible por interfaces.

Campos principales:

```text
contract
schema_version
operation
ok
exit_code
message
data
findings
generated_at
```

Criterios PASS:

```text
Conserva exit_code y findings.
Es JSON serializable.
No reemplaza CommandResult.
No emite contenidos secretos crudos.
```

Criterios BLOCK:

```text
Perder severidad de findings.
Cambiar la semántica de exit codes.
Ocultar bloqueos de PolicyEngine, SecretGuard o CostGuard.
```

### ServiceCapability

Describe una operación consumible por UI futura.

Incluye:

```text
operation
description
side_effect
dry_run_default
command_equivalent
output_contract
```

### InterfaceRouteContract

Define rutas lógicas, no rutas HTTP activas.

Ejemplo:

```text
POST /application/validators/frontmatter -> validators.validate_frontmatter
```

## 5. ApplicationService

`ApplicationService` expone una fachada para validadores y contratos internos.

Operaciones iniciales:

```text
validate_frontmatter(path, strict=False)
validate_artifact(path, strict=False)
checklist_pre_code(strict=True)
readiness(strict=False)
standards_status()
application_contract()
as_application_response(result, operation=None)
```

## 6. Integración con CLI

A partir de `FUNC-SPRINT-18`, los comandos principales de validación documental pasan por `ApplicationService`:

```text
validate-frontmatter
validate-artifact
checklist-pre-code
readiness-check
standards status
```

El nuevo comando de inspección de contrato es:

```powershell
python -m devpilot_core app contract --json
python -m devpilot_core app contract --json --write-report
```

## 7. Relación con Desktop/Web futuro

Este sprint prepara el core para posibles shells futuros:

```text
Desktop Shell: Tauri/Electron/otra tecnología -> llama ApplicationService o un backend local controlado.
Web Shell: FastAPI/otro backend local -> expone rutas sobre ApplicationService.
```

No se decide todavía una tecnología definitiva de UI. Esa decisión requerirá ADR cuando se elija stack, permisos, packaging, IPC/HTTP, distribución y seguridad de la interfaz.

## 8. Criterios PASS

```text
ApplicationService existe.
DTOs son serializables.
CLI usa ApplicationService para validadores principales.
app contract devuelve JSON parseable.
No hay UI implementada todavía.
No hay servidor ni proceso externo.
No hay dependencias nuevas.
pytest -q pasa completo.
README y runbook quedan sincronizados.
```

## 9. Criterios BLOCK

```text
Agregar framework UI sin ADR.
Duplicar lógica de validadores en una capa visual.
Agregar FastAPI/Tauri/Electron como dependencia en Sprint 18.
Habilitar APIs externas o costos.
Guardar secretos o credenciales en DTOs.
Cambiar el contrato CommandResult sin migración.
```

## 10. Riesgos y evolución

Esta es una primera versión de frontera de aplicación. Todavía no cubre autenticación local, sesiones, autorización por rol, streaming de eventos, WebSocket, IPC real, empaquetado desktop, servidor local, CSRF/CORS, control de procesos, versionado de API ni compatibilidad hacia atrás formal.

Evolución recomendada:

```text
FUNC-SPRINT-19+: evaluar stack desktop/web y abrir ADR.
Agregar capa API local solo cuando los contratos estén estables.
Agregar tests de compatibilidad de contratos.
Agregar schemas JSON versionados.
Agregar simulador de cliente desktop/web antes de implementar UI real.
```
