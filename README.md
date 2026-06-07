# DevPilot Local — Agent-assisted SDLC personal

Estado actual: `baseline pre-code approved + functional backlog approved + gates documentales ejecutables`  
Último hito: `FUNC-SPRINT-05 — Checklist pre-code y readiness estricto`  
Siguiente hito: `FUNC-SPRINT-06 — Reportes Markdown/JSON formales y evidencia de gates`  
Estándar rector: MIPSoftware  
Extensión inteligente: MIASI  
Modo de trabajo: local-first híbrido, API keys opcionales, costo externo controlado, dry-run por defecto.

## Propósito

DevPilot Local será una plataforma personal de ingeniería de software asistida por agentes para gestionar el ciclo de vida completo de creación de aplicaciones: idea, producto, requerimientos, arquitectura, seguridad, calidad, operación, implementación, revisión, trazabilidad, Git, patches, refactor seguro, modelos locales/API opcionales y evolución.

El primer ciclo funcional no busca construir todavía todos los agentes ni una interfaz completa. Su objetivo es convertir la baseline documental aprobada en validadores ejecutables, reportes, trazas, políticas y contratos técnicos que hagan que MIPSoftware y MIASI funcionen como gates reales dentro del repositorio.

## Estado de implementación

Ya existe:

- estructura base Python;
- CLI bootstrap;
- contrato común `CommandResult`, `Finding`, `Severity` y `ExitCode`;
- comando `readiness-check` compatible y comando `readiness-check --strict`;
- comando `miasi-required`;
- comando `validate-frontmatter`;
- comando `validate-artifact`;
- comando `standards status`;
- comando `checklist-pre-code`;
- parser de checklist Markdown pre-code;
- generación local de evidencia `outputs/reports/readiness_check.json` y `outputs/reports/readiness_check.md`;
- documentación pre-code aprobada;
- estándares MIPSoftware y MIASI versionados dentro de `docs/standards/`;
- backlog funcional aprobado en `docs/functional_backlog_after_precode.md`.

Pendiente de implementación funcional:

- reportes Markdown/JSON formales por gate;
- trazas JSONL;
- workspace manager;
- policy/security guards;
- persistencia SQLite;
- registries ejecutables de agentes y herramientas;
- agentes documentales controlados;
- Git read-only;
- patch/code review en dry-run;
- ModelAdapter híbrido.

## Regla de documentación viva

La carpeta `docs/` es el contrato de ingeniería vivo del proyecto. Puede ajustarse durante la implementación, pero todo cambio debe quedar justificado, versionado y trazado. Si un cambio altera requerimientos, arquitectura, seguridad, agentes, herramientas, costos, persistencia o APIs, debe actualizar los documentos y ADRs correspondientes.

## Estructura

```text
DevPilot_Local/
  docs/
    00_product/
    01_requirements/
    02_architecture/
    03_security/
    04_quality/
    05_operations/
    06_miasi/
    audits/
    checklists/
    reference/
    standards/
  src/devpilot_core/
    standards/
    validators/
  tests/
  outputs/
  scripts/
```

## Instalación local

```powershell
cd D:\Projects\DevPilot_Local
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Si se ejecuta sin instalación editable, usar:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q
```

## Comandos operativos principales

```powershell
python -m pytest -q
python -m devpilot_core --version
python -m devpilot_core readiness-check
python -m devpilot_core readiness-check --json
python -m devpilot_core readiness-check --strict
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi-required
python -m devpilot_core miasi-required --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --strict
python -m devpilot_core standards status
python -m devpilot_core standards status --json
python -m devpilot_core checklist-pre-code
python -m devpilot_core checklist-pre-code --json
```

## Interpretación de exit codes

```text
0 = PASS
1 = FAIL
2 = BLOCK
3 = ERROR
```

## Evidencia generada

`readiness-check --strict` genera evidencia local en:

```text
outputs/reports/readiness_check.json
outputs/reports/readiness_check.md
```

Estos archivos son artefactos runtime y están ignorados por `.gitignore`; pueden conservarse localmente como evidencia de ejecución o regenerarse en cualquier momento.

## Higiene local del repositorio

Para revisar artefactos generados antes de un commit:

```powershell
python scripts\func_sprint_00_cleanup.py
```

Para eliminarlos de forma explícita:

```powershell
python scripts\func_sprint_00_cleanup.py --execute
```

El script trabaja en modo dry-run por defecto para evitar eliminaciones accidentales.

## FUNC-SPRINT-01 — CLI core y contrato común de resultados

Este sprint introduce la arquitectura mínima interna del CLI: modelos comunes de resultado, hallazgos, severidades y códigos de salida. El objetivo es que los comandos actuales y futuros de DevPilot no devuelvan respuestas improvisadas, sino un contrato consistente que pueda imprimirse para humanos o serializarse como JSON.

Códigos de salida definidos:

```text
0 = PASS
1 = FAIL
2 = BLOCK
3 = ERROR
```

## FUNC-SPRINT-02 — Validador de frontmatter

FUNC-SPRINT-02 incorpora el primer validador documental real de DevPilot. El comando `validate-frontmatter` valida que un documento Markdown tenga frontmatter, campos mínimos, estado permitido, versión SemVer-like y fecha `updated` en formato `YYYY-MM-DD`.

Criterios rápidos:

```text
PASS: documento con frontmatter completo y válido.
FAIL: documento sin frontmatter, sin campo obligatorio o con status inválido.
STRICT: un documento approved sin campo approval falla.
```

## FUNC-SPRINT-03 — Validación de artefactos MIPSoftware/MIASI

El comando `validate-artifact` valida que un documento Markdown no solo tenga frontmatter, sino también estructura mínima según su perfil documental. El validador es determinístico, local-first y no usa LLMs ni APIs externas.

Interpretación de resultados:

```text
PASS: el documento tiene frontmatter válido, H1 único y secciones mínimas del perfil.
FAIL: el documento no aprobado incumple estructura mínima.
BLOCK: un documento aprobado incumple estructura mínima y debe corregirse antes de continuar.
ERROR: archivo inexistente, ruta inválida o archivo no Markdown.
```

## FUNC-SPRINT-04 — Standards Registry y carga local de reglas

Este sprint agrega el primer registro local de estándares de DevPilot. El objetivo es que la aplicación pueda detectar y reportar la presencia de MIPSoftware y MIASI dentro de `docs/standards`, listar artefactos obligatorios del proyecto y exponer los perfiles de validación disponibles.

Comandos principales:

```powershell
python -m devpilot_core standards status
python -m devpilot_core standards status --json
```

El comando no modifica archivos, no llama servicios externos y no requiere API keys. Su salida JSON usa el contrato común `CommandResult`.

## FUNC-SPRINT-05 — Checklist pre-code y readiness estricto

Este sprint convierte el checklist pre-code y el readiness documental en gates ejecutables.

Componentes principales:

- `src/devpilot_core/validators/checklist.py`: parser y validador del checklist Markdown.
- `src/devpilot_core/validators/readiness.py`: composición del gate estricto.
- `checklist-pre-code`: evalúa filas obligatorias del checklist, artefactos, estado PASS y status `approved`.
- `readiness-check --strict`: valida existencia, frontmatter, estado aprobado, estructura mínima, MIASI, Standards Registry y checklist.
- `outputs/reports/readiness_check.json` y `.md`: evidencia generada localmente.

Criterios rápidos:

```text
PASS: todos los artefactos obligatorios existen, están approved y pasan validadores mínimos.
BLOCK: falta un artefacto obligatorio, falta MIASI, falla el checklist o un documento aprobado incumple estructura mínima.
WARNING: brechas recomendadas no bloqueantes; deben atenderse en endurecimiento posterior.
```

Resultado esperado actual:

```text
pytest -q -> 30 passed
checklist-pre-code -> PASS
readiness-check --strict -> PASS con warnings no bloqueantes
```
