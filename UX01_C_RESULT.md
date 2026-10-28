# UX01-C — Architecture Workbench: resultado del candidato

Fecha: 2026-10-27T17:01:27.529851-05:00

**PASS técnico focal / CANDIDATO LOCAL / PENDING_OWNER_REVIEW.** No se declara cerrado UX01-C ni se inicia UX01-D.

## Autoridad y baseline

El Owner aceptó el cierre técnico UX01-B sobre `ba74af6aec2dd0bec703865ae1ff4c5ba992bef0` y 71 focales PASS. La calidad real Ollama sigue sin acreditarse y es condición obligatoria de UX01-D. Se leyeron literalmente el sprint v1.1.0 OWNER_APPROVED y el prompt C v1.0.0 OWNER_APPROVED_IMPLEMENTATION_PROMPT. No se usaron etiquetas editoriales para conceder permisos.

- `C:\Users\Pedro\Downloads\DEVPL_MP_132_A190_R03_PLAN_C02\7_ Execution_packages-sprints_prompts\BACKLOG_R03\SPRINT_R03_04_UX_01_ARCHITECTURE\SPRINT_R03_04_UX_01_ARCHITECTURE_WORKBENCH_v1_1_0_OWNER_APPROVED.md` — SHA-256 `4e771230fff8325896c7d0d4f634abce77fc31c8d8c9ec31e10e9273137c8381`.
- `C:\Users\Pedro\Downloads\DEVPL_MP_132_A190_R03_PLAN_C02\7_ Execution_packages-sprints_prompts\BACKLOG_R03\SPRINT_R03_04_UX_01_ARCHITECTURE\PROMPT_R03_04_UX_01_03_C.md` — SHA-256 `eba420be017dd6bb6aeca1d9893ea231182aad068aeabb33165892cf8089b2d1`.

Antes de editar C se consultó el remoto vivo: estaba en UX01-A, mientras el principal limpio tenía un único commit adicional, UX01-B. Se hizo exclusivamente un **push normal** `HEAD:refs/heads/evolution/multiprovider-v2`, sin force, y se comprobó HEAD/origin local/remoto vivo iguales a UX01-B. La consulta final sigue coincidiendo. No hubo fetch/pull, merge ni adaptación silenciosa.

## Resultado funcional

- Un único Architecture Workbench en Architecture; tres pestañas primarias: **Arquitectura**, **Opciones tecnológicas**, **ADR**. También conserva consulta en etapas posteriores y en PRE_CODE_READY cuando ya existe Architecture.
- Cada pestaña renderiza el Markdown completo del candidato o fuente aprobada, con tablas, listas, citas, bloques, enlaces seguros y frontmatter íntegro como metadatos. No usa innerHTML ni carga imágenes externas. Se conserva la navegación por línea del visor compartido.
- Una sola superficie activa: lectura Markdown o editor Owner, con preview/cancelación y borrador editorial preservado entre pestañas, refresh y errores. Preferencia de pestaña y texto sin guardar están en sessionStorage por workspace; nunca son autoridad de approval. Una revisión con hash base antiguo se conserva pero no se guarda sobre otro candidato.
- Cabecera común con proyecto/workspace, estado server-side, fuente/identidad, elección, calidad, siguiente acción y recibos. Guided/Expert leen los mismos documentos y permisos.
- Generación y sucesores usan los endpoints existentes. Cambiar T1/T2 o regenerar exige confirmación de invalidación y envía epoch/SHA observados. Una acción Architecture solicita una unidad acotada; no se agregan bucles de inferencia o reintentos automáticos.
- Progreso inmediato con tiempo medido desde el clic, botones bloqueados con motivo, estado/receipt recuperable y tratamiento de resultado incierto. No hay porcentaje, ETA ni cancelación de inferencia ficticios. Los 409 orientan a renovar diff sobre los mismos bytes; 500/red se muestran sin detalles privados y conservan el borrador.
- Diff/approval/apply/freeze y companion reutilizan los servicios, planes y controles existentes. No se ejecutaron esas operaciones sobre el piloto. La API vuelve a validar sesión, rol, scope, B0, fuentes y lineage.

## Contratos y protección FROZEN

Extensión aditiva de GET `/api/v1/guided-sdlc/pre-code`: `architecture_workbench_documents`, `architecture_inference_pending`, `project_name`. Los documentos solo se agregan dentro del scope autenticado. Architecture FROZEN se lee del archivo aprobado con SHA exacto; ante deriva/path inválido se devuelve BLOCK sin texto obsoleto. Los companions materializados requieren el bundle gobernado ready/receipt válido y sus postimágenes exactas. Sin materialización acreditada se muestran candidatos REVIEW_REQUIRED, nunca archivos falsamente FROZEN.

La proyección nueva es de lectura; no crea approvals, writers, estados lifecycle o registro de fuentes paralelos. El cliente tipa los campos de B y acciones export_handoff/adr_not_applicable sin cambiar sus rutas. Se corrige el recorte a 240 s del presupuesto Technology/ADR: solo sus acciones de inferencia admiten 450 s, por encima de los 380 s del adaptador; sin ampliar el límite de otras operaciones ni habilitar retry.

## Archivos

7 archivos versionados modificados y 5 nuevos de implementación/pruebas; este resultado añade un sexto archivo nuevo (13 rutas totales).

```text
src/devpilot_core/application/pre_code_wizard_service.py
ui/web/package.json
ui/web/src/api/client.ts
ui/web/src/api/types.ts
ui/web/src/components/DocumentViewer.ts
ui/web/src/pages/PreCodeWizardView.ts
ui/web/src/styles.css
src/devpilot_core/application/architecture_workbench_projection.py
tests/test_r03_04_ux01_c_projection.py
ui/web/scripts/ux01c-workbench-smoke.mjs
ui/web/scripts/ux01c-workbench.browser.ts
ui/web/src/components/ArchitectureWorkbench.ts
UX01_C_RESULT.md
```

La extensión del renderer seguro de DocumentViewer mantiene su interfaz y agrega tablas, listas ordenadas, citas y enlaces, además de preservar navegación por líneas. Las demás etapas Pre-code conservan su editor y lifecycle; Architecture utiliza el componente canónico. El cambio en package.json solo añade test:ux01-c, sin dependencias nuevas.

## Validaciones iniciales en Windows (histórico anterior al correctivo)

| Validación | Resultado |
|---|---|
| Focales Python: proyección C (9), dispatch P8 (7), RBAC C02 (2), companion (7) | **25 PASS, 0 FAIL, 0 ERROR, 0 SKIP** |
| Chrome headless instalado: DOM real con transporte simulado | **24 casos PASS** |
| Build UI final Vite 6.4.3 | **PASS**, 78 módulos, 1.58 s informados por Vite |
| Integridad final de fuentes respecto de hashes pre-test | **12/12 PASS** |
| Archivos monitoreados del piloto/runtime | **8/8 sin cambios** |
| git diff --check | **PASS** |

Python: `.venv/Scripts/python.exe -B -m pytest tests/test_r03_04_ux01_c_projection.py tests/test_r03_04_p8_action_dispatch.py tests/test_mp132_r03_04_c02_rbac.py tests/test_devpl_gsdlc_13_c_02_adr_companion.py --basetemp=outputs/ux01_c_validation/pytest_tmp --junitxml=outputs/ux01_c_validation/focal.xml -p no:cacheprovider -q`, cwd `D:\Projects\DevPilot_Local`, PYTHONPATH a su src y bytecode deshabilitado. Esta fue una sola invocación Python. JUnit: `{"name": "pytest", "errors": "0", "failures": "0", "skipped": "0", "tests": "25", "time": "3.408", "timestamp": "2026-10-27T16:50:12.272266-05:00", "hostname": "DESKTOP-BKQ8PJI"}`.

UI: `node ui/web/scripts/ux01c-workbench-smoke.mjs`; build: `npm --prefix ui/web run build`. Se hizo una pasada inicial DOM de 22 casos/build; dos precisiones del audit (inicio real del contador y navegación por línea del renderer compartido) justificaron las revalidaciones UI de 23 y 24 casos y sus builds. El resultado de esa revisión inicial fue **24**, no la suma de esas pasadas. Python no se repitió porque sus fuentes no cambiaron.

Los casos DOM cubren AC-03 (un contenedor, tres pestañas, documentos distintos/completos, editor único), edición/preview/preservación, sucesión T1/T2 y SHA/epoch, doble clic/progreso, 409, 500 redacted, recarga/recibo terminal, vacío/candidato/FROZEN, rol, Guided/Expert, handoff/hallazgos, frontmatter/Markdown seguro, viewport reducido/overflow, contrato de timeout y navegación por línea. Los casos Python prueban lectura FROZEN por SHA, drift/path bloqueados, companions y scope sin conceder permisos nuevos.

**Alcance de la evidencia:** las pruebas se ejecutaron en Windows, contra fuentes del principal y Chrome instalado. El transporte es simulado y los proyectos son fixtures temporales: no es un recorrido real con Ollama, ni prueba de calidad profesional ni aceptación integral. No se capturaron screenshots; se conserva DOM real de las pruebas y su JSON de resultados. No se inició el servidor de producción; el harness abre un listener local efímero para servir únicamente los tests y lo cierra.

### Chequeo TypeScript y observaciones

El tsc exploratorio no es globalmente limpio: mostró **6 TS2352** en casts de Release/Recovery/Reconciliation del cliente. Una comparación de diagnóstico (archivo/código/mensaje) con las mismas fuentes leídas desde UX01-B confirmó los mismos 6, sin diagnósticos nuevos de C. No se modificaron esos métodos ajenos al alcance. No se presenta tsc global como PASS. Build, sintaxis y pruebas focales sí PASS.

OBSERVE_ONLY: Vite advierte chunk JS final de aproximadamente 646.86 kB minificado (>500 kB); no se cambió el umbral ni se rediseñó la partición global. Las reglas de Markdown son un subconjunto seguro extendido para este producto, no certificación de compatibilidad total CommonMark. Un receipt activo/interrumpido o respuesta incierta sin sucesor terminal permanece bloqueado hasta consultar evidencia; no se promete cancelación del backend. sessionStorage es recuperación editorial local y no sincroniza borradores entre dispositivos.

## Evidencia y patch

Raíz de evidencia: `D:\Projects\DevPilot_Local\outputs\ux01_c_validation`. Se conservan `focal.xml`, `browser-result.json` (24), `browser-dom.html`, `browser-stderr.log`, `initial_browser-result.json` (22), `timer_browser-result.json` (23), y los manifiestos pre-test `pretest.json`, `pretest_final_ui.json`, `pretest_final.json`.

La comprobación del patch detectó diferencias físicas CRLF durante su serialización de texto en Windows; se emitió finalmente en bytes LF y se validó contra el baseline Git normalizado usando un índice temporal independiente, sin alterar el índice real ni las fuentes. El acta final `validation.json` contiene hashes, scope y estados Git. El diff completo del candidato respecto de UX01-B está en `outputs/ux01_c_validation/UX01_C.patch`; incluye archivos nuevos y este informe. No es un baseline ZIP ni un bundle Windows de D. Los datos de tests y dist permanecen ignorados.

## Git, exclusiones y pendientes

- Repositorio de implementación: `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`; HEAD `ba74af6aec2dd0bec703865ae1ff4c5ba992bef0`. Índice sin stage; C permanece como cambios locales revisables, sin commit ni push de C.
- Referencia local origin y remoto vivo: `ba74af6aec2dd0bec703865ae1ff4c5ba992bef0` (consulta final). El push de este encargo publicó únicamente el commit B aceptado.
- Worktree 047c preservado con su checkpoint B `ee01a9e4c1e6e6477a60a7d2f339f59a2f4ea58b`; no se creó otro worktree. Los archivos de preparación están ignorados; no se cambió allí la implementación versionada.
- No se versionan auth DB, credenciales, dependencias, estado del piloto ni temporales. No hubo instalaciones, inferencia Ollama, full regression, modificaciones FROZEN, commit de C o inicio de D.

La comparación directa del piloto se limita a project.yaml, workspace-registration.json, Vision, Scope, Requirements, Architecture, registro runtime del principal y state pre-code del piloto. Los ocho hashes permanecen iguales; no se afirma una auditoría completa de todos los archivos del piloto.

**Siguiente acción Owner:** revisar este resultado, patch y evidencias para decidir la aceptación técnica de UX01-C y su commit/integración. UX01-D requiere orden específica; allí siguen pendientes la importación gobernada del proyecto aislado, calidad real Ollama, recorrido integral de UI/lifecycle/companion y GUIA_UNICA_WINDOWS.md.


## Correctivo focal de selectores — 2026-10-27

**PASS técnico focal / PENDING_OWNER_REVIEW.** Esta sección actualiza la evidencia vigente de interfaz; conserva la evidencia histórica anterior. No declara cierre ni inicia UX01-D.

### Validación visual comunicada por el Owner

Resultado literal recibido:

> El Owner realizó la validación visual sobre el piloto B original, en modo consulta, con resultado favorable para el contenedor único, los tres documentos Markdown y los estados FROZEN.

Es una comprobación reportada por el Owner, previa a este correctivo. No se repitió ni se atribuye a las pruebas automatizadas. El cambio visual de pestañas y los selectores quedan disponibles para su revisión final.

### Correctivo y contratos existentes

Se sustituyó el nombre libre por un selector de modelos obtenidos mediante `DevPilotApiClient.probeLocalModelReadiness()`, POST `/settings/local-model-readiness/probe` dentro de la base API existente. Se utilizan únicamente los nombres devueltos por el proveedor Ollama saludable, sin catálogo paralelo, instalaciones ni modelo obligatorio. Se conserva la selección entre pestañas; el modelo histórico solo se preselecciona si sigue instalado, o se selecciona automáticamente el único disponible. El modelo escogido llega a los payloads existentes de Architecture, Options y ADR.

Se recuperó «Modo de autoría», filtrado por `allowed_modes` de la etapa y las cuatro modalidades reconocidas por el contrato vigente: `LOCAL_MODEL`, `DEVPL_MOCK`, `MANUAL`, `IMPORT`. Ninguna de estas cuatro fue retirada. Valores desconocidos no se ofrecen. `DEVPL_MOCK` conserva su generador determinístico existente, sin inferencia Ollama; Manual e Import utilizan el guardado existente, con un único editor y sin approval automático. Options/ADR mantienen su requisito previo Architecture LOCAL_MODEL; no se amplió su contrato a otros modos.

La consulta de modelos se comparte dentro del componente y puede actualizarse explícitamente. Si falla o no hay modelos, se explica la condición y se bloquea la generación que necesita modelo; siguen disponibles las acciones de revisión/guardado/elección permitidas por rol y estado. Los controles de autoría, modelo, importación, edición y generación quedan deshabilitados en FROZEN. No se añadieron endpoints ni se modificó Python, approval, lifecycle, Source Registry, calidad multiprovider o el generador de documentos.

El CSS distingue pestañas inactivas y seleccionada mediante fondo, borde y forma; conserva las tres pestañas, ARIA, teclado, foco y disposición adaptable. No se rediseñaron otras etapas.

### Archivos de este correctivo

- `ui/web/src/components/ArchitectureWorkbench.ts`: selectores y conexión a las acciones existentes.
- `ui/web/src/styles.css`: presentación focal de pestañas y límites responsivos de selectores.
- `ui/web/scripts/ux01c-workbench.browser.ts`: 14 casos nuevos y selección de los 7 casos anteriores impactados; transporte de modelos simulado; ajuste del fixture para conservar la referencia de la vista tras refresh.
- `ui/web/scripts/ux01c-workbench-smoke.mjs`: modo focal mediante `UX01_C_TEST_SCOPE=selectors`, con resultados separados de los históricos.
- `UX01_C_RESULT.md`: esta conciliación documental.

El candidato C completo sigue comprendiendo las mismas 13 rutas enumeradas arriba. El resto de fuentes permaneció idéntico a la evidencia anterior.

### Validación vigente y economía de pruebas

Antes de aplicar el correctivo se comprobaron los 13 hashes del acta anterior. Tras estabilizar los cuatro archivos se registraron hashes pre-test de las 12 fuentes/pruebas, excluyendo este informe documental. Se ejecutó **una única validación focal consolidada de 21 casos Chrome DOM: 21 PASS**, seguida de **un único build UI final PASS**. No hubo cambios funcionales después, ni reejecuciones. Las 12/12 huellas pre-test y post-test coinciden.

Comandos desde `D:\Projects\DevPilot_Local`:

```powershell
$env:UX01_C_TEST_SCOPE = 'selectors'
node ui/web/scripts/ux01c-workbench-smoke.mjs
npm --prefix ui/web run build
```

Los 21 casos incluyen allowlist de modos, catálogo real descubierto (simulado en pruebas), selección alternativa sin gemma obligatorio, envío de modelo a los tres flujos, ausencia de modelos, fallo de discovery sin datos privados, Manual, Import con archivo íntegro, DEVPL_MOCK, conservación editorial, FROZEN sin discovery, rol viewer, recibo pendiente, trabajo sin guardar, doble solicitud y pestañas/teclado/viewport reducido. Son 14 casos nuevos y 7 casos previos impactados repetidos justificadamente por los cambios del componente; no se suman a los 24 históricos para anunciar un total vigente ficticio.

Las **25 pruebas Python PASS previas se conservan sin repetir**: no cambió ningún archivo Python ni contrato de backend. Tampoco se repitieron las pruebas anteriores ajenas al correctivo del renderer/API. Python utilizado para comprobaciones de integridad y empaquetado: `D:\Projects\DevPilot_Local\.venv\Scripts\python.exe`, con `-B`; dependencias existentes, sin instalaciones.

Build Vite 6.4.3: 78 módulos, 3.12 s; JS `index-BC_OEGIy.js` 651.56 kB y CSS `index-BCFQ_OjK.css` 95.69 kB. Persiste la advertencia >500 kB; no bloquea este correctivo. Los seis TS2352 heredados documentados anteriormente no se corrigieron ni se repitió tsc global; no se declara tsc global PASS.

### Evidencia, Git y protección del piloto

Evidencia nueva en `D:\Projects\DevPilot_Local\outputs\ux01_c_selectors_validation`: `pretest.json`, `checks.json`, `browser-result.json`, `browser-dom.html`, `focal.log`, `build.log`, `validation.json`, `manifest.json` y `UX01_C.patch`. Evidencia histórica conservada en `D:\Projects\DevPilot_Local\outputs\ux01_c_validation`, incluido `focal.xml` de 25 Python y `browser-result.json` de 24 DOM anteriores.

El patch nuevo contiene **todo C respecto de UX01-B**, incluidos archivos nuevos e informe, y se comprueba contra el árbol B mediante un índice temporal independiente. No altera el índice real. El manifiesto acredita fuentes y evidencias; no contiene documentos privados del piloto.

HEAD y referencia local origin continúan en `ba74af6aec2dd0bec703865ae1ff4c5ba992bef0`, rama `evolution/multiprovider-v2`, sin stage, commit ni push de C. La verificación del remoto vivo descrita arriba pertenece a la integración B anterior; no se repitió una consulta de red en este correctivo. 047c permanece preservado, sin worktree nuevo.

**Personal_care_sales no se modificó.** Se comprobaron antes y después los mismos seis archivos del piloto (metadatos y Vision/Scope/Requirements/Architecture), incluidos sus cuatro documentos FROZEN, con hashes iguales a la evidencia anterior; además, los dos archivos runtime monitoreados permanecieron iguales durante este trabajo: 8/8 sin cambios. No se reabrieron documentos, no se inició API de producción ni se ejecutó inferencia real.

### Entrega y límites pendientes

Paquete único para revisión: `D:\Projects\DevPilot_Artifacts\R03_04_UX_01\UX01_C_OWNER_REVIEW.zip`. Incluye informe, fuentes del candidato, patch completo contra B, manifiesto, pruebas y resultados focales nuevos e históricos seleccionados. Excluye perfiles Chrome, temporales pytest, cachés, dependencias, credenciales y contenido del piloto. El SHA-256 del ZIP se comunica tras su verificación, fuera del propio archivo para evitar una referencia circular.

El transporte de pruebas es simulado en Chrome real. Quedan para decisión final Owner la presentación de los controles/pestañas y la aceptación técnica del candidato; no se exige repetir la validación visual ya reportada del piloto. La inferencia Ollama real, calidad profesional de documentos y recorrido integral siguen pendientes de UX01-D autorizado. No se inició D, no hubo regresión completa, commit ni push. **Detenido para revisión final de ChatGPT convencional y del Owner.**
