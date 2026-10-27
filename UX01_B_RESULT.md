# UX01-B — Resultado del candidato recuperado

Fecha: 2026-10-27 (America/Bogota).

**Estado vigente: correctivo técnico focal PASS, pendiente de revisión Owner.** Las secciones 1–9 conservan el cierre documental del candidato recuperado; la sección 10 registra el correctivo posterior y prevalece para los archivos, pruebas y estado actuales. Pruebas históricas: **132 PASS**; correctivo: **71 casos únicos PASS (18 nuevos)**. Cierre UX01-B: **PENDING_OWNER_REVIEW**. La utilidad de Ollama real y la aprobación profesional siguen pendientes.

## 1. Identidad y procedencia

- Worktree vigente: `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local`.
- Baseline UX01-A / HEAD: `09b07c8d5afab66eda9c2fad4c65e9686607f275`.
- Snapshot recuperado: `aff2dfd1c1e05ce3dc86c03d93858abe93d34723`, cuyo padre es exactamente el baseline.
- Referencia de conservación: `refs/codex/snapshots/d19574c9f6844a1fd4d102a424c99219f5e88cac`.
- Chat original archivado: «Implementar componente UX01-B», ID `01a17ccb-e86a-7e42-90ee-338ebdd63ae1`.
- Worktree original: `C:\Users\Pedro\.codex\worktrees\5c17\DevPilot_Local`; ya no existe. La continuidad utiliza `047c`.
- Se recuperaron 22 archivos exactos del snapshot. `reconciliation.json` añadió sus SHA-256 después de la recuperación. Esta finalización añade únicamente este informe, el checkpoint y el acta ligera de comprobaciones.

El snapshot es un commit de recuperación ya existente, creado por el archivado de Codex. Esta continuación no creó commits ni modificó HEAD o el índice.

## 2. Resultado funcional

El flujo prepara borradores de Architecture, compara alternativas tecnológicas y redacta un ADR vinculado a la elección explícita del Owner. Conserva las fuentes y la identidad de cada generación para impedir que una elección antigua o un ADR contradictorio se utilicen en una conciliación posterior.

La generación incorpora B0 y fuentes verificadas, instrucciones sobre responsabilidades, consistencia, seguridad, operación local y referencias RF/RNF. Las alternativas deben justificar su complejidad y la adopción de tecnologías distintas de Python. Los verificadores detectan algunas carencias; el cumplimiento semántico de estas instrucciones requiere revisión humana.

Las salidas seguras incompletas pueden conservarse como candidatos reparables, con hallazgos y revisión pendiente. Las revisiones Owner mantienen `before_owner`. Una nueva identidad de candidato o elección invalida las asociaciones dependientes. Los recibos registran llamadas, estado, duración y errores; la actividad puede consultarse tras una recarga. La generación segmentada limita cada acción manual a una unidad y conserva unidades previas.

La exportación offline entrega Markdown, fuentes y hashes, secciones, hallazgos, restricciones y elección Owner. Un consumidor simulado mejora una sección sin aceptar automáticamente el resultado. La decisión y las secciones que citan decisiones D-* están protegidas. También existe una declaración explícita Owner de ADR no aplicable, con justificación y vínculo a Architecture.

## 3. Archivos del candidato y alcance

Rutas relativas a la raíz absoluta del worktree indicada arriba. El inventario exacto con hashes está en `docs/audits/ux01_b/reconciliation.json`.

| Archivo recuperado | Cambio o finalidad |
|---|---|
| `.devpilot/gsdlc/architecture_authoring_profile.json` | Política de generación acotada: una llamada por acción, límites por unidad y revisión del contrato segmentado. |
| `src/devpilot_core/application/r03_03_architecture.py` | Prompt, B0, contexto e informe de calidad Architecture. |
| `src/devpilot_core/application/r03_03_segments.py` | Contexto acotado, sucesores por epoch, recibos y calidad segmentada. |
| `src/devpilot_core/application/r03_04_local_authoring.py` | Calidad Options/ADR, conservación de candidatos, recibos, actividad y rechazo de decisión contradictoria. |
| `src/devpilot_core/application/r03_04_quality_contract.py` | DTO de calidad conectado al flujo, alternativas repetidas y handoff seccional. |
| `src/devpilot_core/application/pre_code_wizard_service.py` | Acciones, elección Owner, guards de SHA/epoch/fuentes, revisiones y conciliación. |
| `src/devpilot_core/application/pre_code_adr_bundle_service.py` | Verificación adicional de epoch e identidad del companion. |
| `src/devpilot_core/application/services.py` | Paso de campos aditivos por facade y dispatcher existentes. |
| `src/devpilot_core/interfaces/api/routers/guided_sdlc.py` | DTO de entrada y acciones de exportación/no aplicabilidad. |
| `tests/test_r03_04_ux01_b_pipeline.py` | 22 casos focales, incluyendo parametrizaciones. |
| `scripts/ux01_b_offline_example.py` | Reproducción offline con fixtures sintéticos. |
| `docs/02_architecture/UX01_B_API_CONTRACT.md` | Contrato backend entregado para revisión; no inicia UX01-C. |
| `docs/audits/ux01_b/focal.xml` | Resultado JUnit conservado de la pasada de 132 casos. |
| `docs/examples/ux01_b/README.md` | Naturaleza y reproducción de las muestras. |
| `docs/examples/ux01_b/architecture.md` | Muestra sintética Architecture. |
| `docs/examples/ux01_b/technology_options.md` | Muestra sintética de alternativas. |
| `docs/examples/ux01_b/adr.md` | Muestra sintética ADR. |
| `docs/examples/ux01_b/sources.json` | Fuentes de prueba anonimizadas. |
| `docs/examples/ux01_b/classifications.json` | Clasificaciones reales de las muestras. |
| `docs/examples/ux01_b/handoff.json` | Paquete exportado de ADR. |
| `docs/examples/ux01_b/offline_proposal.json` | Propuesta simulada con lineage. |
| `docs/examples/ux01_b/adr_refined_offline.md` | ADR con mejora limitada a riesgos y mitigaciones. |

Son 9 archivos previamente versionados modificados y 13 añadidos recuperados. El cambio de perfil de Architecture pertenece al límite de llamadas de B; no es un cambio accidental de otro sprint. Los cambios de código recuperados están limitados a generación, calidad, persistencia, conciliación y su ruta API existente. No hay cambios de frontend, dependencias, Source Registry ni documentos de proyectos FROZEN en este delta. No se ejecutó una auditoría histórica o de proyectos externos para esta finalización.

Documentación adicional: `docs/audits/ux01_b/reconciliation.json` (recuperación anterior), `UX01_B_RESULT.md`, `docs/audits/ux01_b/UX01_B_CHECKPOINT.md` y `docs/audits/ux01_b/documentation_checks.json` (esta finalización).

## 4. Contratos afectados y compatibilidad

Se amplía `POST /api/v1/guided-sdlc/pre-code/technology-action` y la proyección de estado existentes. Campos aditivos: `artifact_kind`, `expected_sha256`, `generation_epoch`; acciones añadidas: `export_handoff`, `adr_not_applicable`. La autoridad Owner, los scopes y el lifecycle siguen en los servicios existentes.

La selección registra opción, SHA, actor y epoch. Los candidatos y revisiones exponen identidad, parentesco, `quality.current`, `quality.before_owner` y recibos de ejecución. La conciliación y el companion verifican las asociaciones exactas. La renovación de planes caducados utiliza el mecanismo existente y está cubierta por las focales conservadas; esta finalización no lo modifica ni ejecuta.

Los errores tipados se transportan por el CommandResult existente; el contrato API detalla los códigos de datos obsoletos, deriva de fuentes, concurrencia y recibos. `COMPLETE` describe una operación terminada, no una aprobación de calidad. Los hashes de bytes del archivo candidato y los hashes de Markdown lógico tienen usos distintos; no deben compararse indistintamente.

Persistencia aditiva en JSON y recibos existentes; sin migración de base de datos. Candidatos históricos sin calidad UX01 no se exportan atribuyéndoles ese informe. Los bindings históricos sin epoch mantienen la compatibilidad prevista. La reversión requiere revisión del delta B y conservación de outputs/recibos; no se ejecutó rollback.

## 5. Pruebas y evidencia verificable

El XML conservado registra la ejecución original de 2026-10-27 a las 05:19:34 -05:00, duración informada 12.527 s. Estos tiempos corresponden a pytest, no al trabajo total ni a inferencia real.

| Suite (archivo en `tests/`) | PASS |
|---|---:|
| `test_r03_04_ux01_b_pipeline.py` | 22 |
| `test_r03_04_ux01_a_quality_contract.py` | 18 |
| `test_mp132_r03_04_local_authoring.py` | 7 |
| `test_mp132_r03_04_context_pack.py` | 5 |
| `test_mp132_r03_04_c02_p5_flow.py` | 1 |
| `test_r03_04_p6_quality.py` | 4 |
| `test_r03_04_p7_owner_revision.py` | 5 |
| `test_r03_04_p8_action_dispatch.py` | 7 |
| `test_r03_04_p11_plan_refresh.py` | 3 |
| `test_mp132_r03_04_c02_rbac.py` | 2 |
| `test_mp132_r03_04_c02_p4_readiness.py` | 7 |
| `test_mp132_r03_04_technology.py` | 8 |
| `test_mp132_r03_03_architecture.py` | 17 |
| `test_mp132_r03_03_segments_c03.py` | 19 |
| `test_devpl_gsdlc_13_c_02_adr_companion.py` | 7 |
| **Total; fallos/errores/omitidos = 0/0/0** | **132** |

Cobertura acreditada: integración de calidad/handoff, candidatos incompletos conservados, fuentes/SHA/epoch obsoletos, elección T2 frente a ADR T1, conservación de `before_owner`, sucesores, concurrencia sin nueva inferencia, segundo dominio y EOL, opciones repetidas, ADR superficial, DTO/dispatch, no aplicabilidad, elección exportada, cambios durante inferencia, generación segmentada y actividad durable. Las suites existentes cubren además planes, RBAC/readiness y companion. Los transportes de modelo son simulados; no demuestran calidad de Ollama real.

Durante la recuperación se reprodujo el script offline: **PASS_LOGICAL_EQUIVALENCE**. Cuatro salidas solo cambiaron LF/CRLF; se restauraron sus bytes exactos del snapshot. En esta finalización no se volvió a ejecutar el script ni pytest. Se verifican hashes de los 22 archivos frente al manifiesto y al snapshot, XML, inventario de cambios, enlaces documentales y `git diff --check`. El acta de estas verificaciones queda en `documentation_checks.json`.

### Limitación de trazabilidad

No había un manifiesto de hashes capturado antes de la pasada de pruebas. La correspondencia se apoya en el orden de operaciones del chat original, la ausencia de ediciones de código registradas tras la última pasada, el delta final y el snapshot recuperado. Los hashes actuales prueban la identidad del candidato recuperado y su conservación durante esta finalización; **no certifican retroactivamente los bytes exactos que ejecutó pytest**. Se conserva esta limitación, aunque la evidencia aceptada resulta suficiente para no repetir los 132 casos en un cierre exclusivamente documental.

## 6. Calidad, riesgos y pendientes

Las tres muestras tienen `structural_disposition=STRUCTURALLY_VALID` y `quality_level=REVIEW_REQUIRED`. Son fixtures sintéticos, no salidas de Ollama ni documentos del Pilot B. La elección T1 es un dato de prueba. La ausencia de hallazgos mecánicos en estas muestras no acredita sustancia, coherencia semántica ni calidad profesional.

No se acredita `HANDOFF_READY` ni `PROFESSIONAL_REVIEWED`. La propuesta offline conserva `professional_reviewed=false` y requiere revisión Owner autenticada. La exportación de una muestra reparable es evidencia del mecanismo de transferencia, no un certificado de utilidad de todos los candidatos.

Riesgos y límites relevantes:

- Los límites de generación (448 tokens por unidad Architecture y prompts Options/ADR acotados) pueden producir contenido superficial o incompleto; hay que evaluar una salida local real.
- Los verificadores de stacks, secciones y términos son heurísticos. La prioridad Python y las ventajas de otra tecnología necesitan juicio humano.
- La serialización Technology usa un lock del proceso; esta evidencia no acredita concurrencia entre varios procesos de servidor ni recuperación integral tras caída.
- Los clientes pueden omitir SHA/epoch por compatibilidad; las comprobaciones explícitas de pantalla obsoleta requieren enviar los campos observados.
- No se ha validado aquí la UI, el operador Windows, inferencia real, proveedor externo, certificación profesional ni full regression. UX01-C y UX01-D no se iniciaron.
- La revisión Owner del candidato, la utilidad del handoff y la comprobación local real siguen pendientes. Ante contradicción material, falsa autoridad o regresión reproducida, corresponde **BLOCK** y registrar el hallazgo; no forzar PASS.

## 7. Estado Git del cierre documental previo (histórico)

| Ámbito | Estado y alcance de la evidencia |
|---|---|
| Worktree candidato `047c` | HEAD separado en UX01-A; 9 archivos versionados modificados, 13 añadidos recuperados y 4 documentos de conciliación/cierre adicionales. Índice vacío de cambios; candidato sin commit propio. HEAD y hashes del código se comprueban en esta finalización. |
| Repositorio principal `D:\Projects\DevPilot_Local` | La última consulta directa durante la recuperación lo encontró limpio en `evolution/multiprovider-v2`, HEAD UX01-A. En esta finalización se consulta la referencia local compartida, que sigue en UX01-A; no se vuelve a certificar su árbol de trabajo. No se integra el candidato. |
| Remoto | `refs/remotes/origin/evolution/multiprovider-v2` local sigue en UX01-A y coincide con la rama local. No se hizo fetch ni consulta de red en esta finalización: estado remoto vivo **UNKNOWN**. No hubo push. |

Estados locales: **versionados sin stage = 9**; **staged = 0**; **no versionados = 17** al completar los documentos (13 recuperados + conciliación + resultado + checkpoint + acta). Los directorios agrupados por `git status --short` no equivalen a un solo archivo. El acta registra la lista completa. El snapshot preservado no equivale a una integración del candidato.

## 8. Comprobaciones humanas necesarias para UX01-B

1. **Revisión Owner del candidato y de las muestras:** contrastar las fuentes con Architecture, alternativas y ADR; evaluar proporcionalidad, opción Python o razón de otra tecnología, decisión material, consecuencias, riesgos y utilidad de las tareas de reparación. Confirmar que las etiquetas de calidad y las decisiones de prueba no se confunden con aprobaciones reales.
2. **Una comprobación focal con Ollama real, en proyecto aislado y con el modelo ya disponible:** recorrer Architecture → Options → elección explícita → ADR → conciliación a nivel de borrador, con una llamada por acción/unidad. Conservar modelo, fuentes/SHA, epoch, candidatos y `before_owner`; revisar que el ADR respeta la opción y que la salida tiene contenido utilizable. No aplicar ni congelar el proyecto real. Si no existe modelo disponible, registrar el bloqueo sin instalarlo.
3. **Evaluar el handoff de una sección:** revisar el ADR original, paquete y propuesta offline ya existentes; confirmar que solo mejora riesgos y mitigaciones y conserva decisión, demás secciones, fuentes y lineage. Esta revisión puede usar las muestras guardadas sin repetir la reproducción.

Registrar el dictamen Owner con evidencia y pendientes. No se exige aquí validación integral de interfaz ni el operador Windows de UX01-D. La revisión documental por ChatGPT convencional puede ayudar a evaluar el candidato, pero no sustituye la ejecución local real ni el dictamen Owner.

## 9. Rutas exactas para revisión externa

Raíz: `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local`.

Entregar a ChatGPT convencional los archivos adjuntos; una ruta local por sí sola no le da acceso:

- `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\UX01_B_RESULT.md`
- `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\audits\ux01_b\UX01_B_CHECKPOINT.md`
- `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\audits\ux01_b\reconciliation.json`
- `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\audits\ux01_b\documentation_checks.json`
- `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\audits\ux01_b\focal.xml`
- `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\02_architecture\UX01_B_API_CONTRACT.md`
- Todos los 9 archivos de `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\examples\ux01_b\`: `README.md`, `architecture.md`, `technology_options.md`, `adr.md`, `sources.json`, `classifications.json`, `handoff.json`, `offline_proposal.json`, `adr_refined_offline.md`.

Para una revisión de código, adjuntar además los 8 archivos Python de aplicación/API, el perfil, el test y el script listados en el inventario; el manifiesto permite comprobar sus identidades. Este informe no contiene un patch completo. Para evaluar cumplimiento normativo del sprint, acompañar también el sprint y prompt aprobados UX01-B originales; esta continuación no los recrea ni modifica.

## 10. Correctivo focal posterior a la auditoría independiente

Fecha: 2026-10-27. **PASS técnico focal / PENDING_OWNER_REVIEW**. Se conservan el snapshot, el manifiesto, XML original, muestras, acta documental y `UX01_B_SOURCE_REVIEW.zip` como evidencia anterior al correctivo; no deben interpretarse como hashes/pruebas de la versión corregida. De los 22 archivos recuperados, 20 permanecen exactos y 2 cambian intencionalmente. La integridad de esta versión y las pruebas focales se registran en `docs/audits/ux01_b/corrective_checks.json`.

### Brechas confirmadas y cambios mínimos

1. **Vigencia de B0:** `pre_code_wizard_service.py` solo comprobaba B0 al exportar mediante el hash de todo `project.yaml`. Una elección, generación ADR o conciliación podía reutilizar Technology de un B0 anterior. Ahora comprueba el texto B0 registrado en calidad antes de esas acciones y de las revisiones Owner (para impedir que una revisión recertifique la fuente anterior). La conciliación verifica tanto Technology como ADR. La exportación usa la misma regla. La identidad de la solicitud ADR incluye un hash del texto B0 normalizado: si las Options sucesoras tienen idéntico Markdown después de cambiar B0, no se reutiliza un ADR antiguo de la caché. Un cambio de B0 durante inferencia conserva el candidato/recibo y bloquea asociarlo al estado.
2. **Igualdad editorial:** se compara únicamente el campo `business_need` parseado, unificando espacios y saltos de línea. Comentarios YAML, nombre del proyecto y LF/CRLF no invalidan esa comprobación. Se conservan los hashes originales de procedencia; no se reescriben recibos. No se intenta decidir equivalencia semántica entre redacciones distintas ni se ignoran cambios de palabras, negaciones o cifras.
3. **Reparación por sección:** `r03_04_quality_contract.py` añade el hallazgo `UX01_B_SECTION_BOILERPLATE` para cuerpos completos repetidos de al menos 35 caracteres o marcadores explícitos de desarrollo pendiente. Incluye instrucciones localizadas, con acciones específicas para componentes, consistencia, alternativas y riesgos. No es un nuevo motor semántico; una redacción genérica que eluda esos patrones puede necesitar revisión humana. No se autoasigna HANDOFF_READY ni calidad profesional.

Contrato de errores: `UX01_B_BUSINESS_NEED_DRIFT` ante contenido distinto y `UX01_B_BUSINESS_NEED_UNVERIFIED` cuando falta texto B0 trazable en el candidato; se transportan por el finding/CommandResult existente. No hay cambio de DTO o ruta. Un candidato anterior sin esa procedencia requiere una generación sucesora explícita, no una aprobación inferida. El guard de deriva conserva los candidatos y recibos previos; no congela ni aplica documentos.

### Archivos de este correctivo

- Funcionales: `src/devpilot_core/application/pre_code_wizard_service.py` y `src/devpilot_core/application/r03_04_quality_contract.py`.
- Pruebas nuevas: `tests/test_r03_04_ux01_b_corrective.py` (18 casos con parametrizaciones).
- Documentación: este informe, `docs/audits/ux01_b/UX01_B_CHECKPOINT.md` y la guía `docs/audits/ux01_b/UX01_B_OLLAMA_CHECK.md`.
- Evidencia adicional: `corrective_initial_setup.xml`, `corrective_retry_nodes.txt`, `corrective_focal.xml`, `corrective_adr_binding.xml`, `corrective_first_revision.json`, `corrective_checks.json` y `UX01_B_CORRECTIVE.patch`, dentro de `docs/audits/ux01_b/`.

### Pruebas efectivamente ejecutadas

La selección inicial comprendió 17 casos nuevos y las cinco suites directamente afectadas: pipeline B (22), contrato A (18), flujo C02/P5 (1), revisión Owner/P7 (5), dispatch/API P8 (7). **Selección inicial: 70 casos únicos PASS; balance final: 71 casos únicos PASS, con 18 nuevos, 0 fallos de aserción y 0 omitidos.** No se ejecutaron las 132 focales completas ni full regression ni inferencia real.

La primera invocación registró 37 PASS y 33 errores de preparación: faltaba el directorio padre `outputs` del `--basetemp`. Su XML se conserva como `corrective_initial_setup.xml`; no es una pasada íntegra PASS. Se creó ese directorio en `047c` y se repitieron únicamente los 33 casos no ejecutados, enumerados en `corrective_retry_nodes.txt`. `corrective_focal.xml` registra esos **33 PASS / 0 FAIL / 0 ERROR / 0 SKIP**. El acta reconcilia por ID los 37 éxitos iniciales con los 33 de la segunda invocación; no se suman ejecuciones duplicadas ni se crea un XML ficticio de 70 PASS. Después se añadió la identidad B0 de caché ADR y su prueba: `corrective_adr_binding.xml` registra 3 PASS (el nuevo caso y 2 casos de elección/flujo C02 repetidos porque esa rama cambió). La unión de IDs exitosos es 71, no 73. `corrective_first_revision.json` conserva los hashes de la revisión probada inicialmente; el acta final registra los de la revisión vigente y la revalidación focal de la última rama modificada.

Se usó el intérprete existente `D:\Projects\DevPilot_Local\.venv\Scripts\python.exe` en modo `-B`, con `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=src` de `047c` y `-p no:cacheprovider`. Esto reutiliza dependencias en lectura; las pruebas y temporales escriben en el worktree actual. No se instalaron dependencias ni se alteró el repositorio principal. El acta contiene los hashes contemporáneos de los dos archivos corregidos y el test nuevo; para las 132 pruebas originales sigue vigente la limitación de trazabilidad descrita en la sección 5.

La cobertura nueva verifica deriva material antes de selección/ADR/conciliación/revisión, preservación de estado y recibos, LF/CRLF/espacios/metadatos irrelevantes, ADR con B0 antiguo aunque Technology sea vigente, procedencia ausente, deriva durante inferencia, sucesor explícito y tareas de reparación localizadas sin certificación. `git diff --check` permanece PASS.

### Estado vigente, límites y siguiente acción

HEAD separado sigue en UX01-A; índice sin cambios, candidato sin commit propio. El repositorio principal no se modifica ni se vuelve a certificar su árbol de trabajo. Las referencias locales se registran en el acta; remoto vivo UNKNOWN, sin consulta de red ni push. El inventario anterior de 17 archivos no versionados es histórico: el acta correctiva registra el inventario actual, incluidos ZIP anterior y entregables nuevos.

La muestra histórica de Architecture queda conservada con su clasificación anterior; al evaluarla con el contrato corregido sus marcadores explícitos originan tareas de reparación. No se regeneran ni falsifican los resultados históricos de muestras. La corrección no prueba semántica profesional ni concurrencia entre procesos. No se amplía el guard B0 al resto del lifecycle/apply/freeze: este alcance es selección, ADR, conciliación, revisiones y exportación del candidato. Los upstream FROZEN permanecen intactos.

**Siguiente acción Owner:** seguir `docs/audits/ux01_b/UX01_B_OLLAMA_CHECK.md` con proyecto aislado y modelo ya instalado, guardar evidencia y dictamen. La guía observa el backend mediante solicitudes manuales autenticadas; no inicia UX01-C ni UX01-D. Esta continuación no llamó Ollama ni APIs externas, no instaló paquetes/modelos ni hizo commit, merge, integración o push.

Para la revisión independiente, entregar además del paquete anterior el patch `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local\docs\audits\ux01_b\UX01_B_CORRECTIVE.patch`, el acta `corrective_checks.json`, los tres XML correctivos, la lista de reejecución y esta guía, informe y checkpoint actualizados. El ZIP anterior se conserva como base de comparación; no es un paquete actualizado.
