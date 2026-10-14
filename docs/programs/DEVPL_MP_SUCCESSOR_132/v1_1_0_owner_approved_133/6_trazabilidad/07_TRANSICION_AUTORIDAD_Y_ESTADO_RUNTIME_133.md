---
doc_id: DEVPL-MP-132-AUTHORITY-TRANSITION-133
status: OWNER_DECISION_EFFECTIVE_REPO_REBIND_PENDING
version: "1.0.0"
owner: "Ordóñez"
decision_date: "2026-10-13"
input_program_sha256: "d9743653686f6b232cdc6cd9e3983685f25a197b072848d53a200525b91647f8"
input_baseline_sha256: "fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8"
source_head: "8db5b44694abcced3231183e05731e732f5b8f24"
approval_method: "Declaración explícita del Owner en conversación"
---

# Diferencia entre decisión de programa y valores Git históricos

La aprobación programática y levantamiento global del STOP están **vigentes por acto expreso Owner**, pero el repositorio `8db5...` fue producido antes del acto. Sus banderas internas persistentes `mp_stop=ACTIVE`, estado MP-1B, Source Registry y Project State **no se modificaron** por crear este paquete. Por diseño deben reconciliarse como un incremento documental gobernado en R0 con auditoría focal previa, allowlist y test negativo de autoridad. Hasta entonces:

- La persona puede diseñar/auditar y solicitar autorización de nuevos incrementos del programa 132.
- No interpretar el flag viejo como autorización; si el servicio actual deniega la operación, **no sortearlo por fuera**: corregir la fuente de autoridad con un sucesor aprobado y test.
- No reabrir viejos prompts MP-1B ni usar endpoints de proveedor externo automáticamente.
- G5 y COR-130 no se reejecutan ni se editan en place; permanecen sellados.
- La migración de worktree B queda condicionada a preflight Windows y documentación de rollback.

El próximo incremento R0 puede implementar/publicar esa reconciliación de autoridad **después** de revisión focal y orden ejecutable independiente. No se crean aquí operadores ni se modifica Windows.
