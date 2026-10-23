---
doc_id: MP132-R03_02_TECH_CONTEXT_PROFILE-SPRINT
status: SPRINT_EXECUTION_APPROVED
version: 1.0.0
owner: Owner DevPilot
planning_authority: MP132-A188 + R02-M2-CLOSEOUT-189
execution_authority: true
baseline_reference: 9c51d987a6965822f1d171142e25a159a8bfbeb2
owner_increment_approval: APPROVED_2026_10_23
execution_state: WINDOWS_VALIDATION_PENDING
---
# R03_02_TECH_CONTEXT_PROFILE — ContextPack técnico y aplicabilidad

## A. Resultado y responsable
**IDs propietarios:** MP131-R3-01; MP132-R3-07 (profile base). El sprint cierra una unidad **verificable**, no reabre R02 ni desplaza otros backlogs.

## B. Precondiciones y audit-first
- R03_01 CLOSED/PASS or PASS_WITH_FINDINGS + new Git HEAD. Antes de ejecutar: obtener HEAD y diff reales de Windows; releer contratos y archivos afectados en repo y Project runtime. Rebind sprint/prompt al HEAD vigente; probar compatibilidad con A187/A188.
- Repo DevPilot `evolution/multiprovider-v2`; mismo Pilot B FROZEN, `operator_project_writes=0`, tres consolas foreground únicamente para validación de UI.
- **Owner aprobó individualmente R03-02 y su prompt el 2026-10-23.** Esta autorización alcanza únicamente el delta focal rebindeado a `9c51d987a6965822f1d171142e25a159a8bfbeb2`; cierre sigue sujeto a evidencia Windows.

## C. Scope acotado
TECHNICAL_RAG_SOURCE_PROFILE y resolver PESP de contexto: RF/Vision/Scope FROZEN, ADR vigentes, security risks, límites de memoria/contexto; ignore changelog superseded.

**Ajuste audit-first respecto de A189:** R03-01 cerró técnicamente con COR2+COR3, HEAD `9c51d987a696...` y auditoría 1.762 entradas sin hallazgos. R03-02 reutiliza `PreCodeWizard` para autorización FROZEN y `ArtifactProfileRegistry/ProjectApplicability` como PESP. Sólo agrega un resolver de contexto read-only, una policy versionada y recibo de proveniencia de Architecture, sin cambiar UI, sin decidir stack, sin solicitar nueva aprobación para controles mecánicos. ADR/security inputs siguen condicionales hasta que existan vigentes; `UNKNOWN` no se falsifica como N/A.

## D. Artefactos y áreas candidatas
RAG/context pack, profile registry, fixtures y pruebas. El implementador debe identificar los paths exactos después del audit-first; este plan **no** declara allowlist ficticia ni dependencias instaladas.

## E. Escenarios/criterios de aceptación
Pruebas contra referencias obsolete/poisoned, fuentes falsificadas, stage/hash drift, segunda industria y `NOT_APPLICABLE` sustentado; no API externa.

## F. Control de impacto y seguridad
- no inventar decisiones ni usar `project_id` como semántica.
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
