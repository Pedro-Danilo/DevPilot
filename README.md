# DevPilot Local — Agent-assisted SDLC personal

Estado actual: `baseline pre-code approved + functional backlog approved`  
Último hito: `FUNC-SPRINT-00 — Higiene del repo y sincronización de baseline`  
Siguiente hito: `FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados`  
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

- validadores estrictos de frontmatter;
- validadores de artefactos MIPSoftware/MIASI;
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
FUNC-SPRINT-01 — Arquitectura interna del CLI y modelo común de resultados
```

Este sprint debe crear la base común para comandos, resultados, errores, exit codes, serialización y pruebas del CLI.

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
