---
doc_id: "PROMPT-DEVPL-UX-P1-BOUNDED-CORRECTIVE-TEMPLATE"
title: "Prompt template — DEVPL-UX-P1 bounded corrective"
status: "approved-template"
version: "1.1.0"
---

# Prompt — UX-P1 bounded corrective

Contexto obligatorio: un acceptance checkpoint de GSDLC-13 está pausado por un finding reproducible de DevPilot.

Actúa como **ingeniero de DevPilot**, no como autor del proyecto greenfield. Analiza literalmente el Run Packet, el finding y la última authority Windows-validada. Determina causa raíz y modifica únicamente DevPilot si corresponde.

Reglas:

- preservar first-attempt evidence;
- no escribir ni reparar externamente contenido normal del proyecto greenfield;
- scope mínimo ligado al finding;
- state-aware/reentrant;
- Test Impact + focal tests + affected browser checkpoint + authority/RBAC/approval/evidence contracts pertinentes;
- no Full en 13-B..13-D;
- una sola guía `.md` Windows si existe source delta;
- promoción fast-forward-only y remote sync antes de la siguiente mutación DevPilot;
- devolver `resume_checkpoint` exacto.

Si el problema no requiere source mutation, entregar adjudicación/procedimiento sin crear repo/commit artificial.
