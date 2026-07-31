---
doc_id: "DEVPL-POST-H-EVAL-002-E2E-PILOT-UI-FIRST-RUNBOOK"
title: "POST-H-EVAL-002 — Runbook altamente detallado del piloto real end-to-end UI-first"
status: "approved"
version: "1.7.0"
owner: "Ordóñez"
updated: "2026-07-30"
approval: "approved_by_owner"
phase: "POST-H-EVAL-002"
roadmap_path: "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md"
planning_backlogs_total: 3
implementation_status: "active/02-a-authorized-after-01-d-closure"
source_repo: "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
baseline_repo: "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
baseline_test_evidence: "1919 passed, 0 failed, 0 errors, 0 skipped"
recommended_repo_path: "docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md"
local_first: true
ui_first: true
dry_run_default: true
network_runtime_allowed: false
external_apis_allowed: false
remote_execution_enabled: false
connector_write_enabled: false
plugin_execution_enabled: false
production_multiuser_enabled: false
---

# POST-H-EVAL-002 — Runbook altamente detallado del piloto real end-to-end UI-first

## 0. Decisión ejecutiva

Es **necesario y conveniente** elevar el procedimiento del piloto a un documento Markdown formal, versionado, revisable y gobernado.

El piloto no será una demostración informal. Será el principal mecanismo para determinar si DevPilot funciona como producto integrado y no solamente como una colección de capacidades que pasan pruebas aisladas. Para que sus conclusiones sean reproducibles, el procedimiento debe fijar antes de comenzar:

- baseline exacto;
- reglas de instalación;
- topología de carpetas;
- alcance del proyecto piloto;
- superficie principal de operación;
- bridges CLI permitidos;
- criterios PASS/BLOCK;
- evidencias obligatorias;
- métricas;
- reglas de pausa y reanudación;
- clasificación de hallazgos;
- protocolo para correcciones críticas;
- procedimiento de release candidate;
- método para derivar el diagnóstico industrial y el nuevo roadmap.

Sin este runbook, dos ejecuciones del mismo piloto podrían usar pasos, comandos y criterios diferentes, haciendo imposible comparar resultados o separar defectos de producto de errores del operador.

## 0.1. Estado documental

Este runbook queda `approved` y autorizado como procedimiento operativo de `POST-H-EVAL-002`.

El baseline operativo del piloto es:

- `repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip`.

Trazabilidad de origen:

- baseline operativo sincronizado inmediatamente anterior: `repo_DevPilot_Local_317_POST_H_EVAL_002_BASELINE_READY.zip`;
- baseline de activación: `repo_DevPilot_Local_316_POST_H_EVAL_002_ACTIVATION.zip`;
- SHA-256 del baseline de activación: `c60c3a69d2ead35ca4e66f10ad15a0ed64b4db913b6cb4978ab6e587c824b305`;
- commit de activación registrado: `6092e83`;
- log de regresión de activación: `Log_consola_validacion_general_no-regresion_POST-H-EVAL-002_activate.txt`;
- SHA-256 del log: `9c379fdd0e6fd26bb781607404e2ab18263c76e4624ded40c6c57632b4fc0ae9`;
- resultado de activación: `1918 passed, 0 failed, 0 errors, 0 skipped`;
- contrato focal de activación: `40 passed, 0 failed, 0 errors, 0 skipped`.

Evidencia autoritativa y procedencia por capas:

- baseline ejecutable congelado: `repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip`;
- SHA-256 de la copia exacta R1: `bf5c10df92a104a9c212c19db28d518eff0d5e5a671b4b35ec71bfd79c7df308`;
- commit de empaquetado documental R1: `2c5f209`;
- ancla funcional validada: `0c7741f`;
- log exacto de esta entrega: `Log_consola_validacion_POST-H-EVAL-002_synchronize_operational_baseline_318.txt`;
- SHA-256 del log exacto: `42afee0bac6eaf7bfe816e3caa02bbf22a1e820f061ac049df94a0298f429bbc`;
- regresión completa: `1919 passed, 0 failed, 0 errors, 0 skipped`;
- contrato focal: `41 passed, 0 failed, 0 errors, 0 skipped`;
- repo de gobernanza posterior a 01-B: `repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip`.

`0c7741f` identifica la superficie ejecutable probada. `2c5f209` identifica el commit documental R1 desde el cual se generó el ZIP exacto congelado. El charter y `evidence_manifest.json` deben registrar ambas capas. Las correcciones exclusivamente documentales y de metadata de gobernanza no requieren repetir `pytest -q`; bastan pruebas focales, Documentation Governance, TCR, Evidence Freshness, búsqueda anti-drift y RAG grounded.

El repo histórico `repo_DevPilot_Local_315_POST_H_034-CLOSURE.zip` permanece únicamente como fuente de cierre de POST-H-034; no debe utilizarse para ejecutar el piloto porque no contiene la activación canónica de `POST-H-EVAL-002`.

Ruta canónica dentro del repo:

```text
DevPilot_Local/docs/05_operations/
  DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md
```

El runbook, roadmap y tres backlogs están registrados en Documentation Source Registry, TCR v1/v2 e índice RAG. `POST-H-EVAL-002-01-C` está cerrado `PASS-WITH-GAPS`; `repo_DevPilot_Local_322_POST_H_EVAL_002_01_D_ACCEPTANCE_READY.zip` prepara 01-D corrigiendo dispatch de rutas y timeout browser. La ejecución formal de rutas críticas, estados negativos, screenshots y bridges sigue pendiente y pertenece exclusivamente a 01-D.

---

## Parte I — Propósito, alcance y modelo de evaluación

## 1. Objetivo del piloto

Poner a prueba DevPilot mediante un proyecto de software real y acotado, recorriendo de extremo a extremo:

```text
instalación del baseline
→ arranque de API y Web UI
→ onboarding del proyecto
→ planificación
→ requisitos
→ arquitectura
→ seguridad
→ preparación pre-code
→ implementación asistida
→ revisión de código y patches
→ pruebas
→ trazabilidad
→ documentación
→ observabilidad
→ release candidate
→ reinstalación limpia
→ evaluación industrial
```

El propósito no es demostrar que todos los comandos existen. El propósito es verificar que las capacidades colaboran de forma coherente y que un operador puede completar el SDLC con trazabilidad, seguridad y una experiencia razonable.

## 2. Preguntas que debe responder el piloto

Al finalizar, la evidencia debe permitir responder sin especulación:

1. ¿Puede instalarse DevPilot desde un baseline limpio siguiendo documentación vigente?
2. ¿La API y la Web UI arrancan de forma reproducible en Windows?
3. ¿La UI permite comprender el estado del sistema sin depender de conocimientos internos?
4. ¿Un proyecto nuevo puede incorporarse sin editar manualmente metadata interna de DevPilot?
5. ¿Los artefactos pre-code se generan, validan y visualizan de forma coherente?
6. ¿Los agentes producen recomendaciones trazables y acotadas?
7. ¿Los resultados muestran fuentes, findings, reportes y traces suficientes?
8. ¿Las acciones sensibles permanecen bloqueadas o approval-gated?
9. ¿Test Impact, TCR y quality gates recomiendan y verifican lo correcto?
10. ¿La UI refleja fielmente el estado producido por CLI y ApplicationService?
11. ¿Existen operaciones importantes que solamente pueden realizarse por CLI?
12. ¿Los estados loading, empty, ERROR, BLOCK, 401, 403 y API-down son comprensibles?
13. ¿Puede obtenerse un release candidate reproducible del proyecto piloto?
14. ¿El proyecto puede reinstalarse en otra ruta y volver a operarse desde la UI?
15. ¿Qué gaps deben convertirse en el siguiente roadmap de DevPilot?

## 3. Alcance funcional del piloto

Proyecto recomendado:

```text
PILOT-E2E-001 — Sistema local de ventas e inventario
para microemprendimientos
```

Capacidades mínimas del proyecto piloto:

- catálogo de productos;
- categorías;
- existencias actuales;
- movimientos de entrada y salida;
- registro de ventas;
- detalle de venta;
- alerta de stock mínimo;
- reporte básico de ventas e inventario;
- persistencia SQLite;
- backend Python/FastAPI;
- frontend React o TypeScript;
- pruebas unitarias;
- pruebas de integración;
- documentación de instalación y uso;
- empaquetado local reproducible.

## 3.1. Fuera de alcance

No se incluirá en el primer piloto:

- pagos reales;
- integración bancaria;
- facturación electrónica;
- datos personales sensibles;
- nube;
- despliegue público;
- APIs externas obligatorias;
- SaaS;
- multi-tenancy;
- enterprise IAM;
- OIDC/SSO;
- connector write;
- plugin execution;
- remote execution;
- loops autónomos sin límite;
- cambios a los no-go gates vigentes.

Cualquier necesidad de estas capacidades se registra como `future-capability-gap`; no se habilita durante el piloto.

## 4. Hipótesis de producto que se evaluarán

### H1 — Instalación reproducible

Un operador técnico puede instalar el baseline limpio y llegar a una UI funcional siguiendo únicamente documentación versionada.

### H2 — Web-first operacional

La Web UI es suficiente como consola principal para observar estado, reportes, trazas, aprobaciones y configuración local, aunque ciertas operaciones de creación o ejecución sigan requiriendo CLI o IDE.

### H3 — Gobernanza integrada

Las recomendaciones, patches, pruebas, reportes y release candidate mantienen una línea trazable entre requerimiento, cambio, evidencia y decisión.

### H4 — Seguridad preservada

El piloto no habilita capacidades sensibles ni permite que una acción crítica se ejecute sin gate, dry-run o aprobación.

### H5 — Release local verificable

El proyecto piloto puede producir un RC local, instalarse en una ruta limpia y volver a funcionar desde la UI.

## 5. Principio UI-first aplicado correctamente

UI-first **no significa** afirmar que la UI actual implementa todos los flujos del SDLC.

El baseline registra cinco rutas UI críticas:

```text
ui.dashboard   → /
ui.reports     → /reports
ui.traces      → /traces
ui.approvals   → /approvals
ui.settings    → /settings
```

El Operator Dashboard está embebido en `ui.dashboard`.

La UI actual funciona principalmente como:

- consola de estado;
- visor de reportes;
- visor de trazas;
- centro de aprobaciones locales;
- lanzador de acciones allowlisted en dry-run;
- visor de settings y security posture;
- superficie de operador para PASS/WARN/BLOCK/ERROR/PENDING.

No existe todavía una UI completa para:

- redactar requisitos;
- editar arquitectura;
- modificar threat models;
- administrar todos los workspaces;
- ejecutar toda la taxonomía de pruebas;
- generar y aplicar patches completos;
- operar el ciclo de release completo.

Por ello, el piloto usa esta regla:

```text
UI para observar, decidir y aprobar siempre que exista superficie.
IDE/archivos versionados para autoría de ingeniería.
CLI únicamente como bridge para capacidades todavía no expuestas en UI.
```

Todo bridge CLI debe quedar registrado como evidencia de UX y candidato de evolución.

---

## Parte II — Gobernanza del piloto

## 6. Identificadores obligatorios

Usar los siguientes identificadores salvo decisión explícita distinta:

```text
Hito de evaluación:    POST-H-EVAL-002
Piloto:                PILOT-E2E-001
Proyecto:              inventory-sales-local
Workspace ID:          pilot-inventory-sales-local
Baseline de plataforma: repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip
```

## 7. Roles

Una persona puede desempeñar varios roles, pero cada decisión debe identificar el rol ejercido.

| Rol | Responsabilidad |
|---|---|
| Product Owner | Define alcance y acepta historias. |
| Pilot Operator | Ejecuta el runbook y registra evidencia. |
| DevPilot Maintainer | Diagnostica defectos de plataforma. |
| Application Engineer | Implementa el proyecto piloto. |
| Security Reviewer | Revisa riesgos, approvals y no-go gates. |
| QA/Evidence Reviewer | Verifica pruebas, trazas y manifest de evidencia. |
| Release Reviewer | Autoriza o bloquea el RC local. |

## 8. Regla de separación de repositorios

No desarrollar la aplicación piloto dentro del repo de DevPilot.

Topología recomendada:

```text
D:\Projects\DevPilot_E2E_Evaluation\
├── baselines\
│   ├── repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip
│   └── checksums\
├── platform\
│   └── DevPilot_Local_318_EVAL\
├── workspaces\
│   └── inventory-sales-local\
├── evidence\
│   └── PILOT-E2E-001\
├── clean_install_validation\
└── backups\
```

Separación lógica:

```text
platform/      código y runtime de DevPilot
workspaces/    código del proyecto piloto
evidence/      evidencia de la evaluación
outputs/       evidencia runtime generada por DevPilot
backups/       puntos de restauración explícitos
```

## 9. Política de freeze

Durante la ejecución normal del piloto:

- no se agregan capacidades nuevas a DevPilot;
- no se refactoriza DevPilot por oportunidad;
- no se corrigen problemas cosméticos en caliente;
- no se relajan gates para “hacer pasar” una fase;
- no se cambia el baseline sin registrar una nueva iteración del piloto.

Solo se permite parchear DevPilot si aparece un defecto `S0` o `S1` que impide continuar.

### 9.1. Severidades

| Severidad | Definición | Acción |
|---|---|---|
| S0 | Riesgo de pérdida de datos, violación de seguridad o acción destructiva no gobernada. | Detener inmediatamente. |
| S1 | Bloqueo total sin workaround seguro. | Pausar, proyectar patch y repetir checkpoint. |
| S2 | Gap importante con workaround seguro y trazable. | Continuar y registrar. |
| S3 | Fricción, copy, layout o mejora menor. | Continuar y priorizar después. |

## 10. No-go gates del piloto

Deben permanecer verdaderos durante toda la ejecución:

```text
local_first=true
dry_run_default=true
network_runtime_allowed=false
external_apis_allowed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
production_multiuser_enabled=false
enterprise_ready_claimed=false
saas_ready_claimed=false
compliance_certified_claimed=false
```

Una variación no aprobada produce `BLOCK` y detención del piloto.

## 11. Política de red y costos

El runtime de DevPilot y la aplicación piloto no deben requerir red externa.

La provisión inicial de dependencias puede requerir acceso a repositorios Python/npm. Esa actividad debe clasificarse por separado:

```text
network_for_environment_provisioning != network_used_by_application_runtime
```

Opciones, en orden de preferencia:

1. usar cache local ya disponible;
2. usar wheelhouse/npm cache previamente preparado;
3. autorizar una ventana de red solo para instalación;
4. registrar dominios, fecha y paquetes descargados;
5. volver a modo sin red antes de iniciar el piloto funcional.

No usar API keys pagas en el primer piloto.

---

## Parte III — Estructura de evidencia

## 12. Directorio de evidencia

Crear:

```text
D:\Projects\DevPilot_E2E_Evaluation\evidence\PILOT-E2E-001\
├── 00_control\
├── 01_baseline_installation\
├── 02_ui_api_startup\
├── 03_ui_baseline_acceptance\
├── 04_workspace_onboarding\
├── 05_precode_requirements_architecture_security\
├── 06_implementation_cycles\
├── 07_testing_traceability\
├── 08_documentation\
├── 09_release_candidate\
├── 10_clean_install_validation\
├── 11_incidents_and_ux_gaps\
└── 12_final_assessment\
```

No guardar secretos, tokens, `.env`, bases de datos productivas ni raw prompts sensibles.

## 13. Convención de nombres

```text
<UTC-or-local-timestamp>_<phase>_<artifact>_<status>.<ext>
```

Ejemplos:

```text
20260713T091500-0500_01_baseline_hashes_PASS.txt
20260713T103000-0500_03_ui_dashboard_loading_PASS.png
20260713T110500-0500_04_workspace_bootstrap_dry_run_PASS.json
20260714T083000-0500_06_story_INV-001_traceability_PASS.md
20260715T170000-0500_11_UX-GAP-007_workspace_registration_cli_only.md
```

## 14. Manifest de evidencia

Crear `00_control/evidence_manifest.json`:

```json
{
  "pilot_id": "PILOT-E2E-001",
  "baseline": "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip",
  "baseline_sha256": "<sha256>",
  "started_at": "<ISO-8601>",
  "operator": "<name>",
  "environment": {
    "os": "Windows",
    "python": "<version>",
    "node": "<version>",
    "git": "<version>"
  },
  "artifacts": []
}
```

Cada evidencia relevante debe registrar:

- ruta;
- SHA-256;
- fase;
- comando o acción UI que la produjo;
- resultado;
- operador;
- timestamp;
- sensibilidad/redacción.

---

## Parte IV — Fase 0: autorización y preparación

## 15. FASE 0 — Pilot Charter

### Objetivo

Autorizar el piloto antes de instalar o modificar artefactos.

### Paso 0.1 — Crear el charter

Crear:

```text
00_control/PILOT-E2E-001_charter.md
```

Contenido mínimo:

```markdown
# PILOT-E2E-001 — Charter

## Objetivo
Validar DevPilot end-to-end con un proyecto local de ventas e inventario.

## Baseline
- Repo:
- SHA-256:
- Patch:
- SHA-256:

## Alcance
...

## Fuera de alcance
...

## Roles
...

## Criterios PASS/BLOCK
...

## Fecha de inicio
...

## Aprobación
...
```

### Paso 0.2 — Registrar riesgos iniciales

Crear `00_control/initial_risk_register.md` con al menos:

- dependencia de instalación npm;
- limitaciones de UI;
- duración de suite general;
- riesgo de contaminación del repo;
- riesgo de almacenar token o secretos;
- riesgo de confundir dry-run con ejecución;
- riesgo de introducir patches durante evaluación;
- riesgo de falsos PASS/BLOCK;
- riesgo de reportes no visibles desde UI.

### Paso 0.3 — Definir criterio de detención

Detener si ocurre cualquiera de los siguientes:

- mutación destructiva no autorizada;
- exposición de secreto;
- ejecución remota;
- connector write;
- plugin execution;
- acción crítica sin aprobación;
- corrupción de baseline;
- inconsistencia que invalide la evidencia;
- pérdida de trazabilidad entre historia y cambio.

### Criterio PASS de FASE 0

```text
charter aprobado
+ roles asignados
+ baseline identificado
+ riesgos registrados
+ criterios de detención aceptados
```

---

## Parte V — Fase 1: instalación reproducible del baseline

## 16. Prerrequisitos de estación

Verificar:

```powershell
$PSVersionTable.PSVersion
py --version
python --version
git --version
node --version
npm --version
```

Requisitos mínimos del baseline:

- Python 3.10 o superior; recomendado 3.12;
- Git disponible para capacidades read-only;
- Node.js 20 o superior para la Web UI;
- PowerShell;
- espacio libre suficiente para `.venv`, npm cache y outputs;
- puerto local 8787 disponible;
- puerto local 5173 disponible.

Guardar la salida en:

```text
01_baseline_installation/tool_versions.txt
```

## 17. Paso 1.1 — Copiar el baseline aprobado

```powershell
$EvalRoot = "D:\Projects\DevPilot_E2E_Evaluation"
$BaselineZip = "$EvalRoot\baselines\repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
$PlatformRoot = "$EvalRoot\platform\DevPilot_Local_318_EVAL"
```

## 18. Paso 1.2 — Calcular hashes

```powershell
Get-FileHash $BaselineZip -Algorithm SHA256
```

Guardar:

```powershell
Get-FileHash $BaselineZip -Algorithm SHA256 |
  Format-List | Out-File "$EvalRoot\evidence\PILOT-E2E-001\01_baseline_installation\baseline_sha256.txt"

```

No continuar si el hash del baseline no corresponde al aprobado en el charter.

## 19. Paso 1.3 — Extraer en ruta nueva

```powershell
New-Item -ItemType Directory -Force "$EvalRoot\platform" | Out-Null
Expand-Archive -Path $BaselineZip -DestinationPath "$EvalRoot\platform\_extract" -Force
```

Identificar la carpeta raíz resultante y mover/copiar su contenido a `$PlatformRoot`.

No sobrescribir una instalación existente.

## 20. Paso 1.4 — Verificar que el cierre administrativo ya está integrado

El baseline 318 fue generado después de aplicar y versionar la activación y la sincronización documental previa. No requiere overlays adicionales antes del micro-sprint 01-A. No debe aplicarse un ZIP diferencial adicional. Verificar que existan:

```text
$PlatformRoot\.devpilot\project_state.json
$PlatformRoot\docs\post_h_034_closure_manifest.json
$PlatformRoot\tests\test_post_h_034_closure_regression_reconciliation.py
```

## 21. Paso 1.5 — Inventario post-overlay

```powershell
Get-ChildItem $PlatformRoot -Recurse -File |
  Select-Object FullName, Length, LastWriteTime |
  Export-Csv `
    "$EvalRoot\evidence\PILOT-E2E-001\01_baseline_installation\platform_file_inventory.csv" `
    -NoTypeInformation
```

## 22. Paso 1.6 — Git de evaluación

Si el ZIP limpio no contiene `.git`, no inventar historia del proyecto original.

Opciones:

### Opción preferida

Usar una copia/clon real del repositorio Git en el commit equivalente al baseline 318.

### Opción controlada para evaluación

Inicializar un repositorio local solo para trazabilidad del piloto:

```powershell
Set-Location $PlatformRoot
git init
git add .
git commit -m "Baseline DevPilot 318 for PILOT-E2E-001"
git tag pilot-e2e-001-baseline
```

Registrar claramente que este commit es un baseline de evaluación y no preserva la historia previa.

## 23. Paso 1.7 — Crear entorno Python

```powershell
Set-Location $PlatformRoot
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
$env:PYTHONPATH = "src"
```

Guardar:

```powershell
python -m pip freeze |
  Out-File "$EvalRoot\evidence\PILOT-E2E-001\01_baseline_installation\pip_freeze.txt"
```

## 24. Paso 1.8 — Preparar frontend

Desde el repo:

```powershell
Set-Location $PlatformRoot
npm --prefix ui/web ci
```

Si se exige instalación sin red:

```powershell
npm --prefix ui/web ci --offline
```

`--offline` solo funcionará si el cache contiene todas las dependencias.

Registrar si hubo red de aprovisionamiento:

```text
network_provisioning_used=true|false
runtime_external_network_allowed=false
```

## 25. Paso 1.9 — Validaciones del cierre POST-H-034

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_closure_regression_reconciliation.py `
  tests/test_post_h_eval_002_activation_contract.py `
  -q

python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core release-candidate evidence-freshness --json
```

Resultados esperados:

```text
POST-H-034 closure contract: PASS
Project State: PASS
Documentation Governance: PASS
TCR v1: PASS
TCR v2: PASS
Evidence Freshness: PASS
```

## 26. Paso 1.10 — Baseline de pruebas

Es obligatorio ejecutar la regresión general sobre el baseline 318 antes de aceptar G0/G1 y comenzar trabajo funcional del piloto:

```powershell
python -m pytest -p no:ddtrace --assert=plain -q `
  2>&1 | Tee-Object `
  "$EvalRoot\evidence\PILOT-E2E-001\01_baseline_installation\pytest_baseline.log"
```

Criterio esperado:

```text
1919 passed
0 failed
0 errors
0 skipped
```

Si la suite no coincide, el piloto queda `BLOCKED-BASELINE-DRIFT`.

Para una instalación limpia de un ZIP cuyo SHA-256 coincide exactamente con el baseline congelado y que no modifica fuente, puede heredarse la regresión general autoritativa 1919/1919 y ejecutar el closure contract focal más los validadores de gobernanza. La regresión completa se repite si cambia el hash, aparece drift funcional/de dependencias, existe S0/S1 o un gate posterior la exige.

### Criterio PASS de FASE 1

```text
hash del baseline confirmado
+ cierre administrativo integrado
+ entorno Python funcional
+ frontend instalado
+ Project State PASS
+ docs governance PASS
+ TCR PASS
+ evidence freshness PASS
```

---

## Parte VI — Fase 2: arranque de API y Web UI

## 27. Paso 2.1 — Preflight de API

```powershell
Set-Location $PlatformRoot
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"

python -m devpilot_core api serve `
  --host 127.0.0.1 `
  --port 8787 `
  --dry-run `
  --json
```

Debe confirmar:

- bind local;
- puerto previsto;
- no wildcard CORS;
- token requerido para rutas protegidas;
- sin apertura de socket durante dry-run.

## 28. Paso 2.2 — Generar token temporal

```powershell
python -m devpilot_core api token --json
```

Copiar el valor a una variable de sesión:

```powershell
$env:DEVPILOT_API_TOKEN = "<token-generado>"
```

Reglas:

- no escribirlo en el runbook;
- no guardarlo en Git;
- no incluirlo en screenshots;
- no almacenarlo en el manifest de evidencia;
- cerrar la terminal al terminar el piloto del día.

## 29. Paso 2.3 — Iniciar API

Terminal 1:

```powershell
Set-Location $PlatformRoot
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
$env:DEVPILOT_API_TOKEN = "<token-generado>"

python -m devpilot_core api serve `
  --host 127.0.0.1 `
  --port 8787 `
  --execute
```

Registrar hora de inicio y PID.

## 30. Paso 2.4 — Pruebas estáticas de UI

Terminal 2:

```powershell
Set-Location $PlatformRoot
npm --prefix ui/web test
npm --prefix ui/web run test:visual
npm --prefix ui/web run test:operator-flows
npm --prefix ui/web run test:route-enforcement
```

No iniciar el piloto funcional si cualquiera falla.

## 31. Paso 2.5 — Iniciar Web UI

```powershell
Set-Location $PlatformRoot
npm --prefix ui/web run dev -- `
  --host 127.0.0.1 `
  --port 5173
```

Abrir:

```text
Web UI:             http://127.0.0.1:5173
Swagger diagnóstico: http://127.0.0.1:8787/api/v1/docs
```

Swagger se usa para diagnóstico, no como superficie principal del operador.

## 32. Paso 2.6 — Configurar sesión UI

La UI usa token local y no debe persistirlo fuera de `sessionStorage`.

Verificar:

- token válido permite acceso;
- cerrar la pestaña/sesión elimina el token;
- token no aparece en URLs;
- token no aparece en Report Viewer;
- token no aparece en traces;
- token no aparece en screenshots.

## 33. Paso 2.7 — Smoke API/UI

```powershell
python -m devpilot_core api contract-drift --json --write-report
python -m devpilot_core api security-hardening --json --write-report
python -m devpilot_core api visual-smoke-report --json --write-report
python -m devpilot_core api operator-flow-smoke --json --write-report
python -m devpilot_core api ui-route-enforcement --json --write-report
python -m devpilot_core release-candidate ui-api-smoke `
  --base-url http://127.0.0.1:8787 `
  --json `
  --write-report
```

Copiar los reportes relevantes a la carpeta de evidencia o registrar sus hashes y rutas.

### Criterio PASS de FASE 2

```text
API local operativa
+ UI local operativa
+ token requerido
+ pruebas npm PASS
+ contract drift PASS
+ security hardening PASS
+ visual/operator/route smoke PASS
```

---

## Parte VII — Fase 3: aceptación detallada de la Web UI

## 34. Objetivo

Validar la UI como producto de operador antes de usarla para evaluar un proyecto real.

No basta con que cargue. Debe mostrar estados correctos, fallar de forma comprensible y respetar contratos.

## 35. Matriz de rutas UI

### 35.1. Dashboard `/`

Verificar:

- carga inicial;
- workspace status;
- readiness;
- standards;
- MIASI;
- Operator Dashboard embebido;
- badges `local-first`, `dry-run`, `no-remote`;
- PASS/WARN/BLOCK/ERROR/PENDING visibles;
- next actions;
- source references cuando corresponda;
- ausencia de controles destructivos.

Evidencias:

```text
03_ui_baseline_acceptance/dashboard_normal.png
03_ui_baseline_acceptance/dashboard_block_state.png
03_ui_baseline_acceptance/dashboard_sources.md
```

### 35.2. Reports `/reports`

Verificar:

- lista vacía;
- lista con reportes;
- apertura de reporte;
- findings legibles;
- rutas y timestamps;
- errores de reporte inexistente;
- ninguna lectura directa del filesystem desde navegador;
- redacción de secretos.

### 35.3. Traces `/traces`

Verificar:

- lista vacía;
- lista con traces;
- inspección de trace;
- correlación con operación;
- spans/handoffs visibles cuando existan;
- error controlado para trace inválido;
- ausencia de raw prompts/outputs sensibles.

### 35.4. Approval Center `/approvals`

Verificar:

- estado vacío;
- creación de solicitud local;
- visualización pending;
- aprobación;
- denegación;
- actor y justificación visibles;
- asociación con acción/herramienta cuando exista;
- acciones allowlisted solo en dry-run;
- ausencia de `patch apply`, `git push`, `deploy`, `rollback execute` y `refactor execute`.

### 35.5. Settings `/settings`

Verificar:

- workspace settings visibles;
- provider settings visibles y redactados;
- policy settings visibles;
- security posture;
- provider editor en modo plan-only;
- ningún secret value;
- ninguna escritura directa desde browser;
- error controlado si API no responde.

## 36. Matriz de estados negativos

Ejecutar uno por uno:

| Caso | Procedimiento | Esperado |
|---|---|---|
| Token ausente | Abrir sesión sin token. | 401 visible y recuperable. |
| Token inválido | Introducir token incorrecto. | 401/403 sin leak. |
| API caída | Detener API con UI abierta. | Estado API-down comprensible. |
| Reports vacíos | Limpiar runtime permitido o usar workspace sin reportes. | Empty state, no error. |
| Traces vacíos | Usar workspace sin traces. | Empty state, no error. |
| Acción prohibida | Intentar operación fuera de allowlist. | BLOCK visible. |
| Reporte corrupto | Fixture controlado, nunca evidencia canónica. | ERROR controlado. |
| Timeout | Simular operación lenta permitida. | Diagnóstico, no congelamiento indefinido. |

## 37. Criterio de aceptación UI

### Gate obligatorio

```text
100% de rutas críticas visitadas
100% de estados negativos ejecutados
0 secretos expuestos
0 controles críticos no autorizados
0 errores no manejados
0 divergencias de contrato API/UI
```

### Métrica diagnóstica

No usar como gate único el porcentaje global UI, porque la UI actual no cubre toda la autoría del SDLC.

Calcular dos métricas:

```text
UI Eligible Coverage =
operaciones realizadas por UI
/
operaciones que tienen superficie UI registrada
```

Objetivo: `100%`.

```text
Overall UI Coverage =
operaciones del piloto realizadas completamente por UI
/
total de operaciones del piloto
```

Esta segunda métrica es diagnóstica y alimenta el roadmap.


## 37.1. Baseline de aceptación 01-D

Antes de la captura formal debe verificarse que se opera:

```text
repo_DevPilot_Local_322_POST_H_EVAL_002_01_D_ACCEPTANCE_READY.zip
```

La preparación implementa:

- dispatch runtime explícito de las cinco rutas contractuales;
- navegación local y foco de ruta;
- timeout HTTP de 8 segundos con estado recuperable;
- test estático `npm --prefix ui/web run test:acceptance-baseline`.

Estos controles no sustituyen la evidencia browser. El operador debe conservar
el baseline 318 y materializar una nueva plataforma 322 separada. No debe aplicar
el patch sobre `platform/DevPilot_Local_318_EVAL` en caliente.

El resultado previo a la ejecución formal es:

```text
01-D implemented = true
01-D browser evidence = pending
01-D closed = false
02-A authorized = false
```

---

## Parte VIII — Fase 4: creación y onboarding del workspace piloto

## 38. Paso 4.1 — Definir variables

```powershell
$PilotRoot = "D:\Projects\DevPilot_E2E_Evaluation\workspaces\inventory-sales-local"
$PilotId = "inventory-sales-local"
$PilotName = "Sistema local de ventas e inventario"
```

## 39. Paso 4.2 — Bootstrap dry-run

Desde el repo de plataforma:

```powershell
python -m devpilot_core workspace bootstrap `
  --project-id $PilotId `
  --project-name $PilotName `
  --project-type agent-assisted-sdlc `
  --target-root $PilotRoot `
  --dry-run `
  --json `
  --write-report
```

Verificar antes de ejecutar:

- target root correcto;
- archivos previstos;
- no sobrescrituras;
- no secretos;
- no rutas fuera del workspace;
- no mutaciones reportadas en dry-run.

## 40. Paso 4.3 — Revisar reporte desde UI

Ir a `/reports`.

Verificar que el reporte de bootstrap:

- aparece en la lista;
- puede abrirse;
- muestra dry-run;
- lista archivos planificados;
- no afirma que fueron creados;
- expone findings y paths.

Si no aparece, registrar:

```text
UX-GAP — bootstrap report not discoverable from Reports UI
```

## 41. Paso 4.4 — Autorizar ejecución

Crear una aprobación o registro equivalente antes de `--execute`, aunque el bootstrap sea local y acotado.

Guardar:

- actor;
- justificación;
- target root;
- hash del plan;
- timestamp;
- decisión.

## 42. Paso 4.5 — Ejecutar bootstrap

```powershell
python -m devpilot_core workspace bootstrap `
  --project-id $PilotId `
  --project-name $PilotName `
  --project-type agent-assisted-sdlc `
  --target-root $PilotRoot `
  --execute `
  --json `
  --write-report
```

Verificar:

```text
$PilotRoot\.devpilot\project.yaml
```

No continuar si se crean archivos fuera de `$PilotRoot` o de outputs autorizados.

## 43. Paso 4.6 — Readiness preview inicial

```powershell
python -m devpilot_core workspace readiness-preview `
  --target-root $PilotRoot `
  --project-id $PilotId `
  --project-name $PilotName `
  --json `
  --write-report
```

El primer resultado puede ser PENDING/BLOCK por artefactos faltantes. Eso es correcto.

Registrar la lista exacta de gaps.

## 44. Paso 4.7 — Registrar workspace

```powershell
python -m devpilot_core workspace register `
  --path $PilotRoot `
  --workspace-id "pilot-inventory-sales-local" `
  --name $PilotName `
  --json `
  --write-report
```

Después:

```powershell
python -m devpilot_core workspace registry-validate --json
python -m devpilot_core workspace isolation-check --json
python -m devpilot_core workspace list --json
python -m devpilot_core portfolio status --json
```

Consultar `--help` antes si el comando requiere un argumento adicional en el baseline vigente.

## 45. Paso 4.8 — Verificación UI post-registro

Volver a `/` y `/settings`.

Verificar:

- workspace visible;
- nombre correcto;
- estado readiness coherente;
- portfolio/operator dashboard actualizado;
- sin necesidad de refresco manual no documentado;
- sin stale cache.

Registrar cualquier diferencia CLI↔UI como `CONTRACT-DRIFT`.

### Criterio PASS de FASE 4

```text
bootstrap dry-run revisado
+ execute autorizado
+ workspace materializado
+ registry valid
+ isolation PASS
+ estado visible en UI
```

---

## Parte IX — Fase 5: pre-code, requisitos, arquitectura y seguridad

## 46. Plantillas versionadas disponibles

Usar como base:

```text
docs/templates/new_project/product_vision.template.md
docs/templates/new_project/mvp_scope.template.md
docs/templates/new_project/requirements_specification.template.md
docs/templates/new_project/architecture_document.template.md
docs/templates/new_project/security_threat_model.template.md
docs/templates/new_project/test_strategy.template.md
docs/templates/new_project/miasi_agent_registry.template.json
docs/templates/new_project/miasi_tool_registry.template.json
docs/templates/new_project/miasi_policy_matrix.template.json
```

Copiar y adaptar dentro del workspace piloto, nunca editar las plantillas canónicas del repo DevPilot para personalizar un proyecto.

## 47. Paso 5.1 — Product Vision

Definir:

- problema;
- usuarios;
- objetivos;
- resultados medibles;
- restricciones;
- riesgos;
- fuera de alcance.

Criterios:

- no contiene solución detallada prematura;
- no introduce nube/APIs externas;
- identifica operación local;
- tiene frontmatter válido;
- puede rastrearse al charter.

## 48. Paso 5.2 — MVP Scope

Definir historias mínimas:

```text
INV-001 Crear producto
INV-002 Registrar entrada de inventario
INV-003 Registrar salida/ajuste
SAL-001 Registrar venta
SAL-002 Consultar detalle de venta
REP-001 Ver reporte básico
ALT-001 Ver alerta de stock mínimo
OPS-001 Ejecutar backup local
```

Cada historia debe incluir:

- actor;
- precondiciones;
- flujo;
- criterios de aceptación;
- errores esperados;
- datos;
- pruebas;
- riesgos.

## 49. Paso 5.3 — Requirements Specification

Requisitos mínimos:

- funcionales;
- no funcionales;
- seguridad;
- observabilidad;
- trazabilidad;
- instalación;
- recuperación;
- restricciones de datos.

Asignar IDs estables:

```text
FR-INV-001
FR-SAL-001
NFR-SEC-001
NFR-OPS-001
NFR-TEST-001
```

## 50. Paso 5.4 — Arquitectura

Arquitectura inicial recomendada:

```text
React UI
   ↓ HTTP localhost
FastAPI API
   ↓
Application/Domain services
   ↓
Repository layer
   ↓
SQLite
```

Decisiones obligatorias:

- monorepo o carpetas separadas;
- módulos de dominio;
- contratos de API;
- migraciones;
- estrategia de errores;
- configuración local;
- logging;
- test pyramid;
- packaging.

No copiar la arquitectura interna de DevPilot al proyecto piloto sin justificarla.

## 51. Paso 5.5 — Threat Model

Cubrir como mínimo:

- manipulación de inventario;
- venta duplicada;
- pérdida/corrupción de SQLite;
- path traversal en exportaciones;
- exposición de configuración;
- inyección en campos de texto;
- errores de autorización local si se implementa un rol simple;
- backup/restore;
- integridad de reportes;
- dependencia del navegador local.

No declarar cumplimiento normativo ni seguridad certificada.

## 52. Paso 5.6 — Test Strategy

Definir:

- unit tests de dominio;
- integration tests de repositorio/API;
- contract tests API;
- UI smoke;
- fixtures;
- full regression;
- criterios de flakiness;
- tiempos máximos orientativos;
- política de datos de prueba.

## 53. Paso 5.7 — MIASI

Crear y validar:

- Agent Registry;
- Tool Registry;
- Policy Matrix.

Comandos:

```powershell
python -m devpilot_core miasi validate --json
python -m devpilot_core miasi semantic-validate --json
```

Mantener:

- tools allowlisted;
- dry-run por defecto;
- tools de escritura approval-gated;
- sin connector write;
- sin plugin execution;
- sin remote execution.

## 54. Paso 5.8 — Validaciones pre-code

```powershell
python -m devpilot_core validate docs --json --write-report
python -m devpilot_core validate contracts --json --write-report
python -m devpilot_core validate all --json --write-report
python -m devpilot_core checklist-pre-code --json --write-report
python -m devpilot_core readiness-check --strict --json --write-report
python -m devpilot_core standards status --json
```

Si la sintaxis exacta difiere, consultar:

```powershell
python -m devpilot_core <grupo> --help
```

No alterar el gate para convertir BLOCK en PASS.

## 55. Paso 5.9 — Revisión desde UI

Usar:

- Dashboard para readiness/standards/MIASI;
- Reports para validaciones;
- Traces para operaciones;
- Approvals para decisiones;
- Settings para posture.

Registrar:

- artefactos no descubribles;
- findings sin explicación;
- fuentes ausentes;
- diferencias entre CLI y UI;
- necesidad de abrir filesystem manualmente.

### Criterio PASS de FASE 5

```text
visión aprobada
+ scope aprobado
+ requisitos trazables
+ arquitectura aprobada
+ threat model aprobado
+ test strategy aprobada
+ MIASI PASS
+ readiness strict PASS
```

---

## Parte X — Fase 6: implementación asistida iterativa

## 56. Regla de iteración

Implementar en historias pequeñas. No construir todo el sistema y validar al final.

Ciclo obligatorio:

```text
seleccionar historia
→ confirmar artefactos y aceptación
→ obtener análisis DevPilot
→ revisar fuentes
→ planificar cambio
→ dry-run
→ aprobación humana si aplica
→ editar/aplicar
→ pruebas focales
→ code/patch review
→ test impact
→ reports/traces UI
→ commit
```

## 57. Branching recomendado

En el repo del proyecto piloto:

```text
main
pilot/INV-001-create-product
pilot/INV-002-stock-entry
pilot/SAL-001-register-sale
...
```

Commits pequeños y descriptivos.

## 58. Registro por historia

Crear:

```text
06_implementation_cycles/<story-id>/story_execution_record.md
```

Plantilla:

```markdown
# Historia <ID>

## Requisito relacionado

## Criterios de aceptación

## Análisis DevPilot

## Fuentes utilizadas

## Plan/dry-run

## Aprobación

## Archivos modificados

## Pruebas focales

## Findings

## Trace/report IDs

## Resultado
PASS | BLOCK | WAIVED

## Commit
```

## 59. Capacidades de análisis recomendadas

Según la historia, usar de forma acotada:

```powershell
python -m devpilot_core repo-inventory --help
python -m devpilot_core repo --help
python -m devpilot_core code-review --help
python -m devpilot_core patch-review --help
python -m devpilot_core refactor-plan --help
python -m devpilot_core agent capability-inventory --json
python -m devpilot_core agent rag-context --json
python -m devpilot_core multiagent run --help
python -m devpilot_core multiagent workflow --help
```

No ejecutar comandos desconocidos sin revisar `--help` y confirmar su modo dry-run.

## 60. Uso de RAG

Para una recomendación basada en documentación:

- usar únicamente fuentes allowlisted;
- exigir citations/source IDs;
- verificar freshness;
- tratar `insufficient-evidence` como resultado válido;
- no convertir memoria en evidencia formal;
- no aceptar claims sin fuente.

## 61. Uso de memoria

Si se activa memoria local opt-in:

- mantenerla deshabilitada por defecto;
- separar session/project memory;
- no almacenar secretos;
- no almacenar raw prompts/outputs;
- aplicar retención;
- exportar siempre redactado;
- no usar memoria como prueba de aceptación.

## 62. Uso de tool calling

Mantener:

- tool allowlist por agente;
- dry-run-first;
- approval binding para riesgosas;
- ToolInjectionGuard;
- traceability;
- límite de pasos;
- timeout;
- cero ejecución genérica de shell.

## 63. Handoffs multiagente

Si se usa `sdlc_review`:

- handoffs explícitos;
- supervisor determinístico;
- checkpoints humanos;
- ningún swarm autónomo;
- scopes y tools no heredados implícitamente;
- trace visible en UI.

## 64. Cambio de plataforma detectado durante historia

Si el problema está en DevPilot, no mezclar el fix con la historia del piloto.

Crear incidente:

```text
PLATFORM-DEFECT-<NNN>
```

Incluir:

- reproducción;
- causa probable;
- evidencia;
- severidad;
- workaround;
- decisión de pausar/continuar.

### Criterio PASS por historia

```text
criterios de aceptación PASS
+ pruebas focales PASS
+ review sin blockers
+ trace/report disponible
+ commit trazable
+ no-go gates preservados
```

---

## Parte XI — Fase 7: testing, impacto y trazabilidad

## 65. Test Impact por cambio

Antes de seleccionar pruebas:

```powershell
python -m devpilot_core test-impact analyze-v2 `
  --changed-paths <ruta1> <ruta2> `
  --json `
  --write-report
```

Si el parser admite una forma distinta, consultar `--help` y registrar el comando real utilizado.

Revisar:

- reglas matched;
- dominios;
- perfiles recomendados;
- tests recomendados;
- residual risk;
- full regression signal;
- waiver signal.

## 66. Test Contract Registry

Validar periódicamente:

```powershell
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

Para el proyecto piloto, mantener un registro equivalente o adaptar el mecanismo disponible sin contaminar el registry de DevPilot con contratos de la aplicación, salvo que el diseño multiworkspace lo contemple explícitamente.

## 67. Pirámide mínima del proyecto piloto

| Nivel | Ejemplos |
|---|---|
| Unit | stock, venta, total, validaciones de dominio. |
| Repository | SQLite, transacciones y consultas. |
| API | endpoints, errores, schemas. |
| Contract | OpenAPI/DTOs frontend-backend. |
| UI smoke | navegación y flujo principal. |
| E2E crítico | crear producto → entrada → venta → stock actualizado. |

## 68. Regresión por milestone

Ejecutar full regression del proyecto:

- al cerrar módulo de inventario;
- al cerrar módulo de ventas;
- antes del RC;
- después de instalación limpia.

Ejecutar full regression de DevPilot:

- al inicio;
- después de cualquier patch de plataforma;
- antes del assessment final si hubo patches.

## 69. Quality Gate de DevPilot

```powershell
python -m devpilot_core quality-gate run `
  --profile hardening `
  --json
```

No confundir el gate de DevPilot con la calidad de la aplicación piloto. Se requieren ambos.

## 70. Trazabilidad mínima

Cada requisito debe mapear a:

```text
requirement ID
→ story ID
→ architecture/security decision
→ files changed
→ tests
→ report/trace
→ commit
→ release evidence
```

Gaps de trazabilidad producen `BLOCK` para el RC.

---

## Parte XII — Fase 8: evaluación continua de la UI durante el SDLC

## 71. Registro de bridges CLI

Cada uso de CLI por ausencia de UI debe crear un registro:

```markdown
# UX-GAP-<NNN> — <operación>

## Fase

## Operación requerida

## Resultado deseado

## Superficie UI esperada

## Razón por la que no pudo completarse en UI

## Comando CLI utilizado

## Evidencia generada

## Riesgo

## Frecuencia

## Prioridad recomendada
P0 | P1 | P2 | P3
```

## 72. Tipos de bridge

- `INSTALLATION-BRIDGE`: venv/npm/startup.
- `WORKSPACE-BRIDGE`: bootstrap/register/select.
- `AUTHORING-BRIDGE`: edición de Markdown/JSON en IDE.
- `EXECUTION-BRIDGE`: tests/gates/release.
- `DIAGNOSTIC-BRIDGE`: inspectores avanzados.
- `RECOVERY-BRIDGE`: backup/rollback.

## 73. Hallazgos UI

Clasificar:

- `UI-MISSING-CAPABILITY`;
- `UI-DISCOVERABILITY`;
- `UI-STATE-DISCREPANCY`;
- `UI-ERROR-HANDLING`;
- `UI-PERFORMANCE`;
- `UI-ACCESSIBILITY`;
- `UI-SECURITY`;
- `UI-TRACEABILITY`;
- `UI-COPY`;
- `API-UI-CONTRACT-DRIFT`.

## 74. Métricas UI

Calcular:

```text
Critical Route Coverage
= critical UI routes exercised / 5
```

```text
Eligible UI Coverage
= operations completed in UI / UI-eligible operations
```

```text
CLI Bridge Ratio
= CLI bridges / total operator operations
```

```text
UI Recovery Success
= recovered negative states / negative states executed
```

```text
Report Discoverability
= generated reports found through UI / reports expected to be visible
```

No maquillar el resultado excluyendo bridges incómodos.

---

## Parte XIII — Fase 9: documentación del proyecto piloto

## 75. Documentos mínimos

El proyecto piloto debe terminar con:

- README;
- visión;
- alcance MVP;
- requisitos;
- arquitectura;
- threat model;
- ADRs;
- test strategy;
- runbook de operación;
- guía de instalación;
- changelog;
- release notes;
- troubleshooting;
- manifest de release;
- matriz requisito→test.

## 76. Reglas documentales

- frontmatter consistente;
- IDs estables;
- estado explícito;
- owner;
- versión;
- fecha;
- aprobación;
- fuentes;
- comandos reproducibles;
- no incluir secretos;
- no afirmar enterprise/compliance/SaaS.

## 77. Documentación visible desde UI

Medir qué documentos/reportes pueden localizarse desde `/reports` y cuáles requieren filesystem/IDE.

Registrar como UX gap cualquier artefacto crítico que no pueda descubrirse desde UI.

---

## Parte XIV — Fase 10: release candidate local

## 78. Precondiciones del RC

- todas las historias MVP aceptadas;
- cero S0/S1 abiertos;
- pruebas focales PASS;
- full regression de la aplicación PASS;
- trazabilidad completa;
- docs vigentes;
- no-go gates preservados;
- backup/rollback diseñado;
- UI funcional.

## 79. Evidence freshness de DevPilot

```powershell
python -m devpilot_core release-candidate evidence-freshness `
  --json `
  --write-report
```

## 80. Local RC de DevPilot

```powershell
python -m devpilot_core release-candidate final `
  --json `
  --write-report
```

Interpretar este resultado como evidencia de la plataforma, no como sustituto del RC del proyecto piloto.

## 81. Packaging del proyecto piloto

Definir un proceso propio que produzca:

- source ZIP limpio;
- checksums;
- manifest;
- build frontend;
- dependencias declaradas;
- base de datos demo o migraciones;
- guía de instalación;
- versión.

Puede usarse DevPilot para revisar políticas:

```powershell
python -m devpilot_core package source-zip-policy --json
python -m devpilot_core release artifact-manifest --help
python -m devpilot_core install windows-smoke --help
python -m devpilot_core release upgrade-rollback-dry-run --help
```

No asumir que comandos diseñados para empaquetar DevPilot empaquetan automáticamente cualquier workspace; comprobar alcance y documentar gaps.

## 82. Instalación limpia

Crear:

```text
D:\Projects\DevPilot_E2E_Evaluation\clean_install_validation\
```

Instalar el proyecto piloto desde sus artefactos, sin reutilizar:

- `.venv` anterior;
- `node_modules` anterior;
- SQLite operativa anterior;
- configuración temporal;
- rutas absolutas del workspace original.

## 83. Validación post-instalación

- iniciar backend;
- iniciar frontend;
- abrir UI del proyecto;
- crear producto;
- registrar entrada;
- registrar venta;
- verificar stock;
- generar reporte;
- ejecutar smoke tests;
- ejecutar backup/restore dry-run;
- detener y reiniciar.

## 84. Validación de DevPilot tras reinstalación del piloto

Registrar el workspace instalado o inspeccionarlo según el modelo soportado.

Verificar desde Web UI DevPilot:

- workspace/status;
- reports;
- traces;
- operator dashboard;
- no-go gates;
- RC evidence.

### Criterio PASS del RC

```text
artefactos reproducibles
+ checksums válidos
+ instalación limpia exitosa
+ aplicación funcional
+ UI funcional
+ tests PASS
+ trazabilidad completa
+ cero blockers
```

---

## Parte XV — Incidentes, correcciones y reanudación

## 85. Registro de incidente

```markdown
# INCIDENT-<NNN>

## Timestamp

## Fase/checkpoint

## Severidad

## Síntoma

## Pasos para reproducir

## Resultado esperado

## Resultado real

## Logs/evidencia

## Impacto

## Workaround seguro

## Causa raíz

## Decisión
continue | pause | abort | patch
```

## 86. Patch crítico de DevPilot

Si se requiere:

1. congelar evidencia actual;
2. crear backup del repo de plataforma;
3. abrir micro-patch separado;
4. modificar el mínimo de archivos;
5. añadir prueba de regresión;
6. ejecutar tests focales;
7. ejecutar full regression de DevPilot;
8. actualizar baseline/manifest;
9. registrar nueva versión de la ejecución;
10. repetir el checkpoint afectado.

La ejecución debe pasar de:

```text
PILOT-E2E-001-RUN-01
```

a:

```text
PILOT-E2E-001-RUN-02
```

No mezclar resultados de dos baselines sin identificarlos.

## 87. Aborto controlado

Abortar no significa fracaso del assessment. Un aborto puede ser el resultado correcto si revela un riesgo industrial.

Guardar:

- evidencia completa;
- punto exacto;
- causa;
- daños evitados;
- recomendación;
- condiciones para reanudar.

---

## Parte XVI — Fase 11: assessment industrial

## 88. Taxonomía final de hallazgos

- defecto funcional;
- contract drift;
- schema drift;
- UX gap;
- operación solo CLI;
- documentación insuficiente;
- observabilidad insuficiente;
- falso PASS;
- falso BLOCK;
- paso manual no documentado;
- riesgo de seguridad;
- problema de rendimiento;
- problema de instalación;
- problema de reproducibilidad;
- limitación arquitectónica legítima;
- capacidad sensible futura.

## 89. Dimensiones de madurez

Puntuar con evidencia, no intuición:

| Dimensión | Pregunta |
|---|---|
| Instalación | ¿Puede repetirse desde cero? |
| UI/Product UX | ¿Puede operarse y comprenderse desde Web UI? |
| Onboarding | ¿Un proyecto entra sin manipulación interna? |
| SDLC | ¿Las fases están conectadas? |
| Agentes | ¿Las recomendaciones son útiles y acotadas? |
| RAG | ¿Las fuentes y citations son suficientes? |
| Herramientas | ¿Dry-run/approval/tool scopes funcionan? |
| Multiagente | ¿Handoffs son visibles y gobernados? |
| Testing | ¿Impacto, contratos y regresión son prácticos? |
| Observabilidad | ¿Reportes/traces explican decisiones? |
| Seguridad | ¿No-go gates resisten? |
| Release | ¿El RC es reproducible? |
| Documentación | ¿La fuente canónica está clara? |
| Operación | ¿Es mantenible por un operador real? |

## 90. Escala propuesta

```text
0 = inexistente
1 = diseño/documento
2 = implementado aislado
3 = integrado con workaround importante
4 = integrado y repetible
5 = probado en operación representativa
```

No asignar nivel 5 únicamente por tests unitarios.

## 91. Reportes finales

Crear:

```text
12_final_assessment/
├── post_h_eval_002_baseline_assessment.md
├── pilot_findings_registry.json
├── pilot_metrics.json
├── ui_gap_register.md
├── architecture_hotspots.md
├── risk_register_final.md
├── maturity_scorecard.json
├── prioritized_gap_matrix.md
└── roadmap_recommendation.md
```

## 92. Priorización

Usar criterios:

- impacto de usuario;
- riesgo;
- frecuencia;
- bloqueo de flujo;
- costo;
- dependencia;
- evidencia;
- alineación web-first;
- preservación local-first.

## 93. Secuencia posterior

```text
Piloto C
→ Assessment A basado en evidencia
→ Nuevo roadmap
→ Backlogs por olas
→ Onboarding Report v2 B
```

El Onboarding Report se actualiza después del piloto para reflejar comportamiento real, no solo capacidades declaradas.

---

## Parte XVII — Criterios globales PASS/BLOCK

## 94. PASS del piloto

El piloto puede declararse PASS si:

- baseline 318 verificable;
- instalación reproducible;
- API y UI arrancan;
- cinco rutas UI críticas pasan;
- estados negativos pasan;
- no hay secretos expuestos;
- workspace onboarding completo;
- readiness strict PASS;
- proyecto MVP implementado;
- pruebas del proyecto PASS;
- trazabilidad completa;
- RC reproducible;
- clean install PASS;
- no-go gates preservados;
- todos los bridges CLI registrados;
- assessment y roadmap producidos.

## 95. PASS con gaps

Puede ser PASS con gaps si:

- no hay S0/S1;
- el proyecto llega a RC;
- los gaps son S2/S3;
- existen workarounds seguros;
- cada gap tiene evidencia y prioridad.

## 96. BLOCK

Es BLOCK si:

- baseline no reproducible;
- UI crítica no arranca;
- pérdida de datos;
- secreto expuesto;
- acción destructiva sin aprobación;
- capacidad sensible habilitada;
- divergencia que invalida trazabilidad;
- RC no instalable;
- suite crítica falla sin waiver válido;
- evidencia incompleta impide el assessment.

---

## Parte XVIII — Plantillas operativas

## 97. Bitácora diaria

```markdown
Fecha:
Run ID:
Fase:
Objetivo del día:
Acciones UI:
Bridges CLI:
Entregables:
Pruebas:
Resultado:
Errores:
Solución/workaround:
Hallazgos:
Riesgos:
Decisiones:
Pendiente:
Próximo paso:
```

## 98. Registro de UX gap

```markdown
ID:
Fecha:
Fase:
Usuario/rol:
Operación:
Ruta UI actual:
Comportamiento observado:
Comportamiento esperado:
Bridge CLI usado:
Frecuencia:
Impacto:
Severidad:
Evidencia:
Recomendación:
Backlog candidato:
```

## 99. Registro de decisión

```markdown
Decision ID:
Contexto:
Opciones:
Criterios:
Decisión:
Justificación:
Riesgos aceptados:
Evidencia:
Aprobador:
Fecha:
Revisión futura:
```

## 100. Checklist de cierre de historia

```text
[ ] requisito identificado
[ ] criterios de aceptación aprobados
[ ] análisis con fuentes
[ ] dry-run revisado
[ ] aprobación cuando aplica
[ ] cambios acotados
[ ] pruebas focales PASS
[ ] test impact revisado
[ ] review PASS
[ ] report/trace visible
[ ] commit creado
[ ] docs actualizadas
[ ] UX gaps registrados
```

## 101. Checklist de cierre del piloto

```text
[ ] baseline manifest completo
[ ] hashes confirmados
[ ] instalación reproducible
[ ] UI/API PASS
[ ] UI negative states PASS
[ ] onboarding PASS
[ ] pre-code PASS
[ ] MVP completo
[ ] test suite PASS
[ ] traceability PASS
[ ] RC PASS
[ ] clean install PASS
[ ] no-go gates PASS
[ ] evidence manifest completo
[ ] findings clasificados
[ ] maturity scorecard
[ ] roadmap recomendado
[ ] onboarding v2 planificado
```

---

## Parte XIX — Matriz resumida UI vs CLI

## 102. Superficie preferida por actividad

| Actividad | UI principal | CLI permitida | Observación |
|---|---|---|---|
| Estado general | Dashboard | `workspace status`, `portfolio status` | CLI solo diagnóstico. |
| Reportes | Reports | comandos `--write-report` | Reporte debe ser descubrible en UI. |
| Trazas | Traces | `trace ...` | CLI solo inspección avanzada. |
| Aprobaciones | Approval Center | `approval ...` | UI preferida. |
| Settings/posture | Settings | validadores | UI preferida. |
| Instalación | No disponible | obligatoria | Bridge legítimo. |
| Arranque servicios | No disponible | obligatoria | Bridge legítimo. |
| Bootstrap workspace | No disponible/completo | obligatoria | UX gap a medir. |
| Autoría docs | No disponible | IDE/filesystem | Gap de producto, no ocultar. |
| Readiness | Dashboard/Reports | obligatoria para ejecutar | Resultado debe verse en UI. |
| Agentes/RAG | Reports/Traces | ejecución CLI | Evaluar futura UI. |
| Tests | Reports | ejecución CLI | Evaluar launcher futuro. |
| Release | Reports | ejecución CLI | Evaluar wizard futuro. |

---

## Parte XX — Integración gobernada de este runbook en DevPilot

## 103. Procedimiento de incorporación al repo

El documento ya está aprobado. Para incorporarlo como autoridad canónica:

1. conservar la ruta exacta:

```text
docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md
```

2. registrar en:

```text
.devpilot/docs_governance/source_registry.json
```

3. clasificarlo como fuente de verdad P0 para:

```text
POST-H-EVAL-002 pilot procedure
```

4. registrar también el roadmap y los tres backlogs ejecutables derivados.

5. añadir un contrato documental, como mínimo:

```text
tests/test_post_h_eval_002_pilot_runbook_contract.py
```

6. validar:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

7. regenerar el índice documental RAG mediante el comando soportado por el baseline.

8. verificar que RAG recupera la versión `1.1.0` y no una guía preliminar.

9. actualizar README, runbook principal, changelog y Project State con el hito `POST-H-EVAL-002-01-A`, sin duplicar el contenido completo.

10. crear commit independiente:

```text
POST-H-EVAL-002 approve UI-first pilot runbook and executable roadmap
```

## 104. Contrato documental recomendado

El test debe comprobar:

- `status=approved`;
- `approval=approved_by_owner`;
- baseline 318 y sus hashes;
- pilot ID;
- UI-first;
- cinco rutas UI críticas;
- no-go gates;
- fases 0–11;
- instalación limpia;
- evidence manifest;
- PASS/BLOCK;
- bridges CLI;
- assessment y roadmap;
- ausencia de claims enterprise/SaaS/compliance;
- ausencia de referencias al baseline 314 o al patch administrativo separado.

No debe ejecutar el piloto desde pytest.

---

## Conclusión

Elevar el procedimiento a este documento es conveniente porque convierte el piloto en una evaluación:

- repetible;
- auditable;
- comparable;
- segura;
- orientada a evidencia;
- útil para priorización.

La decisión operacional recomendada es:

```text
1. Integrar el runbook aprobado en Documentation Governance.
2. Registrar el roadmap y los tres backlogs ejecutables.
3. Congelar baseline 318 aprobado y su hash.
4. Ejecutar PILOT-E2E-001 con enfoque UI-first.
5. Registrar todos los bridges CLI y gaps UI.
6. Completar RC e instalación limpia.
7. Elaborar POST-H-EVAL-002 baseline assessment.
8. Derivar nuevo roadmap.
9. Actualizar Onboarding Report v2.
```

El éxito del piloto no se medirá por evitar la CLI a toda costa. Se medirá por usar la UI en toda operación que ya tiene superficie, hacer explícita cada dependencia de CLI y convertir esa evidencia en decisiones de producto verificables.

## 2026-07-17 — POST-H-EVAL-002-01-D UI corrective baseline 323

- Current repository: `repo_DevPilot_Local_323_POST_H_EVAL_002_01_D_UI_ACCEPTANCE_FIX.zip`.
- RUN-01 partial archive is diagnostic-only: 5/6 requested diagnostic files, missing `process_lifecycle.json`, session still `running=true`, formal matrices remain 0/5, 0/8 and 0%.
- API log contains 115 HTTP requests and zero non-200 responses; API/UI stderr contain no application failure.
- Corrective UI removes embedded detail surfaces from Dashboard, limits protected browser concurrency to two, separates Reports/Traces, makes Settings states exclusive and fixes UNKNOWN/disabled gate semantics.
- Request timeout remains 8000 ms and exposes endpoint/retry context.
- Formal retest is `PILOT-E2E-001-RUN-02`; 01-D and backlog 01 remain open and 02-A is not authorized.

## 2026-07-21 — RUN-02 BLOCK y runtime corrective 324

- Current repository: `repo_DevPilot_Local_324_POST_H_EVAL_002_01_D_RUNTIME_CORRECTIVE.zip`.
- `PILOT-E2E-001-RUN-02` cerró forénsicamente en `BLOCK`; no constituye evidencia de aceptación.
- El cierre seguro dejó `session.running=false`, PIDs nulos, puertos 8787/5173 libres y `unknown_pid_killed=false`.
- El runtime corrective 324 preserva el timeout general de 8000 ms, agrega límites explícitos para operaciones costosas, warm-up protegido y feedback pending por acción.
- La validación autoritativa requerida es `PILOT-E2E-001-RUN-03`; 01-D y backlog 01 permanecen abiertos y 02-A no está autorizado.
- La no-regresión Python debe ejecutarse sobre un árbol fuente limpio: `ui/web/node_modules` se elimina después de los contratos npm y antes de `pytest -q`.


## 2026-07-22 — RUN-03 forensic closure and Browser Acceptance Corrective 325

- RUN-03 is preserved as `BLOCK-WITH-PROGRESS`: materialization, R6.2 runtime and lifecycle PASS; formal browser acceptance BLOCK.
- Product corrective: `repo_DevPilot_Local_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip`.
- Ordinary requests remain bounded to 8000 ms; expensive operations use explicit operation-specific budgets.
- Dry-run and provider-plan surfaces use exclusive `idle/loading/pass/block/timeout/error` states and never retain a previous PASS after timeout/error.
- Provider plan validates the synthetic proposal in memory and performs no provider-file write.
- Retest required: `PILOT-E2E-001-RUN-04`.
- `POST-H-EVAL-002-01-D` remains open and `POST-H-EVAL-002-02-A` remains unauthorized.

## 2026-07-30 — RERUN-03 PASS, Stop/Finalize y cierre de gobernanza 327

- `PILOT-E2E-001-RUN-05B-RERUN-02` permanece `BLOCK/product-contract-evidence`, `FORENSIC-ONLY`, sin promoción ni Finalize.
- `PILOT-E2E-001-RUN-05B-RERUN-03` es la evidencia autoritativa de aceptación del repo 326.
- La auditoría independiente leyó únicamente ZIP cerrados y concluyó `PASS`, `S0=0`, `S1=0`, `blockers=[]`.
- Se acreditaron rutas `5/5`, negativos `8/8`, operaciones `23/23`, correlaciones `13/13`, Bridges `8/8` y capturas `13+5`.
- Stop dejó `running=false`, puertos `8787/5173` libres, token DPAPI retirado, portapapeles limpio y `unknown_pid_killed=false`.
- Finalize se ejecutó exactamente una vez.
- Repo vigente de gobernanza: `repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip`.
- `POST-H-EVAL-002-01-D` y la ola 01 quedan cerrados; `POST-H-EVAL-002-02-A` queda autorizado.
- Este cierre no exige reiniciar API/UI, crear un token ni repetir HAR, Bridges o capturas.

## 2026-07-28 — RUN05B RERUN-02 forensic BLOCK and integral corrective 326

- RERUN-02 is preserved as `BLOCK/product-contract-evidence` and forensic-only; `Finalize` is not authorized.
- Product corrective: `repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip`.
- Dashboard consumes Health, Approval Center states are conditional, Settings fully redacts secret-like fields and state notices are accessible.
- Operator/auditor tooling must be corrected before a new run.
- Required retest: `PILOT-E2E-001-RUN-05B-RERUN-03`.
- `POST-H-EVAL-002-01-D` remains open and `POST-H-EVAL-002-02-A` remains unauthorized.
