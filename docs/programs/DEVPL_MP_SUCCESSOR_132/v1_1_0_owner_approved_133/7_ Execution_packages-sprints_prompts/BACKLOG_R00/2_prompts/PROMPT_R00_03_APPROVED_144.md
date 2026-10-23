---
doc_id: PROMPT-MP132-R00-03-144
version: 1.0.1
status: OWNER_APPROVED
linked_sprint: SPRINT-MP132-R00-03-144
approval_scope: BUILD_AND_TEST_WITH_SEPARATE_WINDOWS_APPLY_COMMIT_PUSH_GATES
---
# Prompt sucesor R00-03 — Implementación gobernada

Usar como contrato original `PROMPT_MP132_R00_03_PRIMER_BASELINE_AUTHORITY_REBIND_134.md`, ajustado por la evidencia COR-143: canonical worktree `D:\Projects\DevPilot_Local`, branch `evolution/multiprovider-v2`, HEAD 8db5b44694abcced3231183e05731e732f5b8f24.

Ejecutar únicamente el primer baseline de autoridad. Auditar bytes y SHA de 57 Markdown de Owner-133; publicar completos y sin edición; publicar las dos ADR S1/S2 de B; incorporar solo cambios de gobernanza en Source Registry, Project State, Overlay y pruebas focales de estado histórico/vigente. Rechazar HEAD distinto, workspace sucio, owner token incorrecto, index extraño y upstream divergente. Preparar/validar primero en clon aislado; usar plan/preimage exactos; autorizar `apply`, `commit` y `push` mediante confirmaciones separadas. Git archive + evidence ZIP con SHA/CRC y sin cambios en apps, servicios o runtime. No iniciar R00-04, R1, MP-1B, L/E o Pilot B.
