---
title: "Runbook — DevPilot Local"
doc_id: "DEVPL-OPS-002"
status: "approved"
version: "1.8.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-21"
updated: "2026-06-10"
approval: "approved_by_owner"
source_baseline: "00_product approved + 01_requirements approved + 02_architecture approved + 03_security approved"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "SPRINT-PRECODE-05 quality operations baseline"
---

# Runbook — DevPilot Local

## 1. Propósito

Este runbook define cómo instalar, validar, operar, diagnosticar y recuperar **DevPilot Local** durante la fase pre-code y las primeras fases funcionales.

El runbook no reemplaza la arquitectura ni la estrategia de pruebas. Su función es permitir que el owner opere el proyecto de forma repetible, con comandos claros, criterios de recuperación y reglas de seguridad.

## 2. Entorno base

| Elemento | Valor esperado |
|---|---|
| Sistema operativo inicial | Windows |
| Ruta principal | `D:\Projects\DevPilot_Local` |
| Python | 3.12 recomendado |
| Entorno virtual | `.venv` |
| Instalación | editable local |
| Pruebas | `pytest` |
| Red externa | no requerida por defecto |
| API keys | no requeridas por defecto |

## 3. Instalación inicial

```powershell
cd D:\Projects\DevPilot_Local

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## 4. Validación mínima

```powershell
pytest -q
python -m devpilot_core --version
python -m devpilot_core readiness-check
python -m devpilot_core miasi-required
git status
```

Criterio PASS:

```text
pytest PASS
readiness-check ok=true
miasi-required true
git status limpio o cambios esperados
```

## 5. Aplicación segura de patches documentales

```powershell
cd D:\Projects\DevPilot_Local

Expand-Archive `
  -Path "$env:USERPROFILE\Downloads\patch_NAME.zip" `
  -DestinationPath "D:\Projects\DevPilot_Local" `
  -Force

pytest -q
python -m devpilot_core readiness-check
python -m devpilot_core miasi-required
git status
```

Regla:

```text
No hacer commit sin revisar git diff.
```

Comandos:

```powershell
git diff -- docs
git status
git add docs
git commit -m "docs: describe change"
```

## 6. Operación pre-code

| Acción | Comando actual o futuro |
|---|---|
| Verificar tests | `pytest -q` |
| Verificar readiness | `python -m devpilot_core readiness-check` |
| Verificar MIASI | `python -m devpilot_core miasi-required` |
| Revisar cambios | `git diff` |
| Confirmar estado | `git status` |
| Validar frontmatter | `python -m devpilot_core validate-frontmatter ... --strict` |
| Validar artefacto | `python -m devpilot_core validate-artifact ... --strict` |
| Ejecutar checklist pre-code | `python -m devpilot_core checklist-pre-code` |
| Generar reporte de frontmatter | `python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report` |
| Generar reporte de artefacto | `python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --strict --json --write-report` |
| Generar reporte de checklist | `python -m devpilot_core checklist-pre-code --json --write-report` |
| Consultar traza runtime | `Get-Content outputs\traces\events.jsonl -Tail 20` |
| Inicializar workspace en dry-run | `python -m devpilot_core workspace init --dry-run` |
| Inicializar workspace explícitamente | `python -m devpilot_core workspace init --execute` |
| Consultar workspace | `python -m devpilot_core workspace status --json` |
| Generar reporte de workspace | `python -m devpilot_core workspace status --json --write-report` |

## 6.1. Report Engine y contrato de evidencias

`FUNC-SPRINT-06` introduce `ReportEngine` como mecanismo central para escribir evidencia de gates en `outputs/reports`. El motor produce dos archivos por ejecución cuando el comando lo solicita o cuando el comando ya generaba evidencia por contrato:

```text
.json -> evidencia máquina-legible
.md   -> evidencia legible para revisión humana
```

Contrato mínimo de cada evidencia:

```text
report_id
command
status
ok
exit_code
message
generated_at
summary
findings
data
subject opcional
metadata opcional
```

Comandos operativos:

```powershell
# Readiness mantiene generación automática de evidencia por compatibilidad
python -m devpilot_core readiness-check --strict --json

# Los validadores pueden escribir evidencia explícita con --write-report
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --strict --json --write-report
python -m devpilot_core checklist-pre-code --json --write-report
```

Criterios PASS/BLOCK:

```text
PASS: el comando evaluado devuelve exit code 0 y los archivos JSON/Markdown quedan escritos bajo outputs/reports.
BLOCK/FAIL/ERROR: la evidencia se conserva igualmente con status, exit code y findings para auditoría.
```

Riesgos y límites de esta primera versión:

```text
- No firma criptográficamente reportes.
- No implementa retención ni rotación de reportes.
- El EventLog JSONL ya existe desde FUNC-SPRINT-07, pero todavía no hay correlación industrial completa entre reportes, eventos y persistencia SQLite.
- La redacción avanzada de secretos se moverá a SecretGuard/Policy Engine en sprints posteriores.
- Solo escribe dentro del project root para evitar salida accidental fuera del workspace.
```

Rol dentro de DevPilot:

```text
ReportEngine es la base para trazabilidad operativa, auditoría local, evidencia de gates, revisión humana y futura persistencia SQLite/EventLogger.
```

## 6.2. Event Log JSONL y observabilidad local

`FUNC-SPRINT-07` introduce `EventLogger` como mecanismo local append-only para registrar eventos de comandos, gates y errores en formato JSONL. El archivo runtime por defecto es:

```text
outputs/traces/events.jsonl
```

Propósito operativo:

```text
- saber qué comandos se ejecutaron;
- registrar inicio y cierre de comandos;
- registrar gates evaluados y findings relevantes;
- conservar una traza local mínima para auditoría;
- preparar la transición futura hacia EventStore/SQLite, AgentOps y observabilidad industrial.
```

Funcionamiento:

```text
command.started    se emite al entrar a main() después del parseo CLI.
gate.evaluated     se emite cuando un comando produce CommandResult de gate/validador.
command.completed  se emite al terminar el comando con exit code.
command.error      se emite ante DevPilotError o excepción defensiva de CLI.
```

Comandos de verificación:

```powershell
python -m devpilot_core --version
python -m devpilot_core standards status --json
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
Get-Content outputs\traces\events.jsonl -Tail 20
```

Criterios PASS:

```text
- outputs/traces/events.jsonl existe después de ejecutar cualquier comando vía CLI.
- Cada línea del archivo es JSON válido.
- Los comandos emiten command.started y command.completed.
- Los validadores/gates emiten gate.evaluated con status, exit_code, summary y findings.
- Los eventos no contienen secretos sintéticos conocidos sin redactar.
- EventLogger solo escribe dentro del project root.
```

Criterios BLOCK:

```text
- EventLogger permite escribir fuera del project root.
- Una línea JSONL queda corrupta o no parseable.
- Un comando deja de ejecutar por fallo del logger en condiciones normales.
- El logger persiste secretos sintéticos evidentes como sk-*, ghp_* o hf_* sin redacción.
- pytest falla.
```

Riesgos y límites de esta primera versión:

```text
- No hay rotación ni retención configurable de events.jsonl.
- No hay event_id correlacionado todavía con report_id de EvidenceReport.
- No hay persistencia SQLite ni consultas históricas.
- La redacción es básica y pattern-based; debe evolucionar con SecretGuard/Policy Engine.
- No hay exportación a OpenTelemetry ni backend centralizado.
```

Rol dentro de DevPilot:

```text
EventLogger es la base de observabilidad local para auditoría de comandos, trazabilidad de gates y futura operación AgentOps. Complementa ReportEngine: ReportEngine conserva evidencias por comando/gate; EventLogger conserva la línea temporal de ejecución.
```

## 7. Fallos comunes y recuperación

| Falla | Síntoma | Recuperación |
|---|---|---|
| `.venv` roto | imports fallan | recrear entorno virtual |
| paquete no instalado | `No module named devpilot_core` | `python -m pip install -e .[dev]` |
| tests fallan | `pytest` FAIL | revisar traceback, no commitear |
| readiness FAIL | falta artefacto | restaurar documento o actualizar gate |
| MIASI false | detección incorrecta | revisar docs/06_miasi y comando |
| patch mal aplicado | archivos duplicados | `git restore` o revert |
| ZIP dentro del repo | `git status` muestra `.zip` | borrar y actualizar `.gitignore` |
| egg-info rastreado | metadata generada | borrar y agregar a `.gitignore` |
| secretos detectados | token en archivo/log | revocar secreto, limpiar historia si aplica |


## 7.1. Limpieza de artefactos generados

Ruta recomendada, portable y sin depender de la política de ejecución de PowerShell:

```powershell
python scripts\func_sprint_00_cleanup.py
python scripts\func_sprint_00_cleanup.py --execute
```

Ruta PowerShell equivalente:

```powershell
.\scripts\func_sprint_00_cleanup.ps1
.\scripts\func_sprint_00_cleanup.ps1 -Execute
```

Si PowerShell muestra el error `cannot be loaded ... is not digitally signed`, el problema ocurre antes de que el script ejecute su lógica. No indica un bug en el script: indica que la política local de PowerShell no permite ejecutar ese `.ps1` sin firma o desbloqueo.

Opciones seguras de recuperación:

```powershell
# Opción recomendada: usar la versión Python
python scripts\func_sprint_00_cleanup.py
python scripts\func_sprint_00_cleanup.py --execute

# Opción alternativa: desbloquear solo este archivo después de revisarlo
Unblock-File .\scripts\func_sprint_00_cleanup.ps1
.\scripts\func_sprint_00_cleanup.ps1

# Opción temporal para la sesión actual, sin cambiar la política global
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\func_sprint_00_cleanup.ps1
```

No se recomienda cambiar la política global del equipo solo para ejecutar este helper.

## 8. Recuperación de entorno virtual

```powershell
deactivate
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest -q
```

## 9. Recuperación Git

### Descartar cambios no deseados

```powershell
git status
git restore path\to\file
```

### Revisar último commit

```powershell
git log --oneline -5
git show --stat HEAD
```

### Crear punto de seguridad

```powershell
git tag devpilot-precode-checkpoint-YYYYMMDD
```

## 10. Operación con workspaces futuros

Cuando existan workspaces, el flujo será:

```powershell
devpilot init-workspace D:\Projects\MyApp
devpilot workspace status
devpilot readiness-check --workspace D:\Projects\MyApp
devpilot security-check --workspace D:\Projects\MyApp
devpilot miasi-required --workspace D:\Projects\MyApp
```

Reglas:

```text
Cada workspace debe tener descriptor local.
Cada workspace debe declarar estándar aplicable.
Cada workspace debe separar source, docs, outputs y estado DevPilot.
```

## 11. Operación con agentes futuros

Los agentes no deben ejecutarse sin:

```text
Agent Card
Tool Card
Policy Card
Eval Card
Human Approval Card
Observability Card
```

Flujo esperado:

```text
1. Usuario solicita análisis o generación.
2. Agente produce propuesta en dry-run.
3. Policy Engine evalúa.
4. Human approval decide si aplica.
5. Tool ejecuta si está permitido.
6. Reporte, traza y evidencia quedan guardados.
```

## 12. Incidentes

### Incidente de seguridad

Ejemplos:

```text
secreto expuesto
archivo sobrescrito
patch aplicado incorrectamente
API externa usada sin consentimiento
traza con datos sensibles
```

Procedimiento:

```text
1. Detener ejecución.
2. No hacer commit.
3. Guardar evidencia mínima redactada.
4. Revocar secretos si aplica.
5. Restaurar desde Git o backup.
6. Documentar incidente.
7. Crear prueba de regresión si corresponde.
```

### Incidente operacional

Ejemplos:

```text
outputs corruptos
SQLite futura bloqueada
workspace inconsistente
CLI falla por rutas
```

Procedimiento:

```text
1. Revisar logs.
2. Reproducir con comando mínimo.
3. Ejecutar tests.
4. Restaurar desde Git o backup.
5. Registrar hallazgo.
```

## 13. Backup y restore

| Elemento | Backup |
|---|---|
| `docs/` | Git |
| `src/` | Git |
| `tests/` | Git |
| `outputs/` | selectivo, no todo |
| `.devpilot/` futuro | definir por workspace |
| SQLite futura | backup antes de migraciones |
| `.env` | no versionar; documentar `.env.example` |

## 14. Criterios operativos mínimos

| Criterio | Estado esperado |
|---|---|
| Tests pasan | obligatorio |
| Readiness pasa | obligatorio para pre-code |
| MIASI requerido detectado | obligatorio |
| Git limpio antes de finalizar sprint | obligatorio |
| No secretos en repo | obligatorio |
| Reportes reproducibles | obligatorio |
| Runbook actualizado | obligatorio |

## 15. Changelog

| Versión | Cambio |
|---|---|
| 0.1.0 | Borrador bootstrap inicial. |
| 0.5.0 | Runbook operativo completo para SPRINT-PRECODE-05. |


## Operación de FUNC-SPRINT-01 — CLI core

### Propósito operativo

FUNC-SPRINT-01 estabiliza la forma en que DevPilot comunica resultados desde la CLI. Antes de este sprint, `readiness-check` y `miasi-required` imprimían estructuras JSON específicas de cada comando. Después del sprint, ambos comandos siguen siendo compatibles, pero también pueden emitir un contrato normalizado con `--json`.

### Comandos

```powershell
python -m devpilot_core readiness-check
python -m devpilot_core readiness-check --json
python -m devpilot_core miasi-required
python -m devpilot_core miasi-required --json
python -m pytest -q
```

### Criterio PASS

- `pytest -q` pasa.
- `readiness-check` mantiene salida compatible.
- `readiness-check --json` produce JSON parseable con `command`, `ok`, `exit_code`, `message`, `data` y `findings`.
- `miasi-required --json` produce el mismo contrato normalizado.

### Criterio BLOCK

- No continuar si los comandos existentes dejan de funcionar.
- No continuar si `--json` genera salida no parseable.
- No continuar si se agregan dependencias externas innecesarias.


## FUNC-SPRINT-01 — Operación del CLI core

Propósito operativo: usar el contrato común de resultados para comandos actuales y futuros.

Comandos:

```powershell
python -m devpilot_core readiness-check --json
python -m devpilot_core miasi-required --json
```

Criterio PASS:

```text
Cada comando devuelve JSON parseable con command, ok, exit_code, message, data y findings.
```

Criterio BLOCK:

```text
Un comando nuevo no debe incorporarse si no puede expresarse mediante CommandResult o contrato compatible.
```

## FUNC-SPRINT-02 — Operación del validador de frontmatter

Propósito operativo: validar metadatos documentales mínimos antes de considerar un artefacto como candidato a gate MIPSoftware/MIASI.

Comandos:

```powershell
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict
```

Interpretación:

```text
exit_code 0: PASS.
exit_code 1: FAIL de validación documental.
exit_code 2: BLOCK reservado para bloqueos de política o seguridad.
exit_code 3: ERROR técnico o archivo inexistente.
```

Criterio PASS:

```text
El documento tiene bloque frontmatter, campos obligatorios, status permitido, version SemVer-like y updated en formato YYYY-MM-DD.
```

Criterio BLOCK:

```text
No avanzar a validadores de artefactos si el validador de frontmatter no puede detectar errores básicos de metadatos.
```

Riesgos:

```text
El parser implementado es YAML-like simple, no YAML completo. Si la documentación futura necesita YAML complejo, se deberá crear ADR para incorporar una dependencia controlada o extender el parser.
```


## FUNC-SPRINT-03 — Operación del validador de artefactos

### Propósito operativo

FUNC-SPRINT-03 agrega validación estructural de artefactos MIPSoftware/MIASI. A diferencia de `validate-frontmatter`, que revisa metadatos, `validate-artifact` valida que el documento tenga una estructura mínima esperada según su perfil: producto, requerimientos, arquitectura, seguridad, calidad, operación, ADR o MIASI.

### Comandos

```powershell
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md
python -m devpilot_core validate-artifact docs/06_miasi/agent_card.md --json
python -m devpilot_core validate-artifact docs/02_architecture/architecture_document.md --strict
```

### Interpretación

```text
PASS: el documento tiene frontmatter válido, H1 único y secciones mínimas del perfil.
FAIL: el documento no aprobado incumple estructura mínima.
BLOCK: un documento aprobado incumple estructura mínima y debe corregirse antes de continuar.
ERROR: archivo inexistente, ruta inválida o archivo no Markdown.
```

### Criterio PASS

```text
Los documentos principales de requerimientos y MIASI pasan validate-artifact.
pytest -q pasa.
Los comandos existentes readiness-check, miasi-required y validate-frontmatter siguen funcionando.
```

### Criterio BLOCK

```text
No avanzar a Standards Registry si un documento approved puede incumplir estructura mínima sin emitir BLOCK.
No avanzar si validate-artifact no usa CommandResult.
No avanzar si el validador requiere servicios externos o dependencias nuevas.
```

### Riesgos

```text
Los perfiles de FUNC-SPRINT-03 son determinísticos y mínimos. No reemplazan revisión humana ni plantillas completas. En FUNC-SPRINT-04 deberán integrarse con Standards Registry para que las reglas provengan progresivamente del estándar versionado.
```


## FUNC-SPRINT-04 — Operación del Standards Registry

### Propósito operativo

El comando `standards status` permite verificar que DevPilot encuentra localmente los estándares internos versionados:

- `docs/standards/mipsoftware`
- `docs/standards/miasi`

También reporta los artefactos obligatorios de proyecto y los perfiles de validación disponibles. Este comando es el primer paso para separar progresivamente las reglas documentales del código Python y acercarlas al estándar versionado.

### Comandos

```powershell
python -m devpilot_core standards status
python -m devpilot_core standards status --json
```

### Interpretación

- `exit_code 0`: MIPSoftware y MIASI fueron detectados y sus archivos mínimos existen.
- `exit_code 1`: faltan archivos obligatorios de estándar o artefactos de proyecto.
- `exit_code 2`: falta una carpeta crítica de estándar.
- `exit_code 3`: error técnico no controlado.

### Validación de pruebas

A partir de este sprint, `pytest -q` debe mostrar explícitamente el número de pruebas en PASS mediante el resumen:

```text
DEVPL TEST SUMMARY: N passed, 0 failed, 0 errors, 0 skipped
```

### Criterios PASS

- `python -m devpilot_core standards status --json` devuelve `ok=true`.
- Se detectan `mipsoftware` y `miasi`.
- Se listan artefactos obligatorios de proyecto.
- Se exponen perfiles de validación.
- `pytest -q` imprime número de pruebas en PASS.

### Criterios BLOCK

- Falta `docs/standards/mipsoftware`.
- Falta `docs/standards/miasi`.
- El comando rompe `readiness-check`, `validate-frontmatter` o `validate-artifact`.
- Se requiere red, API key o dependencia externa para validar estándares.

### Riesgos

- Las reglas de artefactos todavía están parcialmente codificadas en Python.
- El Standards Registry aún no carga reglas desde JSON/YAML externo.
- La sincronización completa entre estándares versionados y perfiles ejecutables queda para sprints posteriores.


## FUNC-SPRINT-05 — Operación de checklist pre-code y readiness estricto

### Propósito operativo

FUNC-SPRINT-05 convierte el checklist documental pre-code en un gate ejecutable y endurece `readiness-check` con modo `--strict`. El objetivo operativo es que DevPilot no dependa solo de una revisión humana previa, sino que pueda validar localmente existencia, frontmatter, estado aprobado, estructura mínima, activación MIASI, Standards Registry y consistencia del checklist.

### Comandos

```powershell
python -m devpilot_core checklist-pre-code
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict
python -m devpilot_core readiness-check --strict --json
python -m pytest -q
```

### Evidencia generada

`readiness-check --strict` genera evidencia local en:

```text
outputs/reports/readiness_check.json
outputs/reports/readiness_check.md
```

Estos archivos son evidencia runtime. Están ignorados por `.gitignore` y pueden regenerarse cuando sea necesario.

### Interpretación

- `exit_code 0`: gate PASS.
- `exit_code 1`: FAIL de validación no bloqueante por política de severidad.
- `exit_code 2`: BLOCK. Falta un artefacto obligatorio, un documento aprobado incumple estructura mínima, falta MIASI o el checklist no está en PASS.
- `exit_code 3`: ERROR técnico.

### Criterios PASS

- `checklist-pre-code --json` devuelve `ok=true`.
- Todas las filas obligatorias del checklist están en `PASS`.
- Todos los artefactos obligatorios referenciados por el checklist existen.
- Los artefactos Markdown obligatorios tienen frontmatter válido y `status: approved`.
- `readiness-check --strict --json` devuelve `ok=true`.
- `outputs/reports/readiness_check.json` y `.md` se generan correctamente.
- `pytest -q` pasa.

### Criterios BLOCK

- Falta `docs/checklists/checklist_pre_code.md`.
- Una fila obligatoria del checklist no está en `PASS`.
- Falta un artefacto obligatorio de producto, requerimientos, arquitectura, seguridad, calidad, operación o MIASI.
- Un artefacto obligatorio no tiene `status: approved`.
- El Standards Registry no detecta MIPSoftware o MIASI.
- Un documento aprobado incumple secciones mínimas de su perfil.

### Riesgos y límites actuales

- El parser de checklist está optimizado para las tablas Markdown actuales; no es un parser Markdown general.
- Los perfiles de artefactos siguen siendo determinísticos y mínimos; no reemplazan revisión humana experta.
- Los warnings de secciones recomendadas no bloquean todavía. Deben endurecerse progresivamente cuando las plantillas del estándar se vuelvan más contractuales.
- No hay llamadas externas, API keys, LLMs ni dependencias nuevas.


## FUNC-SPRINT-09 — Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos

### Propósito operativo

Este sprint agrega una capa local de seguridad ejecutable antes de habilitar agentes, Git avanzado, patches, refactors o APIs externas. La evaluación es determinística, offline y no ejecuta la acción simulada.

### Componentes

```text
.devpilot/policy.yaml                         -> política local mínima
src/devpilot_core/policy/decisions.py         -> PolicyDecision y PolicyEffect
src/devpilot_core/policy/path_guard.py        -> PathGuard
src/devpilot_core/policy/secrets.py           -> SecretGuard
src/devpilot_core/policy/cost_guard.py        -> CostGuard
src/devpilot_core/policy/engine.py            -> PolicyEngine
tests/test_policy_engine.py                   -> pruebas de seguridad
```

### Comandos

```powershell
python -m devpilot_core policy check read --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check delete --path docs/00_product/product_vision.md --json
python -m devpilot_core policy check read --path docs/file.md --text "api_key=sk-1234567890abcdef" --json --write-report
python -m devpilot_core policy check external-api --external-api --provider openai --estimated-cost-usd 0.01 --json
python -m pytest -q
```

### Interpretación

```text
PASS: solicitud simulada permitida por todos los guards.
FAIL: solicitud denegada por una política no bloqueante.
BLOCK: ruta insegura, acción peligrosa, secreto detectado o API externa sin presupuesto/política.
ERROR: error técnico inesperado.
```

### Criterios PASS

```text
Safe local read pasa.
Delete/overwrite/remove/rm se bloquean por defecto.
Rutas fuera del workspace se bloquean.
.env y .git se bloquean.
Secretos sintéticos se redactan y bloquean.
API externa sin presupuesto se bloquea.
Reportes y trazas no persisten secretos sintéticos.
pytest -q pasa.
```

### Criterios BLOCK

```text
Una acción destructiva se permite por defecto.
Un path traversal o ruta fuera del workspace pasa.
Un secreto aparece sin redacción en outputs/reports o outputs/traces.
Una API externa se permite sin CostGuard y sin presupuesto local.
El comando policy check no produce CommandResult normalizado.
```

### Riesgos y límites actuales

```text
SecretGuard es pattern-based, no un scanner industrial.
CostGuard no mide consumo real de proveedores.
PathGuard usa política estática inicial.
No existe todavía aprobación humana persistente.
No existe todavía Policy Matrix MIASI ejecutable completa.
```

### Evolución esperada

En sprints posteriores, esta capa debe integrarse con persistencia SQLite, Agent/Tool Registry, aprobación humana, ModelAdapter híbrido, Git read-only, patch review y CostGuard con histórico de consumo.


## FUNC-SPRINT-10 — Persistencia local SQLite y estado operativo

### Propósito operativo

Este sprint agrega estado operativo local mediante SQLite para conservar histórico de ejecuciones, gates, findings, eventos, aprobaciones y costos. La base vive en `.devpilot/devpilot.db`, es generada en runtime y no debe versionarse.

### Componentes

```text
src/devpilot_core/store/local_store.py   -> LocalStore, schema SQLite v0 y operaciones de persistencia
src/devpilot_core/store/__init__.py      -> API pública de persistencia
src/devpilot_core/cli.py                 -> comandos state/history e integración best-effort con gates
.devpilot/project.yaml                   -> declara paths.state
.gitignore                               -> excluye .devpilot/*.db y auxiliares SQLite
tests/test_local_store.py                -> pruebas de schema, historia, CLI y seguridad de ruta DB
```

### Comandos

```powershell
python -m devpilot_core state init --json
python -m devpilot_core state status --json
python -m devpilot_core state status --json --write-report
python -m devpilot_core history list --json --limit 10
python -m devpilot_core history list --json --limit 10 --write-report
python -m devpilot_core readiness-check --strict --json
python -m pytest -q
```

### Interpretación

```text
state init: crea o valida idempotentemente .devpilot/devpilot.db.
state status: muestra schema_version, tablas y conteos por tabla.
history list: lista runs recientes persistidos.
```

### Criterios PASS

```text
La base SQLite se crea bajo .devpilot/devpilot.db.
La migración se puede ejecutar varias veces sin borrar historial.
Existen tablas runs, findings, gates, events, approvals y cost_events.
Los gates/validadores principales persisten CommandResult de forma best-effort.
history list devuelve JSON parseable y runs recientes.
pytest -q pasa.
```

### Criterios BLOCK

```text
La DB intenta ubicarse fuera del workspace.
state init borra historial existente.
Una falla de persistencia rompe un gate documental previamente funcional.
Los outputs o la DB runtime quedan incluidos en el ZIP/repo versionado.
La migración crea un schema incompleto.
```

### Riesgos y límites actuales

```text
SQLite v0 no cifra datos.
No hay política de retención, vacuum, backup ni rotación.
No hay locking multi-proceso explícito más allá del mecanismo de SQLite.
La tabla approvals es estructural; todavía no existe flujo de aprobación humana persistente.
La tabla cost_events es estructural; todavía no mide consumo real de proveedores.
La integración con EventLogger JSONL aún no replica cada línea JSONL en SQLite automáticamente.
```

### Recuperación

Si la base se corrompe durante desarrollo, primero respaldar `.devpilot/devpilot.db`. Luego se puede regenerar una base limpia eliminando el archivo y ejecutando:

```powershell
python -m devpilot_core state init --json
```

No hacer esto en un entorno productivo sin una estrategia de backup/restore formal.

## FUNC-SPRINT-11 — MIASI ejecutable: Agent Registry, Tool Registry y Policy Matrix

### Propósito operativo

Este sprint convierte MIASI de baseline documental aprobada a contrato ejecutable validable. La validación sigue siendo local-first, determinística y no ejecuta agentes ni herramientas. Su función es impedir que DevPilot avance hacia runtime agentic sin registros, herramientas, políticas, evaluación, observabilidad y reglas de aprobación mínimas.

### Componentes

```text
.devpilot/miasi/agent_registry.json       -> contrato ejecutable de agentes permitidos
.devpilot/miasi/tool_registry.json        -> contrato ejecutable de herramientas permitidas
.devpilot/miasi/policy_matrix.json        -> matriz ejecutable de cobertura policy/gate/approval/observability
src/devpilot_core/miasi/registry.py       -> modelos, parser Markdown mínimo y MiasiRegistryValidator
src/devpilot_core/miasi/__init__.py       -> API pública MIASI ejecutable
src/devpilot_core/cli.py                  -> comandos miasi validate*
tests/test_miasi_registry.py              -> pruebas de registries, CLI, drift y casos BLOCK
```

### Comandos

```powershell
python -m devpilot_core miasi validate --json
python -m devpilot_core miasi validate --json --write-report
python -m devpilot_core miasi validate-registry --json
python -m devpilot_core miasi validate-tools --json
python -m devpilot_core miasi validate-policy-matrix --json
python -m pytest -q
```

### Interpretación

```text
miasi validate: valida agentes, herramientas, policy matrix, documentos MIASI y drift básico.
miasi validate-registry: valida solo Agent Registry ejecutable.
miasi validate-tools: valida solo Tool Registry ejecutable.
miasi validate-policy-matrix: valida dominios, gates, approvals y observabilidad de reglas.
```

### Criterios PASS

```text
Existen .devpilot/miasi/*.json.
El JSON es válido.
No hay IDs duplicados.
Los agentes referencian tools existentes.
Las tools referencian reglas de Policy Matrix existentes.
Los agentes A4+ requieren aprobación humana.
Los agentes MVP no superan A2.
Todas las entidades críticas tienen observabilidad.
La matriz cubre Docs, Filesystem, Git, Patch, Model, Agent, Secrets y Deployment.
pytest -q pasa.
```

### Criterios BLOCK

```text
Falta un registro ejecutable MIASI.
Un agente declara una herramienta inexistente.
Una herramienta o agente no tiene cobertura de policy.
Una regla de policy no tiene gate.
Una acción deny/block no es observable.
Un agente A4+ no requiere aprobación.
Un agente MVP supera A2.
Hay drift donde el documento aprobado declara una entidad ausente en el contrato ejecutable.
```

### Riesgos y límites actuales

```text
Primera versión ejecutable: valida declaraciones, no runtime.
No ejecuta agentes ni herramientas.
No implementa RBAC/IAM.
No persiste aprobaciones humanas reales.
No mide uso real de herramientas o modelos.
No reemplaza eval harness ni red teaming.
El parser Markdown es mínimo y soporta la forma de tablas usada por los documentos MIASI del repo.
```

### Recuperación

Si un registro se daña, restaurar desde control de versiones o desde el ZIP de sprint. Después validar:

```powershell
python -m devpilot_core miasi validate --json
python -m pytest -q
```

No habilitar un agente nuevo sin actualizar simultáneamente Agent Registry, Tool Registry, Policy Matrix, pruebas y documentación de auditoría.


## FUNC-SPRINT-12 — Agent Runtime mock/local para agentes documentales MVP

### Propósito operativo

Permitir la ejecución local y controlada de los primeros agentes documentales de DevPilot sin LLM externo, sin API keys y sin acciones destructivas. El runtime convierte los contratos MIASI ejecutables en agentes invocables, pero mantiene `dry-run` por defecto.

### Comandos

```powershell
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --json
python -m devpilot_core agent run documentation-audit --target docs/01_requirements --json --write-report
python -m devpilot_core agent run precode-documentation --idea "Agregar control documental" --dry-run --json
python -m devpilot_core agent run precode-documentation --idea "Agregar control documental" --dry-run --json --write-report
```

### Funcionamiento

`AgentRuntime` resuelve alias de CLI hacia IDs MIASI (`documentation-audit` → `precode.audit`, `precode-documentation` → `precode.documentation`), valida que el agente esté declarado, que sea MVP y que exista implementación local. Antes de cada operación tipo herramienta ejecuta `PolicyEngine`. Los resultados se devuelven como `CommandResult`, pueden escribirse como reporte JSON/Markdown y se registran en SQLite de forma best-effort.

### Criterios PASS

- `pytest -q` en PASS.
- `agent run documentation-audit` devuelve JSON parseable.
- `agent run precode-documentation --dry-run` no escribe archivos.
- Los tool calls incluyen evaluación de política.
- No se usan APIs externas ni llaves.

### Criterios BLOCK

- Agente no registrado o sin implementación local.
- Agente fuera de fase MVP en Sprint 12.
- Secreto sintético detectado en `--idea`.
- Ruta bloqueada por PathGuard.
- Intento de sobrescribir un draft existente.

### Riesgos y límites

Esta es una versión preliminar. Los agentes son rule-based, no usan LLM, no hacen planificación autónoma, no tienen memoria conversacional y no sustituyen revisión humana. La escritura bajo `outputs/drafts` solo debe usarse como borrador revisable y nunca como modificación automática de documentos aprobados.

## FUNC-SPRINT-13 — Evaluation Harness para validadores y agentes

### Propósito operativo

Ejecutar una evaluación offline, determinística y reproducible sobre validadores documentales y agentes documentales MVP. El objetivo es convertir la calidad esperada en casos verificables: documentos limpios deben pasar, documentos defectuosos deben fallar, y los agentes deben detectar brechas esperadas sin usar LLM externo ni servicios de red.

### Componentes

```text
evals/fixtures/documentation_eval_cases.json
src/devpilot_core/evals/models.py
src/devpilot_core/evals/runner.py
src/devpilot_core/evals/__init__.py
tests/test_eval_runner.py
```

### Comandos

```powershell
python -m devpilot_core eval run --json
python -m devpilot_core eval run --json --write-report
python -m devpilot_core eval run --case-id frontmatter-missing-doc-id --json
python -m pytest -q
```

### Funcionamiento

`EvalRunner` carga fixtures sintéticos desde `evals/fixtures/documentation_eval_cases.json`, materializa documentos temporales bajo `outputs/evals/workdir/`, ejecuta el componente indicado en cada caso y compara el resultado real contra la expectativa declarada. La suite inicial cubre:

- `validate-frontmatter`;
- `validate-artifact`;
- `DocumentationAuditAgent`;
- `PreCodeDocumentationAgent`.

El resultado se entrega como `CommandResult` y reporta métricas mínimas:

```text
cases_total
cases_passed
cases_failed
pass_rate
false_positives
false_negatives
missing_expected_findings
```

### Criterios PASS

```text
pytest -q pasa.
eval run --json devuelve ok=true.
pass_rate = 1.0 para la suite sintética vigente.
false_positives = 0.
false_negatives = 0.
missing_expected_findings = 0.
No se usan LLMs, APIs externas ni red.
Los archivos temporales se generan solo bajo outputs/evals/.
```

### Criterios BLOCK

```text
Un documento defectuoso pasa como limpio.
Un documento limpio falla sin razón esperada.
Un agente no detecta una brecha declarada en fixtures.
Una evaluación requiere API externa, secreto real o red.
El workdir intenta escribirse fuera del project root.
La salida JSON deja de ser parseable.
```

### Riesgos y límites actuales

Esta es una primera versión del Evaluation Harness. No mide todavía calidad semántica profunda, groundedness, utilidad de respuestas, cobertura probabilística, robustez ante prompts adversariales ni desempeño de modelos. Los fixtures son sintéticos y deben evolucionar hacia datasets versionados más amplios, golden outputs, red teaming y evaluación continua.

### Recuperación

Si la suite falla, revisar primero el caso reportado:

```powershell
python -m devpilot_core eval run --case-id <case-id> --json
```

Luego validar el componente individual afectado. Por ejemplo:

```powershell
python -m devpilot_core validate-frontmatter <archivo> --strict --json
python -m devpilot_core agent run documentation-audit --target <ruta> --json
```

No ajustar fixtures para ocultar una regresión. Si cambia el contrato esperado, documentar la razón en el manifiesto/auditoría del sprint correspondiente.


## FUNC-SPRINT-14 — Git read-only y repo inventory MVP+

### Propósito operativo

Obtener visibilidad local del estado Git y del inventario del repositorio sin modificar ramas, commits, staging area, archivos ni historial. Esta capacidad prepara los sprints de patch review, code review y agentes sobre repositorios.

### Componentes

```text
src/devpilot_core/repo/git_adapter.py
src/devpilot_core/repo/inventory.py
src/devpilot_core/repo/__init__.py
tests/test_repo_tools.py
```

### Comandos

```powershell
python -m devpilot_core git-status --json
python -m devpilot_core git-status --json --write-report
python -m devpilot_core repo-inventory --json
python -m devpilot_core repo-inventory --json --write-report
python -m pytest -q
```

### Funcionamiento

`GitAdapter` usa `subprocess.run` sin `shell=True` y con una allowlist cerrada de comandos read-only: `rev-parse`, `branch --show-current`, `status --short`, `diff --stat` y `diff --cached --stat`. Si el workspace no es un repo Git, devuelve un resultado controlado con warning, no una excepción no manejada.

`RepoInventory` recorre archivos bajo el workspace, excluye `.git`, `.venv`, caches y `outputs`, clasifica por categoría/riesgo y usa `SecretGuard` para detectar patrones sintéticos tipo secreto. Los contenidos crudos de archivos no se emiten en JSON ni Markdown.

### Criterios PASS

```text
pytest -q pasa.
git-status devuelve JSON parseable.
git-status no cambia git status antes/después.
repo-inventory devuelve JSON parseable.
repo-inventory detecta secretos sintéticos sin exponer valores.
--write-report escribe solo bajo outputs/reports.
No hay comandos Git destructivos.
```

### Criterios BLOCK

```text
Uso de git add/commit/checkout/reset/merge/rebase/tag/push.
Uso de shell=True o comandos Git no allowlisted.
Lectura fuera del workspace.
Secreto crudo filtrado en salida, reporte o traza.
Inventario que incluya outputs/caches como artefactos fuente.
```

### Riesgos y límites

Esta es una versión preliminar de análisis read-only. No sustituye SCA, SAST, secret scanning industrial, auditoría de licencias, análisis de submódulos, ramas remotas, LFS ni revisión semántica de código. Es una base segura para sprints posteriores.

### Recuperación

Si `git-status` falla, verificar primero que Git esté instalado y que el workspace esté inicializado como repositorio. Si `repo-inventory` reporta secretos sintéticos, revisar el archivo indicado y no copiar valores crudos al chat ni a documentación.


## FUNC-SPRINT-15 — Operación local de patch-review y code-review

### Propósito

Ejecutar una revisión local, determinística y no destructiva de patches y código fuente antes de cualquier flujo futuro de aplicación de cambios.

### Comandos

```powershell
python -m devpilot_core patch-review --patch-file safe.patch --json
python -m devpilot_core patch-review --patch-file safe.patch --json --write-report
python -m devpilot_core code-review --target src/devpilot_core/validators --json
python -m devpilot_core code-review --target src/devpilot_core/validators --json --write-report
```

### Funcionamiento operativo

`patch-review` lee un patch dentro del workspace o recibe texto inline, parsea cambios por archivo, evalúa rutas mediante `PolicyEngine`, bloquea patrones tipo secreto y reporta código riesgoso. No ejecuta `git apply`.

`code-review` revisa archivos de texto soportados dentro de un target, excluye `.git`, `.venv`, caches y `outputs`, detecta secretos sintéticos y patrones estáticos iniciales como `shell=True`, `os.system`, `eval`, `exec`, `pickle.loads` y errores de sintaxis Python.

### Criterios PASS

- El comando devuelve JSON válido.
- No hay modificación de archivos.
- No hay aplicación de patches.
- No hay secretos crudos en salida.
- Los reportes opcionales se escriben bajo `outputs/reports`.

### Criterios BLOCK

- Patch o target fuera del workspace.
- Ruta denegada (`.env`, `.git`, `.venv`).
- Secreto sintético detectado.
- Intento de ejecutar acciones destructivas o aplicar patch.

### Riesgos y recuperación

Esta versión es preliminar y puede generar falsos positivos en documentos que contienen ejemplos sintéticos de secretos. Si un review falla por secreto sintético, revisar el archivo indicado y confirmar si se trata de ejemplo, fixture o secreto real. No borrar ni aplicar patches automáticamente; el siguiente paso seguro es documentar el hallazgo y preparar una remediación revisada manualmente.


## FUNC-SPRINT-16 — Safe Refactor Planner

### Propósito

Operar el planificador de refactor seguro en modo `plan-only`, antes de cualquier modificación real de código.

### Funcionamiento

`refactor-plan` valida primero la ruta e intención mediante `PolicyEngine`, `PathGuard` y `SecretGuard`. Luego analiza archivos Python con AST, consulta `CodeReviewEngine` como precondición y genera un plan con candidatos, pasos, pruebas requeridas y rollback. No escribe código, no aplica patches y no ejecuta pruebas.

### Comandos

```powershell
python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared helpers" --json
python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared helpers" --json --write-report
```

### Interpretación

- `ok=true`: el plan se generó sin hallazgos bloqueantes.
- `plan_only=true`: no hay ejecución.
- `files_modified=0`: no se modificó el repo.
- `patch_generated=false`: no se generó patch aplicable.
- `approval_required_for_execution=true`: cualquier refactor futuro requiere revisión humana.

### Criterios PASS

```text
JSON parseable.
dry_run=true.
files_modified=0.
patch_generated=false.
plan con pruebas y rollback.
reportes opcionales bajo outputs/reports.
```

### Criterios BLOCK

```text
Ruta fuera del workspace.
Ruta bloqueada por PolicyEngine.
Secreto sintético en goal.
Target inexistente.
Error de sintaxis Python.
Intento de modificar archivos o aplicar patch.
```

### Riesgos

Versión inicial. No reemplaza refactorización asistida por IDE, análisis semántico, type checking, linters ni revisión humana. El siguiente nivel debe agregar sandbox, aplicación controlada, backup/rollback y aprobación persistente antes de modificar archivos.

## FUNC-SPRINT-17 — ModelAdapter híbrido, proveedores y CostGuard

### Propósito

Operar la primera capa ejecutable de `ModelAdapter` sin depender de API keys, red o costos externos. Esta versión permite validar el contrato multi-modelo de DevPilot antes de conectar proveedores reales.

### Funcionamiento

`model providers` carga metadata de `.devpilot/providers.yaml.example` o `.devpilot/providers.yaml` si existe localmente. El archivo versionado solo declara nombres de variables de entorno, nunca valores secretos. `model generate`, `model classify` y `model embed` enrutan por `ModelAdapterRouter`, aplican `SecretGuard` y `CostGuard`, y ejecutan únicamente `MockModelAdapter` en Sprint 17. Los proveedores locales/API quedan como rutas declaradas, pero no se contactan servidores ni APIs externas.

### Comandos

```powershell
python -m devpilot_core model providers --json
python -m devpilot_core model providers --json --write-report
python -m devpilot_core model generate --provider mock --prompt "Diseñar agente documental" --json
python -m devpilot_core model generate --provider mock --prompt "Diseñar agente documental" --json --write-report
python -m devpilot_core model classify --provider mock --text "bug detectado" --labels "bug,feature" --json
python -m devpilot_core model embed --provider mock --text "vector estable" --json
python -m devpilot_core model generate --provider openai --prompt "test" --json
```

### Interpretación

- `provider=mock`: ejecución determinística local sin costo.
- `external_api_used=false`: no hubo red ni API externa.
- `cost_estimate_usd=0.0`: ruta sin costo externo.
- `COSTGUARD_EXTERNAL_API_BLOCKED`: la ruta API externa fue bloqueada correctamente.
- `MODEL_LOCAL_PROVIDER_NOT_IMPLEMENTED`: proveedor local declarado, pero no ejecutado todavía.

### Criterios PASS

```text
JSON parseable.
MockModelAdapter genera, clasifica y embebe de forma determinística.
ProviderRegistry no contiene secretos crudos.
CostGuard bloquea APIs externas por defecto.
No hay llamadas de red.
No se requieren API keys.
Reportes opcionales bajo outputs/reports.
```

### Criterios BLOCK

```text
Proveedor no registrado.
Texto/prompt con secreto sintético.
API externa sin presupuesto/política explícita.
Intento de leer o persistir API key cruda.
Proveedor local/API ejecutado realmente en Sprint 17.
```

### Riesgos

Implementación preliminar. No mide tokens reales, latencia real, calidad semántica, costo facturado ni disponibilidad de proveedores. Ollama, LM Studio y APIs externas quedan como placeholders. Una integración real posterior deberá agregar clientes específicos, timeouts, retries, manejo de errores, evaluación de calidad, presupuesto persistente, SecretGuard sobre prompts y trazabilidad de costo por run.

## FUNC-SPRINT-18 — Preparación Desktop/Web sin UI completa

### Propósito

Preparar DevPilot Core para interfaces futuras mediante `ApplicationService` y DTOs serializables. Este sprint no implementa UI, no inicia servidor web, no abre ventana desktop y no agrega dependencias externas.

### Comandos operativos

```powershell
python -m devpilot_core app contract --json
python -m devpilot_core app contract --json --write-report
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --json
```

### Interpretación

`app contract` devuelve el contrato lógico que una futura interfaz desktop/web podrá consumir:

```text
capabilities
routes
dto_contracts
ui_implemented=false
desktop_ready_for_shell=true
web_ready_for_shell=true
```

### Criterios PASS

```text
ApplicationService responde.
ApplicationRequest y ApplicationResponse son JSON serializables.
Los validadores principales pueden ejecutarse desde CLI usando ApplicationService.
Los reportes opcionales se escriben bajo outputs/reports.
pytest -q pasa completo.
```

### Criterios BLOCK

```text
Agregar framework UI sin ADR.
Duplicar lógica de validadores en desktop/web.
Iniciar servidor o proceso externo en Sprint 18.
Transportar secretos en DTOs.
Romper CommandResult o los exit codes existentes.
```

### Riesgos

Primera versión. No hay API HTTP activa, IPC real, autenticación, sesiones, RBAC, CORS/CSRF, WebSocket, empaquetado desktop ni elección tecnológica definitiva.

---

## FUNC-SPRINT-19 — Cierre formal ciclo 00–18 y release técnico interno

### Propósito

Cerrar formalmente el ciclo `FUNC-SPRINT-00` a `FUNC-SPRINT-18` y dejar una baseline técnica interna `v0.1.0` verificable, limpia y auditable.

Este procedimiento no habilita nuevas capacidades destructivas. Solo verifica el core existente, los contratos documentales y los artefactos de release.

### Artefactos operativos

| Artefacto | Ruta | Uso |
|---|---|---|
| Reporte de cierre | `docs/audits/functional_cycle_00_18_closure_report.md` | Transferencia técnica del ciclo 00–18. |
| Release manifest | `docs/release/release_manifest_v0.1.0.json` | Fuentes, checksums, exclusiones y smoke commands. |
| Release notes | `docs/release/release_notes_v0.1.0.md` | Resumen funcional y límites del release. |
| Manifest Sprint 19 | `docs/functional_sprint_19_manifest.json` | Evidencia de sprint. |
| Script de verificación | `scripts/verify_release_v0_1_0.py` | Ejecuta smoke test local agrupado. |

### Pytest y regresión general

```powershell
cd D:\Projects\DevPilot_Local
$env:PYTHONPATH="src"
python -m pytest -q
```

Criterio PASS:

```text
DEVPL TEST SUMMARY: 129 passed, 0 failed, 0 errors, 0 skipped
```

El número puede aumentar en sprints posteriores, pero no debe disminuir sin justificación documentada.

### Smoke test manual del release interno

```powershell
cd D:\Projects\DevPilot_Local
$env:PYTHONPATH="src"

python -m devpilot_core --version
python -m devpilot_core workspace status --json
python -m devpilot_core standards status --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi validate --json
python -m devpilot_core eval run --json
python -m devpilot_core app contract --json
```

### Smoke test agrupado

```powershell
cd D:\Projects\DevPilot_Local
$env:PYTHONPATH="src"
python scripts/verify_release_v0_1_0.py --json
```

Criterio PASS:

```text
ok=true
commands_failed=0
```

### Empaquetado limpio

El ZIP limpio del release interno debe excluir:

```text
outputs/
.pytest_cache/
__pycache__/
.venv/
.git/
.devpilot/devpilot.db
build/
dist/
*.egg-info/
```

El ZIP final entregado por el entorno de implementación debe validarse con SHA256 externo.


### Ajuste de compatibilidad Sprint 20 sobre manifest de release v0.1.0

`tests/test_release_manifest.py` fue ajustado en `FUNC-SPRINT-20` porque `README.md`, `docs/05_operations/runbook.md` y los backlogs son artefactos vivos. El manifest `v0.1.0` conserva checksums históricos del release interno, pero la regresión no debe bloquear cambios documentales legítimos posteriores.

PASS: los artefactos inmutables del release siguen comparando SHA256 exacto. BLOCK: scripts, release notes, closure report o manifests de sprint cambian sin actualización justificada.

### Criterios PASS

- `pytest -q` pasa.
- Los comandos smoke devuelven exit code `0`.
- El manifest de release no lista `outputs/` ni `.devpilot/devpilot.db` como fuente.
- README y runbook declaran `FUNC-SPRINT-19` como último hito.
- No hay API keys, llamadas de red, dependencias nuevas ni acciones destructivas.

### Criterios BLOCK

- Falla `pytest -q`.
- El release incluye runtime outputs o DB local.
- Se documenta UI real, API externa real, patch apply o refactor execution como implementados.
- El script de verificación falla.
- El ZIP limpio contiene `.git`, `.venv`, `.pytest_cache`, `__pycache__` u `outputs/`.

### Riesgos

- `v0.1.0` no está firmado criptográficamente; los SHA256 son evidencia de integridad, no firma de supply chain.
- El release es interno; no sustituye un proceso futuro de release packaging industrial.
- La validación de manifest no sustituye auditoría semántica completa.



---

## FUNC-SPRINT-20 — Reconciliación documental post-18 y roadmap vivo

### Propósito

Operar la reconciliación documental creada por `FUNC-SPRINT-20`. Este procedimiento permite validar que README, runbook, roadmap, C4 y auditorías post-18 distinguen correctamente capacidades `implemented`, `implemented-initial`, `partial`, `planned`, `disabled` y `future`.

El sprint es documental-operativo. No agrega comandos del core, no modifica políticas runtime, no activa proveedores externos y no habilita UI, patch apply, refactor execution ni approval workflow.

### Artefactos operativos

| Artefacto | Ruta | Uso |
|---|---|---|
| Matriz de capacidades | `docs/audits/capability_status_matrix_after_sprint_18.md` | Consulta de estados implementado/parcial/planeado/futuro. |
| Reconciliación roadmap | `docs/audits/roadmap_reconciliation_after_sprint_18.md` | Mapeo de comandos históricos vs comandos reales. |
| C4 Context actualizado | `docs/02_architecture/c4_context.md` | Estado real de actores/sistemas externos. |
| C4 Container actualizado | `docs/02_architecture/c4_container.md` | Estado real de contenedores. |
| C4 Component nuevo | `docs/02_architecture/c4_component.md` | Componentes reales del core. |
| Manifest Sprint 20 | `docs/functional_sprint_20_manifest.json` | Evidencia de cierre del sprint. |

### Comandos agrupados por dominio vigente

```powershell
# Regresión general
$env:PYTHONPATH="src"
python -m pytest -q
python -m devpilot_core --version

# Workspace y estándares
python -m devpilot_core workspace status --json
python -m devpilot_core standards status --json

# Gates documentales
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/audits/capability_status_matrix_after_sprint_18.md --strict --json
python -m devpilot_core validate-artifact docs/audits/roadmap_reconciliation_after_sprint_18.md --strict --json
python -m devpilot_core validate-artifact docs/02_architecture/c4_component.md --strict --json

# MIASI, evaluación y contrato de interfaz futura
python -m devpilot_core miasi validate --json
python -m devpilot_core eval run --json
python -m devpilot_core app contract --json
```

### Mapeos de comandos históricos que no deben usarse como implementados

| Nombre histórico | Uso operativo real |
|---|---|
| `policy-check` | `python -m devpilot_core policy check ... --json` |
| `repo-scan` | `python -m devpilot_core repo-inventory --json` |
| `review-code --dry-run` | `python -m devpilot_core code-review --target <path> --json` |
| `refactor-plan --dry-run` | `python -m devpilot_core refactor-plan --target <path> --goal "..." --json` |
| `validate-schema` | Planned para Sprint 22; no usar aún. |
| `git-diff-report` | Planned; no usar como comando existente. |
| `approval request/list/approve` | Planned; no usar como workflow operativo. |
| `devpilot <comando>` | Packaging futuro; usar `python -m devpilot_core ...`. |

### Criterios PASS

- `pytest -q` pasa.
- `validate-artifact docs/02_architecture/c4_component.md --json` pasa.
- README declara `FUNC-SPRINT-20` como último hito y `FUNC-SPRINT-21` como siguiente.
- Roadmap queda marcado como histórico + reconciliado.
- C4 Context/Container/Component distinguen `implemented`, `partial`, `planned`, `disabled` y `future`.
- No se documentan UI, API externa real, patch apply, refactor execution, approval workflow, MCP, RAG ni multiagente como implementados.

### Criterios BLOCK

- Una tabla operativa presenta `validate-schema`, `git-diff-report`, `approval request/list/approve`, UI real o API externa real como disponible.
- C4 omite estados para nodos aspiracionales.
- README o runbook conserva `FUNC-SPRINT-19` como último hito después de cerrar Sprint 20.
- Fallan las pruebas `tests/test_sprint_20_documentation_reconciliation.py`.

### Riesgos

- La reconciliación es manual y puede sufrir drift si sprints posteriores no actualizan estos documentos.
- No reemplaza un futuro Command Catalog ni Schema Engine.
- No valida semánticamente todos los documentos; solo reduce contradicciones operativas críticas.

### Evolución posterior

Próximo sprint operativo: FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot.

`FUNC-SPRINT-21` debe iniciar Schema Registry para que los contratos de `CommandResult`, `Finding`, reportes, DTOs y rutas internas empiecen a tener schemas versionados. Este sprint prepara el terreno, pero no implementa esos schemas.

## FUNC-SPRINT-21 — Schema Registry y catálogo de contratos DevPilot

### Propósito operativo

Operar el Schema Registry inicial creado en `FUNC-SPRINT-21`. Este procedimiento lista contratos JSON versionados de DevPilot y verifica la integridad del catálogo local.

La capacidad es `implemented-initial`: registra y lista schemas, pero no valida todavía instancias JSON. `FUNC-SPRINT-22` debe implementar `schema validate`.

### Artefactos involucrados

| Artefacto | Rol operativo |
|---|---|
| `src/devpilot_core/schemas/models.py` | Define `SchemaSpec` y `SchemaRegistrySummary`. |
| `src/devpilot_core/schemas/registry.py` | Carga el catálogo, detecta duplicados, archivos faltantes y metadata obligatoria vacía. |
| `docs/schemas/schema_catalog.json` | Fuente de verdad del catálogo de schemas registrados. |
| `docs/schemas/*.schema.json` | Schemas preliminares de contratos internos. |
| `docs/audits/func_sprint_21_schema_registry_audit.md` | Auditoría técnica del sprint. |
| `docs/functional_sprint_21_manifest.json` | Manifest del sprint. |
| `tests/test_schema_registry.py` | Pruebas de catálogo, CLI y reportes. |

### Comandos de uso

Listar schemas:

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core schema list --json
```

Listar schemas y generar reporte:

```powershell
python -m devpilot_core schema list --json --write-report
```

Ejecutar pruebas específicas:

```powershell
python -m pytest tests/test_schema_registry.py -q
```

Ejecutar regresión completa:

```powershell
python -m pytest -q
```

### Criterios PASS

- `schema list` devuelve `CommandResult` JSON parseable.
- `summary.schemas_total` coincide con el catálogo.
- `summary.schemas_existing` coincide con los archivos reales.
- `duplicate_schema_ids` está vacío.
- `missing_schema_paths` está vacío.
- `--write-report` genera `outputs/reports/schema_list.json` y `outputs/reports/schema_list.md`.
- No se requiere red, API key ni dependencia externa.

### Criterios BLOCK

- Un schema listado no existe.
- Hay `schema_id` duplicados.
- Falta `version` o `description` en una entrada.
- El comando emite JSON inválido.
- Se usa el registry como si fuera validador de instancias.

### Riesgos y evolución posterior

El principal riesgo es confundir catálogo con validación. `FUNC-SPRINT-21` no valida datos reales contra schemas; solo registra contratos y verifica integridad del catálogo.

Para alcanzar nivel industrial, los próximos pasos son:

- `FUNC-SPRINT-22`: implementar `SchemaValidator` e instancia `schema validate`.
- `FUNC-SPRINT-23`: extender schemas a MIASI, workspace, providers y manifests.
- `FUNC-SPRINT-24`: conectar schemas con `ValidationGateway`.

### Fallos comunes

| Síntoma | Causa probable | Acción |
|---|---|---|
| `SCHEMA_CATALOG_MISSING` | Falta `docs/schemas/schema_catalog.json`. | Restaurar catálogo desde repo vigente. |
| `SCHEMA_REGISTRY_DUPLICATE_ID` | Dos entradas comparten `schema_id`. | Corregir ID en catálogo. |
| `SCHEMA_REGISTRY_MISSING_FILE` | El catálogo apunta a archivo inexistente. | Crear schema o corregir ruta. |
| `schema list` no existe | Entorno no actualizado a Sprint 21. | Reinstalar editable y revisar `PYTHONPATH`. |

Próximo sprint operativo: `FUNC-SPRINT-22 — Schema Validator y schemas de contratos transversales`.

