---
doc_id: MP132-R03_05_CONDITIONAL_TECH_ARTIFACTS-SPRINT
status: DRAFT_EXECUTION_GATED
version: 1.0.0
owner: Owner DevPilot
planning_authority: MP132-A188 + R02-M2-CLOSEOUT-189
execution_authority: false
baseline_reference: 1f15fa5b770db37c684e870a49572dcb569bd3a4
owner_increment_approval: PENDING
---
# R03_05_CONDITIONAL_TECH_ARTIFACTS — Catálogo condicional de datos, API, UX e interfaces

## A. Resultado y responsable
**IDs propietarios:** MP132-R3-07 (completion). El sprint cierra una unidad **verificable**, no reabre R02 ni desplaza otros backlogs.

## B. Precondiciones y audit-first
- R03_04 CLOSED/PASS or PASS_WITH_FINDINGS + new Git HEAD. Antes de ejecutar: obtener HEAD y diff reales de Windows; releer contratos y archivos afectados en repo y Project runtime. Rebind sprint/prompt al HEAD vigente; probar compatibilidad con A187/A188.
- Repo DevPilot `evolution/multiprovider-v2`; mismo Pilot B FROZEN, `operator_project_writes=0`, tres consolas foreground únicamente para validación de UI.
- **Estado DRAFT**, sin permiso de escribir source o instalar dependencias hasta autorización explícita individual del Owner de este sprint y prompt.

## C. Scope acotado
PESP activa contratos de dominio, datos, integración/API y UX según hechos y riesgos; elegibilidad REQUIRED/CONDITIONAL/RECOMMENDED/NOT_APPLICABLE, rutas de import/edit desde UI.

## D. Artefactos y áreas candidatas
catalog/coverage, template profiles, UI/read-only, tests. El implementador debe identificar los paths exactos después del audit-first; este plan **no** declara allowlist ficticia ni dependencias instaladas.

## E. Escenarios/criterios de aceptación
Cobertura por proyecto y segundo dominio; N/A rationale y contradicción de riesgo se clasifican proporcionalmente; sin documentos de relleno.

## F. Control de impacto y seguridad
- sin obligar especificaciones técnicas a todos los proyectos.
- Reutilizar componentes reales; no crear segundo publisher, approval o source registry. Modo dry-run inicial; autorización solo para cambios materiales, red/costos y efectos reales.
- Semántica L local competente y supervisada; mock/fixtures sólo para negativos; API E, agentes mutativos y egress externo deshabilitados.
- Fuente upstream con hash y `profile_version` en las propuestas; no usar identificador literal Pilot B para decidir validez global.

## G. Evidencia, gates y checkpoint
- pytest focal + negativos pertinentes, Vite build cuando cambie UI; prueba manual por Guided/Expert **solo si cambia la superficie**, mínimo 1 captura por estado relevante, observación Owner sin burocracia.
- Comparar contenido Git normalizado (`git diff --check`), no bloqueos por LF/CRLF; manifest de before/after, incidentes y resolución, estados persistidos.
- Una única guía `.md`, comandos PowerShell **de una línea** con PASS/BLOCK; operador Python mínimo con verify/apply/test/collect/package, nunca `git add -A`, `reset --hard`, `clean`, ni full regression salvo riesgo autorizado.
- Commit selectivo y push normal autorizado; `git archive HEAD` como baseline, SHA-256, CRC y README breve; artefactos de validación empaquetados aunque se produzca BLOCK.
- `CLOSED` sólo con Windows/gate, evidence, Git/baseline y ratificación técnica. Si `BLOCK`: diagnosticar una vez, parche focal, preservar estados; nunca aprobar por recuento bruto de tests.

## H. Fuera de alcance
No avanzar a la siguiente unidad ni ola automáticamente; no ejecutar R04 ni liberar API E o publicar software del Pilot B por cuenta de este sprint.
