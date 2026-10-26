---
doc_id: MP132-R03_04_TECH_DECISION_ADR-SPRINT
status: SPRINT_EXECUTION_APPROVED
version: 1.0.2
owner: Owner DevPilot
planning_authority: MP132-A188 + R02-M2-CLOSEOUT-189
execution_authority: true
baseline_reference: df6a5dcbb6eeb112008db1373d2e975cbc60b18f
owner_increment_approval: APPROVED_2026_10_24
---
# R03_04_TECH_DECISION_ADR — Selección tecnológica y ADR companion

## A. Resultado y responsable
**IDs propietarios:** MP131-R3-03; MP132-R3-10 (decision source). El sprint cierra una unidad **verificable**, no reabre R02 ni desplaza otros backlogs.

## B. Precondiciones y audit-first
- R03_03 CLOSED/PASS or PASS_WITH_FINDINGS + new Git HEAD. Antes de ejecutar: obtener HEAD y diff reales de Windows; releer contratos y archivos afectados en repo y Project runtime. Rebind sprint/prompt al HEAD vigente; probar compatibilidad con A187/A188.
- Repo DevPilot `evolution/multiprovider-v2`; mismo Pilot B FROZEN, `operator_project_writes=0`, tres consolas foreground únicamente para validación de UI.
- **Aprobación individual Owner 2026-10-24:** R03_04 y su prompt autorizados exclusivamente sobre el baseline C11 autenticado. No autoriza instalar dependencias, publicar/aplicar Pilot B ni ejecutar R03_05.

## C. Scope acotado
Technology Decision Workbench en Architecture; tradeoffs justificadas, costo/soporte/seguridad, ADR gobernada cuando es material. Decisión Owner central consolidada en approval Architecture.

## D. Artefactos y áreas candidatas
architecture workbench/ADR service/UI, tests, ADR si cambia arquitectura. El implementador debe identificar los paths exactos después del audit-first; este plan **no** declara allowlist ficticia ni dependencias instaladas.

## E. Escenarios/criterios de aceptación
UI muestra alternativas y rationale, fallo si instala stack al decidir, no ADR trivial, ADR approved lineage y rechazo de decisiones no grounded.

## F. Control de impacto y seguridad
- no auto-install, no stack predeterminado ni Owner approval cosmético.
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

## I. Rebind a R03_03 CLOSED y ajuste por evidencia A190/C11

- C11 confirmó `df6a5dcbb6eeb112008db1373d2e975cbc60b18f` en Windows/Git local/remoto. ZIP baseline `repo_DevPilot_Local_R03_03_ARCHITECTURE_AUTHORING_df6a5dcbb6ee_WINDOWS_VALIDATED.zip`, SHA256 `0e2de50a23d88d6d404d2981cd54a8b8d11cc06eed4071d2c22575c3f077c524`, CRC PASS y 23 rutas Git verificadas. R03_03 cerrado **PASS_WITH_FINDINGS**: juicio semántico Pilot B `REVIEW_REQUIRED`, sin approval/apply/freeze del artefacto.
- REUSE: pre-code DRAFT/review/approval; Source Registry; proveedor L; perfil Architecture; ADR companion antiguo C02; UI Guided/Expert; Quality Gate A190. No crear otro almacén, publisher, approval ni llamada de inferencia.
- DELTA: evaluación de decisiones tecnológicas/ADRs en la candidata guardada; alternativa y justificación visible; línea de procedencia a FROZEN; negativos de auto-instalación y aprobación tecnológica inventada; propuesta de ADR material identificable. Si el DRAFT es prose no estructurada, `REVIEW_REQUIRED`, nunca calidad profesional ficticia.
- El approval **normal** de Architecture cubre las decisiones incluidas. Solo cuando Architecture sea realmente FROZEN y su fuente coincida con `approved_sha256` se podrá mostrar lineage `APPROVED_WITH_ARCHITECTURE`. La proyección de R03_04 es **read-only**: no materializa archivos standalone. El lifecycle/companion aplicado y sucesores quedan bajo sus fronteras gobernadas, especialmente R03_07; R03_04 no introduce otro requisito de autorización cosmética.
- PESP: ADR `NOT_APPLICABLE` con motivo en proyectos sin decisión material; de otro modo `REVIEW_REQUIRED`; dos dominios en focal. `BLOCK` solo por falta material explícita, autoprovionamiento/stack sin autorización o aprobación no fundada. No seleccionar motor concreto por catálogo global o product ID.
- Este sprint queda **IMPLEMENTATION_CANDIDATE**, no `CLOSED`, hasta focal Windows, UI manual, recibos, Git tres estados y baseline sucesor. La guía secuencial única es autoridad del operador.

## J. Ampliación Owner R03_04_C02 — prevalece sobre las restricciones read-only de I

- **Decisión Owner expresa 2026-10-25:** se aprueba `R03_04_C02_PROPOSAL.md`. C01 cerrado PASS; R03_04 permanece OPEN y su cierre requiere generar realmente Technology Options y una ADR material con Ollama local. Esta ampliación sustituye el límite diagnóstico de I, no las prohibiciones de instalaciones, API externa ni aprobaciones ficticias.
- Architecture DRAFT `LOCAL_MODEL`, Vision/Scope/Requirements FROZEN y hashes reales: generación de 2–3 opciones trazables con costo/licencias, soporte, seguridad, operación y riesgos. Un solo llamado Ollama por operación; recibos persistidos e inmutables, sin reintento automático. El Owner elige **una** opción sin redactarla manualmente. La ADR se genera con el modelo local para esa elección, con contexto, decisión, alternativas, consecuencias y mitigaciones.
- La acción explícita **conciliar** crea una revisión sucesora de Architecture DRAFT que incorpora la elección/ADR y SHA-256 de ambos candidatos; invalida el plan anterior de Architecture. No aprobar/apply/freeze el plan obsoleto. Los mismos controles de revisión/diff/approval/apply/freeze gobiernan esta revisión.
- Cuando Architecture sea FROZEN y su approval/bytes válidos, el servicio `ArchitectureAdrBundleService` extendido prepara un solo plan **multiarchivo** para `docs/02_architecture/technology_options.md` y `docs/02_architecture/adrs/ADR-001-*.md`: approval exacto, apply atómico e idempotencia con recibo. No crear otro escritor, approval tecnológico cosmético ni documentación de origen manual.
- UI Guided/Expert: tarjeta abatible con generación Technology, elección Owner, propuesta ADR y conciliación; distinguir candidatos no aprobados de documentos materializados, mensaje de progreso y botones anti-doble clic; avisos de revisión humana. Verificar cierre visual C01 heredado con dos vistas sin repetir las capturas previas.
- Focal: tests de adaptador Ollama simulado/no uso de E, persistencia e intento sucesor, vínculos de hash, API política/auth, materialización de dos docs y regresión C02 histórica, build UI, recorrido manual Pilot B y negativo de segundo dominio. Git tres estados/commit/push/baseline solo después de PASS Windows y decisión Owner efectiva sobre tecnología.
- R03_07 conserva el lifecycle de opciones/ADRs de evoluciones futuras. Su contrato se reconciliará en su propia ejecución; esta decisión aprobada asigna a R03_04 solo la generación inicial, selección y materialización companion de Architecture.
