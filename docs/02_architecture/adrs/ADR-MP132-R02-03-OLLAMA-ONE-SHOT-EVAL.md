---
doc_id: ADR-MP132-R02-03-OLLAMA-ONE-SHOT-EVAL
status: accepted-for-r02-03-local-candidate
baseline: 8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc
scope: R02-03-only
---
# ADR — Ollama: one-shot Owner evaluation sin runtime enablement

## Contexto
R02-02 acreditó health local de Ollama, no permiso global de ejecución ni aptitud de tarea. R02-03 requiere una llamada real pero no debe habilitar el router de modelos para el resto de DevPilot, ni alterar los documentos FROZEN.

## Decisión
Se define una operación **one-shot de evaluación sintética** autenticada con sesión humana Owner y CSRF, detrás del API local. Usa el `OllamaAdapter` existente y valida `localhost`/modelo instalado, sin activar globalmente el provider. `execute=false` es el valor por defecto; `execute=true` se inicia desde un clic Owner confirmado. El prompt proviene únicamente de tres casos versionados, no de documentos privados. Límite de salud 2 s y generación 75 s; JSON estructurado acotado, sin redirects y sin API externa. Se usa `ArtifactCandidateEnvelope` de R01; la salida se persiste solo en `outputs/mp132_r02_03/candidates/` como recibo runtime con ID idempotente. Respuestas inválidas son BLOCK, sin fallback silencioso ni segundo request automático.

## Autoridad
Esta evaluación no concede `EVALUATED`, `ELIGIBLE`, `SELECTED`, aprobación de artefactos, source-write ni FROZEN. Son prerrogativas de las etapas R02-06/R02-07 y del ciclo Pre-code ya existente. Fallo por modelo ausente o timeout conserva disponible la ruta determinística independiente; nunca se declara calidad EQUIVALENT por defecto.

## Alternativas descartadas
- Habilitar `providers.yaml` global para pasar una prueba: cambia autoridad permanente, no corresponde a R02-03.
- Añadir otro lifecycle de candidatos o publicar directamente archivos de proyecto: duplicaría el gobierno R01.
- Inferencia automática durante el arranque o en un GET: viola opt-in y reproduce riesgos de red/costo.

## Verificación y riesgos residuales
Tres casos reales sintéticos Vision/Scope/Requirements y dos negativas automatizadas como mínimo; recibo, screenshot inmediato, modelo/version, hashes, latencia. El outcome de una inferencia no garantiza semantic quality. No se verifica aún benchmark comparativo ni RAG groundedness real. No se instala ni descarga Ollama; si no existe modelo local, la ejecución Windows queda BLOCK/NOT_TESTED, no PASS simulado.
