---
doc_id: ADR-MP132-R02-07-GUIDED-AUTHORING
status: accepted-for-windows-candidate
version: 1.0.0
owner: product-owner
updated: 2026-10-17
related_sprint: R02_07_FROZEN_PRECODE_DOCUMENTS_SPRINT.md
---
# ADR — Authoring L integrado en Pre-code sin autoridad paralela

## Contexto

R02-06 demostró generación real de candidatos locales, comparaciones y revisión Owner, pero las tres propuestas D/L fueron insuficientes como documentos profesionales. Un laboratorio de comparación no constituye un ciclo de publicación. La premisa MP132 asigna la transformación semántica al modelo y los gates al núcleo determinístico.

## Decisión

En Pilot B la interfaz normal `/guided-sdlc/pre-code` incorpora `LOCAL_MODEL` opt-in para las primeras tres etapas. El LLM recibe `business_need` y, para Scope y Requirements, los artefactos upstream ya FROZEN. Usa instrucciones y estructura **diferentes por etapa**, sin red externa, tools ni aprobación automática. La respuesta se valida como JSON no confiable y se persiste en archivo Markdown candidato `.md` inmutable y sidecar JSON de metadatos; su edición humana crea revisión sucesora `.md`, sin sobrescribir el original. Cada versión conserva hash, modelo, referencia de fuente y contexto. El motor único `PreCodeWizardApplicationService` persiste el DRAFT y mantiene review/diff/approval/apply/freeze sin nuevo writer. El Owner puede editar y revalidar.

Un gate mínimo de completitud, anterior al plan de review, rechaza textos que no representan Product Vision, límites MVP o requisitos verificables. El gate no pretende verificar por sí solo verdad de negocio o grounding semántico profundo; el Owner y las evaluaciones sucesoras conservan esa responsabilidad.

## Boundaries y negativas

- `LOCAL_MODEL` no modifica permisos, egress, Git ni source por sí mismo.
- Modelo instalado local opt-in; sin fallback silencioso, sin API key, timeout y salida acotados.
- Solo proyecto Pilot B exacto y scope Owner; los demás proyectos mantienen el contrato anterior.
- Model/untrusted y revisión Owner no equivalen a aprobación documental.
- Cada FROZEN exige el apply aprobado de Pre-code; no repetir D/L laboratorio ni congelar el candidato R02-06.
- Source Registry de la plataforma registra esta ADR; los documentos finales pertenecen al workspace Pilot B y a su lifecycle pre-code, no a una autoridad de publicación paralela.

## Alternativas descartadas

1. Congelar los D seleccionados en R02-06: calidad semántica insuficiente.
2. Hacer al operador escribir `docs/`: viola control plane UI-first y bypass de approval.
3. Crear motor de publicación exclusivo Pilot B: duplica autoridad.
4. Exigir comparación D/L en cada etapa: coste cognitivo y no aporta a la construcción normal.

## Pruebas y continuación

`tests/test_mp132_r02_07_guided_semantic.py`; validación Windows con Ollama real, calidad y tres freezes gobernados, recuperación y fuente documental física. R02-08 expandirá cobertura/grounding medible, no relajará este gate.

## Reconciliación MP132 187

Una propuesta inicial L en Pre-code es la vía preferida; generación D disponible solo como utilidad diagnóstica, no alternativa semántica equivalente. Modelo externo E no habilitado. La revisión humana ocurre sobre Markdown y la autoridad final pertenece al lifecycle Pre-code ya existente. El quality gate es condición mínima, no certificación semántica autónoma.
