# R03_04 — propuesta Owner de autoría asistida para Technology y ADR

**Estado:** PROPUESTA_MATERIAL_PENDIENTE_OWNER. **Base:** R03_03 C11 `df6a5dcbb6eeb112008db1373d2e975cbc60b18f` + R03_04 C00 sin commit + correctivo visual C01. **No ejecutar esta propuesta con el operador C01.**

## 1. Hallazgo que cambia el alcance

El sprint R03_04 autorizado fue rebindeado con una restricción explícita: proyección Technology/ADR de solo lectura, sin generación de documentos ni materialización standalone, con generación/lifecycle más adelante. La evidencia Windows confirma que ese contrato técnico *funciona*, pero no satisface la expectativa funcional del Owner: el modelo L debe redactar borradores, mientras que el Owner decide sobre sus consecuencias. El estado de implementación actual es, por tanto, `BLOCK_MATERIAL_AUTHORING_GAP`; no es una exigencia cosmética.

## 2. Propiedad de módulo y documentos

Los tres son del **módulo Architecture** en DevPilot y son tres artefactos relacionados, **no el mismo documento**:

| Artefacto | Responsabilidad | Escritor inicial | Autoridad final |
| --- | --- | --- | --- |
| Architecture Document | Componentes, límites, drivers, datos y decisiones de diseño | L local o import/manual autorizado | Lifecycle Architecture existente |
| Technology Options | Compara hasta tres stacks viables; recomienda con costos, licencias, soporte, seguridad y operación; registra incógnitas | L local (con ModelAdapter y upstream FROZEN) | Selección Owner dentro de revisión Architecture |
| ADR material | Registra razón de cada elección material, alternativas descartadas y consecuencias | L local con candidato inmutable derivado de la elección | Mismo plan/review/approval multiarchivo Architecture |

Los documentos derivados deben residir en el workspace del proyecto dentro del árbol de Architecture: `docs/02_architecture/technology_options.md` y `docs/02_architecture/adrs/ADR-NNN-*.md`, conservando identificadores, hashes y vínculos. Los paths son una **propuesta de diseño**, no rutas que C01 vaya a escribir.

## 3. Flujo futuro propuesto (C02 funcional, sujeto a aprobación Owner)

1. **Preflight de contexto:** utilizar el workspace/PESP activo, Vision/Scope/Requirements FROZEN y Architecture guardado; validar hashes/upstream/decisiones aprobadas. Un `APPROVAL_REQUIRED` histórico no se borra ni se interpreta como permiso para escribir source. Al incorporar archivos derivados se prepara una **alternativa sucesora explícita de revisión**, preservando el plan/approval antiguo y marcándolo stale para el nuevo conjunto; nunca se reutiliza un plan monofichero como si autorizara múltiples postimágenes.
2. **«Generar alternativas tecnológicas con modelo local»:** invocar una vez el ModelAdapter L configurado, con presupuesto acotado, generando candidata Markdown separada, recibos de modelo/latencia y hasta tres opciones argumentadas. Sin Stack predeterminado ni instalar/provisionar software. Si el output se corta, preservar segmentos y fallar de modo recuperable.
3. **Revisión Owner:** mostrar un comparador accesible Guided/Expert de opciones y recomendación; exigir solo selección de riesgo material, sin forzar aceptación de la recomendación. El Owner puede solicitar una alternativa sucesora explícita; no hay regeneración silenciosa ni acción externa.
4. **«Proponer ADRs materiales con modelo local»:** crear borradores ADR a partir de las decisiones seleccionadas y drivers de Architecture; materialidad evaluada por perfil/PESP. Si no existe decisión material, documentar `NOT_APPLICABLE` con razón verificable y no inventar archivos.
5. **Un solo plan/diff de revisión:** preparar los archivos Architecture + Technology Options + ADR(s) como **un conjunto inmutable de cambios**, reutilizando PolicyEngine, Approval Center y lifecycle; enlazar plan hash, aprobación, versionado, paths y fuente. La aprobación cubre únicamente ese conjunto exacto. El approval `APPROVAL_REQUIRED` anterior se mantiene como antecedente, **no** como autorización del plan ampliado. No reutilizar ciegamente un approval de un plan monofichero para aplicar otros archivos.
6. **Apply/FROZEN y reentrada:** escribir a workspace exclusivamente desde la API gobernada luego de approval exacto; mantener recibos y comparación bytes para documentos inmutables, equivalencia Git para source text; soportar recuperación sin doble inferencia. El sucesor material y propagación de impacto siguen bajo R03_07.

## 4. Implementación y pruebas mínimas

- Extender el `pre_code_adr_bundle_service` que hoy se limita a `DEVPL_MOCK` C02; **no crear** un publicador/Approval Center paralelo. Generalizar a `LOCAL_MODEL` sólo después de contar con Architecture FROZEN o plan multiarchivo preparado con autoridad equivalente.
- Nuevo perfil `technology_options`/`material_adr` con esquema/contraejemplos. Modelo L genera candidatos; reglas deterministas solo prueban integridad, contradicciones verificables y permisos; juicio profesional incierto=`REVIEW_REQUIRED`, jamás `PASS` por longitud o palabras clave.
- Frontend: tarjetas abatibles para cobertura, opciones y ADR, presentación comparable de criterios/riesgos, una selección explícita Owner, borradores y diff visual; mensajes de BLOCK comprensibles.
- Pruebas focales: dos dominios, tres alternativas o menos, recomendación sin evidencia, costo `NOT_AVAILABLE`, instalación no autorizada, sin ADR material, aprobación falsificada, conflictos de hash FROZEN, reentrada tras interrupción y no cambio de Pilot B sin Owner.
- Medir duración/unidades/llamadas; costos locales no medidos=`NOT_AVAILABLE`, no inventar USD 0 como costo computacional demostrado.

## 5. Frontera de decisión

La aprobación previa del R03_04 de **solo lectura** no cubre este nuevo generador y plan multiarchivo. Se solicita **una única decisión Owner material**: ampliar R03_04 para implementar este flujo antes de cerrarlo, ajustando sprint/prompt y, si el diseño de approval multiarchivo cambia, añadiendo ADR de arquitectura. No se solicita autorización por tarjetas, capturas ni cambios de copy. Hasta dicha decisión: conservar C00/C01, no aprobar el artefacto de Pilot B, no `git commit/push` ni crear un baseline R03_04 falsamente cerrado.
