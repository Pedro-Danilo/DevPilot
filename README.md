# DevPilot Local — Agent-assisted SDLC personal

Estado actual: `baseline pre-code approved + functional backlog approved`  
Último hito: `FUNC-SPRINT-03 — Validador de artefactos MIPSoftware/MIASI`  
Siguiente hito: `FUNC-SPRINT-04 — Standards Registry y carga local de reglas`  
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
- comando `readiness-check`;
- comando `miasi-required`;
- prueba mínima con `pytest`;
- documentación pre-code aprobada;
- estándares MIPSoftware y MIASI versionados dentro de `docs/standards/`;
- backlog funcional aprobado en `docs/functional_backlog_after_precode.md`.

Pendiente de implementación funcional:

- validadores estrictos de frontmatter; **implementado en FUNC-SPRINT-02**
- validadores de artefactos MIPSoftware/MIASI; **implementado en FUNC-SPRINT-03**
- readiness estricto;
- reportes JSON/Markdown;
- trazas JSONL;
- workspace manager;
- policy/security guards;
- persistencia SQLite;
- registries ejecutables;
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
  tests/
  outputs/
  scripts/
```

## Primeros comandos

```powershell
cd D:\Projects\DevPilot_Local
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pytest -q
.\scripts\func_sprint_00_cleanup.ps1
python -m devpilot_core --version
python -m devpilot_core readiness-check
python -m devpilot_core miasi-required
```

## Siguiente sprint

```text
FUNC-SPRINT-03 — Validador de artefactos MIPSoftware/MIASI
```

Este sprint debe validar estructura mínima de documentos por perfil, reutilizando el contrato de resultados y el validador de frontmatter ya implementados.

## Higiene local del repositorio

Para revisar artefactos generados antes de un commit:

```powershell
.\scripts\func_sprint_00_cleanup.ps1
```

Para eliminarlos de forma explícita:

```powershell
.\scripts\func_sprint_00_cleanup.ps1 -Execute
```

El script trabaja en modo dry-run por defecto para evitar eliminaciones accidentales.


## FUNC-SPRINT-01 — CLI core y contrato común de resultados

Este sprint introduce la arquitectura mínima interna del CLI: modelos comunes de resultado, hallazgos, severidades y códigos de salida. El objetivo es que los comandos actuales y futuros de DevPilot no devuelvan respuestas improvisadas, sino un contrato consistente que pueda imprimirse para humanos o serializarse como JSON.

Comandos validados:

```powershell
python -m devpilot_core --version
python -m devpilot_core readiness-check
python -m devpilot_core readiness-check --json
python -m devpilot_core miasi-required
python -m devpilot_core miasi-required --json
python -m pytest -q
```

Códigos de salida definidos:

```text
0 = PASS
1 = FAIL
2 = BLOCK
3 = ERROR
```

Esta capa será la base para los próximos validadores de frontmatter, artefactos MIPSoftware/MIASI, readiness estricto, reportes y trazas.


## FUNC-SPRINT-02 — Validador de frontmatter

FUNC-SPRINT-02 incorpora el primer validador documental real de DevPilot. El comando `validate-frontmatter` valida que un documento Markdown tenga frontmatter, campos mínimos, estado permitido, versión SemVer-like y fecha `updated` en formato `YYYY-MM-DD`.

Comandos relevantes:

```powershell
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict
```

Criterios rápidos:

```text
PASS: documento con frontmatter completo y válido.
FAIL: documento sin frontmatter, sin campo obligatorio o con status inválido.
STRICT: un documento approved sin campo approval falla.
```


## FUNC-SPRINT-03 — Validación de artefactos MIPSoftware/MIASI

El comando `validate-artifact` valida que un documento Markdown no solo tenga frontmatter, sino también estructura mínima según su perfil documental.

Ejemplos:

```powershell
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md
python -m devpilot_core validate-artifact docs/06_miasi/agent_card.md --json
python -m devpilot_core validate-artifact docs/02_architecture/architecture_document.md --strict
```

Interpretación de resultados:

```text
exit_code 0: PASS.
exit_code 1: FAIL de validación.
exit_code 2: BLOCK. Se usa cuando un documento aprobado incumple estructura mínima.
exit_code 3: ERROR técnico, ruta inválida o archivo no soportado.
```

Este comando usa perfiles determinísticos ubicados en `src/devpilot_core/validators/artifact_profiles.py` y el validador en `src/devpilot_core/validators/artifact.py`. No usa LLMs, APIs externas ni dependencias nuevas.
