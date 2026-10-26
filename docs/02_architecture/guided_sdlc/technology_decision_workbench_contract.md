---
doc_id: MP132-R03-04-TECH-DECISION-WORKBENCH-CONTRACT
title: R03-04 Technology Decision y ADR companion con autoría Ollama local
status: ACTIVE_FOR_R03_04
version: 1.0.1
owner: Owner DevPilot
source_baseline: df6a5dcbb6eeb112008db1373d2e975cbc60b18f
execution_authority: R03_04_OWNER_APPROVED_2026_10_24
---

# Technology Decision Workbench — R03-04

## Objetivo y autoridad

Extender el DRAFT Architecture de R03-03 con análisis y **autoría asistida real** de decisiones técnicas. Reutiliza PreCode, Quality Gate A188/A190 y el approval ya existente de Architecture. Una tarjeta ADR no es permiso, instalación ni archivo fuente; el estado de la UI es una proyección del servidor. La generación de candidatos **no modifica** el workspace Pilot B; una materialización posterior requiere approval real y Writer gobernado.

## Contrato mínimo verificable

1. Leer la sección `## Tecnología y alternativas` (o `## Tecnología` heredada) y `## ADRs materiales` (o `## ADRs`). Presentar motivación, alternativa, trade-off, costo, soporte y seguridad cuando existan; valores no medidos=`NOT_AVAILABLE`.
2. Una ADR material estructurada usa `### ADR-NNN — Título` y Contexto, Decisión, Alternativas, Consecuencias. El identificador, contenido y SHA lógico son **propuesta trazable**, no escritura standalone. No exigir ADR cosméticas. PESP puede hacerla `NOT_APPLICABLE` si existe una razón material.
3. Propuesta sin comparación sustentada o ADR no estructurada = `REVIEW_REQUIRED`; auto-provisionamiento explícito sin aprobación, afirmación de aprobación tecnológica sin prueba y ADR material declarada pero incompleta = `BLOCK`. La evaluación por patrones no acredita semántica profesional; Owner revisa decisiones significativas.
4. Solo `FROZEN` con `approval_id` y verificación exacta de los bytes aprobados de Architecture permite `APPROVED_WITH_ARCHITECTURE`. Una petición de approval pendiente, `plan_id`, texto `approved` o una fuente falsificada **no** acreditan ese estado.
5. La proyección no llama LLM, no escribe source, no instala dependencias, no crea otro approval, no modifica Source Registry del proyecto, no hace egreso externo. El compañero ADR standalone y sucesores posteriores conservan el lifecycle/PolicyEngine existente y se tratan según su sprint propietario; no se simula que una propuesta DRAFT ya fue materializada.
6. Revisar la UI en Guided y Expert, preservar el formulario normal de revisión/edición y verificar las diferencias de contenido Git sin aplicar falsa desigualdad LF/CRLF. No alteración de evidencia previa, pre-code FROZEN ni recibos C09.

## Evidencia y límites

`tests/test_mp132_r03_04_technology.py` conserva los escenarios del checkpoint read-only C00. Su validación **no equivale al cierre de C02**: C02 necesita `tests/test_mp132_r03_04_local_authoring.py`, recorridos reales con Ollama en Windows, selección material Owner, revisión Architecture sucesora y materialización companion aprobada. No se fuerza aprobación ficticia ni éxito por simple presencia de tarjetas.

## Ampliación Owner C02: autoría L y documento companion (autoridad vigente)

La proyección read-only de C00 se conserva como diagnóstico, pero no satisface por sí sola R03_04. La acción protegida `POST /api/v1/guided-sdlc/pre-code/technology-action` recibe solamente `generate_options`, `select_option`, `generate_adr` y `reconcile`. Los llamados al LLM usan únicamente proveedor `ollama` local habilitado y endpoint loopback; no hay API E, RAG, agentes, red externa, estimación USD inventada, stack elegido por defecto ni instalación.

Technology Options produce 2–3 opciones con drivers explícitos, costo/licencias, soporte, seguridad, operación, riesgos y una recomendación **no vinculante**. El Owner selecciona T1..T3; una ADR material es generada separadamente para esa elección. Salidas candidatas inmutables `cand-<sha256>.md` y puntero durable `status=IN_PROGRESS|COMPLETE|BLOCK`; reentrada COMPLETE reutiliza; error no reintenta automáticamente y requiere acción sucesora explícita. Las salidas son borradores, no calidad semántica garantizada.

La conciliación guarda DRAFT Architecture sucesor y liga hash de los dos candidatos con la selección; invalida el review/plan previo, aun en `APPROVAL_REQUIRED` no aprobado. El lifecycle normal de Architecture conserva revisión, control de calidad y approval. Tras Architecture FROZEN verificada, el servicio de ADR companion crea un plan **único y atómico** con exactamente dos destinos: `docs/02_architecture/technology_options.md` y `docs/02_architecture/adrs/ADR-001-<slug>.md`. La aplicación requiere approval exacto y PolicyEngine existente; ni previews ni igualdad de contenido implican aprobación.

El proyecto no cambia de repositorio ni se tocan upstream FROZEN; segundo dominio evita especialización Pilot B. Validación C02 incluye pruebas focales reales en Windows y verificación de capturas Guided/Expert. Los controles heredados de C00 permanecen como diagnóstico y no forman un segundo publisher.

## R03_04_C02_P2 — ruta real de autoría local

La ruta `POST /api/v1/guided-sdlc/pre-code/technology-action` pertenece a los contratos API, RBAC servidor y OpenAPI además del dispatcher y el router FastAPI. Su autorización es `owner` con sesión humana y alcance del workspace activo; token legado, roles ajenos y rutas desconocidas siguen denegados. El endpoint solo escribe estado runtime de candidatas locales o elección/reconciliación de DRAFT, no archivos del proyecto ni instalaciones. La escritura de Technology Options/ADR en el workspace mantiene la operación de materialización gobernada existente. Prueba focal: `tests/test_mp132_r03_04_c02_rbac.py`. El correctivo P2 surge del bloqueo real HTTP 403/RBAC_UNKNOWN_ROUTE_DENY del 25-10-2026; no concede excepciones ni omite controles.

## R03_04_C02_P3 — evidencia acotada para inferencia local

El rechazo P2 HTTP 409 `R0304_CONTEXT_TOO_LARGE_REQUIRES_RECONCILIATION` fue
provocado por concatenar cuatro documentos completos antes de llamar a Ollama.
El contrato P3 no modifica ni reduce los documentos Architecture DRAFT,
Vision/Scope/Requirements FROZEN ni las candidatas persistidas. Para cada
solicitud Technology Options se prepara exclusivamente un **contexto para el
modelo**, escogiendo cláusulas completas, semánticamente relevantes, de
Architecture + las tres fuentes FROZEN. Cada fuente conserva su SHA-256 íntegro,
cantidad de cláusulas elegidas y omitidas, y advertencia expresa de cobertura
parcial. La selección es determinística, no adjudica calidad ni completitud.

La generación ADR acota de la misma forma Architecture y Technology Options y
favorece la opción seleccionada por Owner. Nunca genera una decisión para el
Owner. `prompt_sha256`, perfil de selección y hashes íntegros quedan vinculados
al intento de inferencia, así un nuevo contexto no reutiliza por accidente la
candidata anterior. Ningún archivo fuente es editado al preparar el contexto.

Los límites de prompt son 13000 caracteres (Technology) y 12500 (ADR), en
consonancia con la interfaz de Ollama existente y su `num_predict` máximo 512.
Un extracto demasiado pobre o no divisible es BLOCK explícito, nunca falsa
certificación. El Owner debe comprobar en UI que las opciones/ADR generadas
respetan todo el texto original FROZEN, incluso cláusulas omitidas del prompt.
El contrato de revisión/approval/materialización no cambia. Pruebas focales:
`tests/test_mp132_r03_04_context_pack.py` y la batería local C02 existente.
R03_04_UX_01 permanece fuera de este correctivo, pendiente del cierre funcional.

## R03_04_C02_P4 — disponibilidad local y selección visible de modelo

R03_03 permitió explícitamente autoría LOCAL_MODEL con el ejemplo seguro de
Ollama cuya configuración inicial lleva `enabled: false`. C02_P3, sin embargo,
rechazó HTTP 409 `R0304_OLLAMA_LOCAL_ENABLED_REQUIRED`. P4 armoniza el
comportamiento **solamente** para la ruta pre-code autenticada y autorizada a
Owner, sin habilitar al proveedor globalmente ni permitir egreso externo. Si
existe configuración local explícita `.devpilot/providers.yaml` con Ollama
deshabilitado, se respeta como política superior sin sobrescribirla.

Antes de reservar un intento de generación se verifica endpoint localhost,
disponibilidad Ollama y modelo solicitado. Si una lista de modelos está
truncada, no se concluye falsamente que el modelo falta. Un BLOCK en esta
preparación no deja pointer IN_PROGRESS, no consume intento y no justifica
sucesora. Los pointers P3 conservan su identidad histórica; las nuevas
solicitudes llevan `profile_version=2.2.0` para evitar colisiones.

La UI expone claramente proveedor Ollama y el modelo heredado de Architecture;
se permite escoger otro nombre de modelo local instalado. Technology y ADR
mantienen la selección visible, revisión Owner y materialización gobernada.
No hay instalación ni modificación automática del catálogo del proveedor.
El modelo nuevo debe estar instalado y seleccionado por el Owner; un error de
modelo no instalado se informa antes de consumir una inferencia.

P4 incluye build UI y pruebas focales de seguridad local, modelo, contexto,
estado persistente y ausencia de falsos reintentos. No ejecutar full regression.
R03_04_UX_01 permanece pendiente de cierre funcional de R03_04.

## R03_04_C02_P5 — autorización local expresa y cadena funcional

P4 mostró `R0304_OLLAMA_EXPLICITLY_DISABLED` tras pulsar el Owner el botón
de generación, aunque R03_03 Architecture aceptó una acción Owner equivalente
con `enabled: false`. El setting `enabled` mantiene su fuerza para rutas
automáticas o no autenticadas; **solo** el servicio pre-code que ha validado
identidad Owner, alcance de workspace, etapa Architecture LOCAL_MODEL y DRAFT
puede pasar `explicit_owner_action=True` a la autoría de Technology o ADR.
Esto no cambia `.devpilot/providers.yaml`, no habilita Ollama globalmente,
no altera otras rutas y nunca habilita API externa: se conserva endpoint
loopback, salud, modelo instalado y límites previos a inferencia.

La acción debe registrar su resultado en un candidato inmutable y nunca
materializar archivos del proyecto sin el plan/approval posterior. La ruta
secuencia Technology -> elección Tn Owner -> ADR -> reconciliación DRAFT
se ensaya como smoke focal con respuestas controladas y se ejecuta con
Ollama real una sola vez en UI Windows. RBAC no Owner, estados P1-P4,
reintentos inciertos, SHA lógicos y fuentes FROZEN se conservan.

No se modifica UI ni se exige otro build: P4 lo dejó PASS (77 módulos).
Los tests P5 cubren la barrera Owner y las cuatro acciones funcionales;
la calidad de un resultado real del modelo sigue siendo revisión humana,
no se confunde HTTP PASS con calidad semántica. Sin full regression.


## R03_04_C02_P6 — Reviewer quality gate

P5 devolvió HTTP 200 pero generó una recomendación terminada a mitad
de oración. COMPLETE solo acredita el recibo técnico, no el mérito
profesional. El Owner rechaza las alternativas del caso por
desproporción frente a un negocio unipersonal local-first.

La nueva autoría v3 conserva el candidato v2 sin borrarlo, invalida su
selección y exige alternativa sucesora explícita. Valida la estructura,
recomendación identificada y oración completa; la idoneidad arquitectónica
requiere todavía contrastar literalmente las fuentes FROZEN.

Presupuesto sincronizado: 768 tokens, Ollama 380 s, UI 450 s y reserva
IN_PROGRESS 490 s. Si Ollama señala stop_reason length, se bloquea sin
fabricar una conclusión. La política mantiene selección Owner,
approval gobernado, no instalación automática y solo loopback.
Python es una posibilidad pertinente, no un mandato universal.
Las preferencias de UX completas siguen en R03_04_UX_01.

## R03_04_C02_P7 — revisión Owner explícita del candidato (25-10-2026)

Tras P6, el generador local acreditó inferencia real, pero la revisión Owner
identificó deriva de alcance y alternativas desproporcionadas. Se incorporan
dos acciones Owner gobernadas sobre el mismo endpoint: `owner_revise_options`
y `owner_revise_adr`. Solo un Owner autenticado con ámbito al workspace
puede guardar contenido Markdown completo como candidato sucesor inmutable.
La acción exige un candidato preexistente ya generado, verifica su SHA en
archivo y estructura de la revisión, conserva `revision_of_sha256`,
`created_by`, `origin=OWNER_REVISION` y no invoca LLM ni toca documentos
gestionados. Cambiar Options invalida selección, ADR y reconciliación; cambiar
ADR invalida la reconciliación. La elección Owner sigue explícita y el
approval/freeze/materialización sigue siendo obligatorio.

Corrección visual focal: progreso con aria-live situado antes de resultados,
documentos Markdown que respetan ancho de panel y `textarea` revisable.
Una revisión Owner no certifica por sí misma calidad semántica ni aprobación.
El sprint queda OPEN hasta validación Windows completa.
