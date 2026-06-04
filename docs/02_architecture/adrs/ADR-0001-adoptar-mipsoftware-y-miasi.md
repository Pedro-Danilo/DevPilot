---
title: "ADR-0001 — Adoptar MIPSoftware y MIASI"
doc_id: "DEVPL-ADR-0001"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-02"
---
# ADR-0001 — Adoptar MIPSoftware y MIASI

## Estado

Accepted.

## Contexto

DevPilot Local será la primera plataforma aplicada construida después de consolidar MIPSoftware y MIASI. Su propósito es gestionar el ciclo de vida completo de proyectos de software con apoyo progresivo de agentes IA, sin depender de improvisación, nube obligatoria ni servicios pagos.

## Decisión

Adoptar:

- **MIPSoftware** como estándar general para producto, requerimientos, arquitectura, seguridad, pruebas, DevOps, operación, mantenimiento y retiro.
- **MIASI** como extensión obligatoria para agentes, LLMs, RAG, memoria, tool calling, evaluación agentic, policy gates, human approval y observabilidad agentic.

## Consecuencias positivas

- Todo avance queda gobernado por estándares documentados.
- El MVP puede transformar documentos en gates verificables.
- Todo agente queda sujeto a cards, policies, evals y trazas.
- DevPilot Local sirve como prueba real de MIPSoftware + MIASI.

## Consecuencias negativas

- Aumenta el trabajo documental inicial.
- El avance funcional es más lento al principio.
- Exige disciplina de revisión y trazabilidad.

## Reglas derivadas

- Ningún avance funcional fuerte debe omitir la baseline pre-code.
- Ningún agente ejecutor debe operar sin MIASI.
- Ninguna acción destructiva debe ejecutarse sin dry-run y aprobación.
- Toda decisión significativa debe registrarse como ADR.
