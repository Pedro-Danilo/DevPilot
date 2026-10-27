# UX01-B — Comprobación focal con Ollama real

Para Owner con experiencia beginner-medio. Esta guía no se ha ejecutado con Ollama en el correctivo. Su resultado empieza en **PENDING**. Se detiene en borradores; no requiere apply/freeze, integración ni operador integral Windows de UX01-D.

## 1. Preparar el entorno aislado

Usa la API ejecutada desde `C:\Users\Pedro\.codex\worktrees\047c\DevPilot_Local`, con runtime/outputs de ese worktree. No uses el servidor del repositorio principal. Utiliza el arranque local ya configurado; esta guía no instala paquetes ni prepara un nuevo operador de arranque. Si no hay API/UI operativas con las dependencias existentes, registra **BLOCK_ENTORNO** antes de generar.

Abre la UI local e inicia sesión Owner. Selecciona mediante el flujo existente un **proyecto de validación aislado**, con nombre y ruta distintos del proyecto real. Verifica la ruta completa en el contexto de workspace y en las respuestas API. No copies credenciales, bases de datos ni el proyecto FROZEN real.

El proyecto aislado debe tener B0 en `.devpilot/project.yaml` y sus propios Vision, Scope y Requirements ya preparados y gobernados; el backend exige estos tres upstream FROZEN. Se leen sin editarlos. Si no existe ese fixture gobernado, registra **BLOCK_FIXTURE** y solicita su preparación separada por el flujo habitual; no inventes hashes ni marques FROZEN manualmente. Este correctivo no crea ni modifica ese proyecto.

Ejemplo de caso para un fixture nuevo preparado por separado: una operadora registra ventas locales y stock, exige venta/descuento atómicos, respaldo recuperable, uso local y aprobación humana para efectos sensibles. Conserva los RF/RNF y límites reales de sus documentos. No uses las muestras sintéticas como si fueran requisitos aprobados de un proyecto real.

En PowerShell, `ollama list` permite consultar los modelos instalados sin generar ni descargar. Anota el nombre exacto de uno disponible. Si Ollama no responde o falta un modelo, detente; no uses `ollama pull`. No es necesario cambiar de modelo para completar la comprobación.

## 2. Preparar solicitudes manuales autenticadas

La UI heredada puede encadenar varias solicitudes de Architecture desde un clic y todavía no representa todo el DTO de B. Para observar **una solicitud por paso**, usa F12 → Console en la UI local ya autenticada. Mantén DevTools → Network abierto. Confirma que el host es `127.0.0.1`; ajusta solo el puerto a la API local que acabas de verificar. El ejemplo usa el puerto habitual 8787.

Pega este pequeño ayudante en la consola. Reutiliza la sesión Owner, el CSRF y el token local ya configurados; no crea identidades ni imprime secretos. No pegues código de terceros ni exportes un HAR con cookies/headers.

```javascript
var uxBApi = 'http://127.0.0.1:8787/api/v1';
var uxBCall = async (path, body) => {
  const headers = {};
  const token = sessionStorage.getItem('devpilot.apiToken');
  if (token) headers['X-DevPilot-Token'] = token;
  const csrf = document.cookie.split('; ').find(s => s.startsWith('devpilot_csrf='));
  if (csrf) headers['X-DevPilot-CSRF'] = decodeURIComponent(csrf.slice('devpilot_csrf='.length));
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const response = await fetch(uxBApi + path, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'include', headers,
    ...(body === undefined ? {} : {body: JSON.stringify(body)})
  });
  const result = await response.json();
  if (!response.ok || !result.ok) throw new Error(JSON.stringify({http: response.status, result}));
  return result;
};
var uxBState = await uxBCall('/guided-sdlc/pre-code');
console.log(uxBState);
```

Revisa `data.pre_code.workspace_id`, el contexto de la UI y la etapa actual. Deben corresponder al proyecto aislado. Un 401/403 exige corregir sesión, CSRF o scope mediante la UI existente; no quites controles. Un BLOCK de contenido/estado se conserva como evidencia y se investiga antes de continuar. No repitas una inferencia cuando desconozcas si terminó.

## 3. Generar y leer Architecture

La etapa Architecture debe estar habilitada, en MISSING o DRAFT sin plan/approval activo. Sustituye el ejemplo por **el nombre exacto de tu modelo instalado**:

```javascript
var uxBModel = 'NOMBRE_EXACTO_DEL_MODELO_INSTALADO';
var uxBArch = await uxBCall('/guided-sdlc/pre-code/stages/architecture/draft', {
  mode: 'LOCAL_MODEL', content: '', model: uxBModel, regenerate: false
});
console.log(uxBArch);
```

Si devuelve `data.segmented_progress` con IN_PROGRESS, anota completed/total y realiza **la misma solicitud una vez más por cada unidad pendiente**, esperando su respuesta. No hagas un bucle automático. Al recibir el DRAFT ensamblado, detente y vuelve a consultar `uxBState`. Si ya existe un candidato ajeno a esta comprobación, consérvalo y detente para decidir su sucesión; no envíes `regenerate:true` a ciegas.

En `data.pre_code.stages`, localiza `stage_id='architecture'`: lee `draft_content`, `content_sha256` y `derivation` (en particular `generation_epoch` y `ux01_quality`). Compara con B0, Vision, Scope y Requirements del fixture: responsabilidades y límites, flujo principal, transacción/errores, seguridad, despliegue local, respaldo y asuntos diferidos. Los IDs de fuentes y RF/RNF deben ser comprobables. Anota UNKNOWN y contenido genérico. COMPLETE y STRUCTURALLY_VALID no equivalen a una arquitectura útil.

## 4. Generar Options y elegir explícitamente

```javascript
var uxBOptions = await uxBCall('/guided-sdlc/pre-code/technology-action', {
  action: 'generate_options', model: uxBModel
});
var uxBTech = uxBOptions.data.r03_04_authoring.technology;
console.log(uxBTech);
```

Exige alternativas materialmente distintas, proporcionalidad al equipo y operación local, opción Python o ventaja comparativa justificada de otra tecnología, tradeoffs y costos desconocidos señalados. Revisa `quality.current.findings`, `suggested_fix`, fuentes y B0. Conserva la salida original antes de cualquier edición; si solo hay etiquetas diferentes para el mismo stack o texto vacío, registra **BLOCK_UTILIDAD**, sin inventar una alternativa.

Decide T1 o T2 tras esa lectura y sustituye el ID del ejemplo. Copia el epoch y **SHA del archivo candidato**, no el hash lógico de `quality.current`:

```javascript
var uxBChoice = 'T1';
var uxBSelected = await uxBCall('/guided-sdlc/pre-code/technology-action', {
  action: 'select_option', option_id: uxBChoice,
  expected_sha256: uxBTech.candidate_sha256, generation_epoch: uxBTech.generation_epoch
});
```

La selección debe persistir en la siguiente consulta de estado. Si hay `UX01_B_BUSINESS_NEED_DRIFT`, no edites el candidato viejo para aparentar vigencia: revisa el cambio real de B0, conserva los recibos y solicita una nueva generación explícita de Options. Si falta procedencia B0, aparece `UX01_B_BUSINESS_NEED_UNVERIFIED`; tampoco se reutiliza por inferencia.

## 5. Generar ADR y comprobar su decisión

```javascript
var uxBAdrReply = await uxBCall('/guided-sdlc/pre-code/technology-action', {
  action: 'generate_adr', model: uxBModel, generation_epoch: uxBTech.generation_epoch
});
var uxBAdr = uxBAdrReply.data.r03_04_authoring.adr;
console.log(uxBAdr);
```

Lee Contexto, Decisión, Alternativas, Consecuencias, Riesgos/mitigaciones y Reversibilidad. La decisión debe identificar la opción que elegiste y justificar descartes y efectos adversos con fuentes. Conserva IDs, hashes, epoch, `input_binding` en los recibos y `before_owner` en calidad. No cambies de opción para acomodar una respuesta equivocada del modelo.

Si necesitas edición Owner, guarda primero la evidencia original. Las acciones existentes `owner_revise_options` y `owner_revise_adr` crean revisiones; revisar Options requiere elegir de nuevo y regenerar el ADR. Verifica que `before_owner` permanece intacto. No se exige reparar iterativamente una salida mala para declarar PASS: puedes entregar el hallazgo al Owner.

## 6. Conciliar solo el DRAFT y revisar handoff

Consulta de nuevo el estado; copia el SHA lógico actual de Architecture y su epoch observado. Conciliar no requiere aprobar ni aplicar:

```javascript
uxBState = await uxBCall('/guided-sdlc/pre-code');
var uxBArchRow = uxBState.data.pre_code.stages.find(s => s.stage_id === 'architecture');
var uxBReconciled = await uxBCall('/guided-sdlc/pre-code/technology-action', {
  action: 'reconcile', expected_sha256: uxBArchRow.content_sha256,
  generation_epoch: uxBTech.generation_epoch
});
var uxBExport = await uxBCall('/guided-sdlc/pre-code/technology-action', {
  action: 'export_handoff', artifact_kind: 'adr',
  expected_sha256: uxBAdr.candidate_sha256, generation_epoch: uxBTech.generation_epoch
});
console.log(uxBExport.data.handoff);
```

Relee el DRAFT conciliado y confirma la elección exacta, la conservación del resto de Architecture y la invalidación de un plan previo si existía. Revisa `section_tasks` y si sus instrucciones son útiles. Los cuerpos repetidos o explícitamente pendientes deben tener recomendaciones localizadas; la ausencia de ese patrón no certifica calidad semántica. Para comprobar la propuesta por sección sin otro proveedor, compara también `docs/examples/ux01_b/adr.md`, `handoff.json`, `offline_proposal.json` y `adr_refined_offline.md`; estas muestras son históricas y sintéticas.

No necesitas cambiar B0 ni los upstream para esta comprobación humana: los negativos de deriva y los casos LF/CRLF/editoriales están acreditados por las pruebas focales. No pulses aprobación, apply, freeze o materialización companion; no forman parte de esta guía.

## 7. Guardar evidencia y dictamen

Guarda únicamente los JSON de respuestas y Markdown del fixture (por ejemplo con `copy(JSON.stringify(uxBState, null, 2))` desde DevTools), junto con los recibos de `outputs/mp132_r03_03/<workspace_id>/` y `outputs/mp132_r03_04/<workspace_id>/` del worktree. No exportes cookies, tokens, contraseñas ni bases de autenticación. Conserva candidatos anteriores.

Adjunta una nota: fecha, worktree/HEAD y hashes del correctivo de `corrective_checks.json`, proyecto/ruta aislados, modelo instalado, fuentes/IDs/hashes, candidato/epoch, opción elegida, lectura de calidad y hallazgos antes de edición, revisiones si hubo y utilidad del handoff. Escribe **PASS focal**, **BLOCK** con motivo o **PENDING** si no ejecutaste un paso. La aprobación profesional no es automática. Entrega el dictamen al Owner y detente antes de integrar.
