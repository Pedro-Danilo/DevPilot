---
doc_id: "POST-H-024-A-OPERATOR-ONBOARDING-PLAYBOOK"
title: "POST-H-024-A — Playbook de operador DevPilot"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-024-A"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-024-A — Playbook de operador DevPilot

## 1. Propósito operacional

Este playbook convierte el onboarding conversacional de DevPilot en una guía versionada y verificable para que un operador pueda iniciar un proyecto nuevo desde una idea y avanzar hasta una línea base pre-code gobernada.

El objetivo de POST-H-024-A es **documental-operacional**: deja una guía ejecutable por humanos, con comandos reales disponibles en el repo actual. No crea todavía templates versionados, bootstrap automático ni quality gate de onboarding; esas capacidades corresponden a POST-H-024-B, POST-H-024-C, POST-H-024-D y POST-H-024-E.

## 2. Reglas no negociables del operador

```text
local_first=true
dry_run=true por defecto
no_remote_execution_enabled=true
no_external_apis_used=true
no_connector_write_enabled=true
no_plugin_execution_enabled=true
no_secrets_in_templates=true
no_magic_code_generation=true
human_approval_required_for_destructive_actions=true
```

Interpretación:

```text
DevPilot guía y valida el SDLC, pero no reemplaza la ingeniería.
Un PASS documental no autoriza código productivo sin revisión.
Un dry-run no debe mutar archivos fuente.
Un agente puede recomendar, pero los gates determinísticos deciden PASS/BLOCK.
```

## 3. Modelo mental: idea → workspace → docs → readiness → backlog

```text
Idea inicial
  ↓
Workspace local DevPilot
  ↓
Documentos de producto y pre-code
  ↓
Validación de frontmatter y artefactos
  ↓
MIASI requerido para proyectos agent-assisted
  ↓
Readiness estricto
  ↓
Backlog ejecutable
  ↓
Código, review, tests y release dry-run
```

El operador debe mantener esta secuencia. Saltar directamente de idea a código es un criterio BLOCK cuando el proyecto pretende operar con nivel profesional.

## 4. Flujo operativo mínimo

### 4.1. Capturar idea inicial

El operador debe registrar una idea en lenguaje de negocio, no una orden de implementación.

Ejemplo piloto usado por el backlog POST-H-024:

```text
Sistema agent-assisted de ventas e inventario para microemprendimientos locales
```

Checklist de calidad de la idea:

```text
[ ] Problema de negocio identificable.
[ ] Usuario objetivo explícito.
[ ] Resultado esperado verificable.
[ ] Restricciones locales, de privacidad y costo anotadas.
[ ] No requiere APIs externas como dependencia base.
[ ] No requiere secretos reales para iniciar.
```

### 4.2. Inicializar o revisar workspace

Comandos reales disponibles hoy:

```powershell
python -m devpilot_core workspace status --json
python -m devpilot_core workspace init --project-id ventas-micro-local --project-name "Sistema agent-assisted de ventas e inventario para microemprendimientos locales" --project-type agent-assisted-sdlc --dry-run --json
python -m devpilot_core workspace init --project-id ventas-micro-local --project-name "Sistema agent-assisted de ventas e inventario para microemprendimientos locales" --project-type agent-assisted-sdlc --execute --json
python -m devpilot_core workspace registry-validate --json
python -m devpilot_core workspace isolation-check --json
```

Regla de uso:

```text
Primero workspace status.
Luego init --dry-run.
Solo después, y con intención explícita, init --execute.
Nunca usar rutas fuera del workspace raíz validado.
```

### 4.3. Construir documentación pre-code

Hasta POST-H-024-B, las plantillas formales aún no existen. En POST-H-024-A el operador debe usar las rutas documentales canónicas existentes del repo como referencia:

```text
docs/00_product/
docs/01_requirements/
docs/02_architecture/
docs/03_security/
docs/04_quality/
docs/06_miasi/
docs/backlogs/
```

Documentos mínimos esperados para un nuevo proyecto:

```text
product_vision.md
mvp_scope.md
requirements_specification.md
architecture_document.md
security_threat_model.md
test_strategy.md
miasi_agent_registry.json
miasi_tool_registry.json
miasi_policy_matrix.json
backlog inicial
```

### 4.4. Validar documentos y readiness

Comandos reales disponibles hoy:

```powershell
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json
python -m devpilot_core validate-artifact docs/00_product/product_vision.md --strict --json
python -m devpilot_core checklist-pre-code --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core standards status --json
python -m devpilot_core miasi-required --json
python -m devpilot_core miasi validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
```

Interpretación:

```text
frontmatter PASS = metadatos mínimos consistentes.
artifact PASS = estructura documental compatible.
checklist PASS = pre-code gate cubierto.
readiness strict PASS = autorización para avanzar a implementación gobernada.
MIASI PASS = registries y policy matrix coherentes para proyecto agent-assisted.
```

### 4.5. Crear backlog ejecutable

Un backlog nuevo debe incluir:

```text
objetivo;
contexto;
alcance incluido/excluido;
fuentes obligatorias;
entregables;
modelo de datos si aplica;
principios;
micro-sprints;
comandos esperados;
criterios PASS/BLOCK;
riesgos;
definition of done.
```

Para proyectos agent-assisted, el backlog debe declarar:

```text
local_first=true
dry_run=true
no_remote_execution_enabled=true
no_external_apis_used=true
no_connector_write_enabled=true
no_plugin_execution_enabled=true
```

## 5. Ejemplo guiado: ventas e inventario para microemprendimientos

### Idea

```text
Sistema agent-assisted de ventas e inventario para microemprendimientos locales.
```

### Conversión a producto

```text
Usuario objetivo: microemprendedor local que necesita registrar productos, ventas, inventario y reportes básicos.
Problema: control manual disperso en cuadernos, hojas de cálculo o mensajes.
Valor: trazabilidad local, bajo costo, reportes simples y asistencia para decisiones operativas.
Restricción: debe funcionar primero local-first y sin API externa obligatoria.
```

### Pre-code mínimo

```text
product_vision.md: visión, usuarios, propuesta de valor, restricciones.
mvp_scope.md: alcance MVP, fuera de alcance y criterios de éxito.
requirements_specification.md: casos de uso, reglas de negocio, datos y validaciones.
architecture_document.md: arquitectura local, módulos, persistencia, boundaries.
security_threat_model.md: datos sensibles, amenazas, controles y no-go gates.
test_strategy.md: pruebas unitarias, integración, E2E local, fixture de datos.
MIASI registries: agentes, herramientas y políticas del proyecto.
backlog inicial: micro-sprints pequeños y verificables.
```

### Comandos de verificación inicial

```powershell
python -m devpilot_core workspace status --json
python -m devpilot_core miasi-required --json
python -m devpilot_core standards status --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## 6. Errores frecuentes

| Error | Riesgo | Corrección |
|---|---|---|
| Empezar por código | Requerimientos ambiguos y regresiones | Completar pre-code y readiness. |
| Usar agentes como autoridad final | Pérdida de control | Agentes recomiendan; gates deciden. |
| Ejecutar sin dry-run | Mutaciones no revisadas | Dry-run primero, execute solo con intención explícita. |
| Mezclar outputs con repo fuente | ZIP sucio y evidencia no reproducible | Mantener outputs fuera de entregables versionados. |
| Poner secretos en templates | Riesgo de fuga | Usar placeholders y SecretGuard; nunca valores reales. |
| Declarar production-ready antes de gates | Sobreclaim de madurez | Usar estados implemented-initial/preliminary. |
| Habilitar red o APIs externas por defecto | Riesgo de costo/privacidad | Local-first y mock/local por defecto. |

## 7. Criterios PASS

```text
PASS si el operador puede iniciar desde una idea sin depender de memoria conversacional.
PASS si el flujo idea → workspace → docs → readiness → backlog está documentado.
PASS si el playbook usa comandos reales del repo actual.
PASS si las reglas local-first, dry-run y no-remote están explícitas.
PASS si distingue claramente entre guía humana actual y automatización futura.
PASS si el ejemplo de ventas/inventario es suficiente para replicar el flujo.
```

## 8. Criterios BLOCK

```text
BLOCK si el operador necesita instrucciones no documentadas.
BLOCK si el playbook sugiere comandos que no existen actualmente sin marcarlos como futuros.
BLOCK si se habilita red, APIs externas, connector write, plugin execution o remote execution.
BLOCK si se sugiere crear secretos reales o credenciales en plantillas.
BLOCK si se declara production-ready-local por el solo hecho de tener playbook.
BLOCK si se omiten MIASI, readiness o validación documental en proyectos agent-assisted.
```

## 9. Límites explícitos de POST-H-024-A

POST-H-024-A es una primera versión operacional. Quedan pendientes:

```text
POST-H-024-B: templates Markdown/JSON versionados.
POST-H-024-C: workflow bootstrap dry-run/execute seguro.
POST-H-024-D: readiness preview y validación de onboarding.
POST-H-024-E: fixture piloto, quality gate y cierre del hito.
```

Hasta que esos micro-sprints estén implementados, este playbook es guía aprobada para operador, no automatización completa de bootstrap.

## 10. Bitácora recomendada de operador

```text
Fecha:
Proyecto:
Idea inicial:
Workspace:
Documentos creados:
Comandos ejecutados:
Resultado PASS/BLOCK:
Errores:
Solución:
Riesgos abiertos:
Próximo paso:
```
