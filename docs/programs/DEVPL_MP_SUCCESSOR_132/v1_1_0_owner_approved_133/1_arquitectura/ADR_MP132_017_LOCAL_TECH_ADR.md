---
doc_id: MP132-ADR-017
title: R03-04 autoría asistida de Technology Options y ADR material
status: APPROVED_BY_OWNER_2026_10_25_IMPLEMENTATION_PENDING_WINDOWS
version: 1.0.0
owner: Owner DevPilot
baseline: df6a5dcbb6eeb112008db1373d2e975cbc60b18f
---

# ADR-MP132-017 — Autoría L y publicación gobernada de decisiones técnicas

## Contexto

C00 proporcionó una proyección diagnóstica sin acciones de generación, C01 cerró el defecto visual y el Owner aprobó expresamente C02. Redactar alternativas y ADR manualmente contradice la promesa del asistente SDLC. Architecture DRAFT ya estaba en `APPROVAL_REQUIRED`: un plan antiguo no puede convertirse silenciosamente en autoridad para nuevas decisiones.

## Decisión

Se incorpora un generador Ollama local de **Technology Options** (2–3 opciones, tradeoffs, costos desconocidos explícitos) y **una ADR material** fundada en opción elegida por el Owner. Candidatos separados son inmutables y sus recibos de intento sobreviven entre ejecuciones. La selección se reconcilia creando Architecture DRAFT sucesor y anulando el plan anterior; nunca se altera FROZEN. Después del review/approval/apply/freeze normal de Architecture, se reutiliza el escritor companion multiarchivo previamente protegido para un plan exacto con `docs/02_architecture/technology_options.md` y `docs/02_architecture/adrs/ADR-001-*.md`. Su aprobación y aplicación están sujetas al PolicyEngine y recibos durables existentes.

## Alternativas

- Solo redactar ADR dentro de Architecture: descartado por incumplir separación documental y autoría asistida.
- Generar y escribir archivos directamente con Ollama: descartado porque un candidato no equivale a decisión Owner ni autoriza source writes.
- Construir un segundo publisher/approval: descartado por duplicar gobernanza y fragilidad de reanudación.

## Consecuencias

El Owner realiza una sola elección material explícita entre opciones, además de los approvals de publicación ya existentes. La misma UI Guided/Expert muestra candidatos reales y estado; no automatiza instalación, scaffold, gasto, nube ni publicación. El pipeline conserva evaluación semántica humana y evidencia. R03_07 conserva la ampliación futura de su lifecycle.

## Riesgos y mitigaciones

Riesgo de límite de tokens/salida incompleta del modelo local: una llamada acotada, validación mínima de estructura, recibo BLOCK y sucesora explícita sin reintento silencioso. Riesgo de estados inconsistentes: hash de candidata y DRAFT, bloqueo por preimage drift y plan idempotente. Riesgo de falsos BLOCK LF/CRLF: en operador se comparan contenidos Git normalizados o hashes lógicos; los hashes aprobados de un documento publicado se comprueban contra bytes de su fuente real, no se equiparan al hash del DRAFT.
