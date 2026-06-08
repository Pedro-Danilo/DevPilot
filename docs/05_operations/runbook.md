---
title: "Runbook — DevPilot Local"
doc_id: "DEVPL-OPS-002"
status: "approved"
version: "1.5.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-10"
updated: "2026-06-08"
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
