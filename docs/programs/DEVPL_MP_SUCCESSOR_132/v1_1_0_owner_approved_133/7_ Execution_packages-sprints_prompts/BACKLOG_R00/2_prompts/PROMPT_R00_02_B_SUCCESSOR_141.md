# PROMPT de implementación aprobada para COR-141 — solo R00-02 modalidad B

- **Estado:** OWNER_APPROVED por el mandato explícito del Owner de esta conversación.
- **Implementación:** únicamente `cor141.py` y su validación focal; Git mutable solamente después de inspección Windows PASS y confirmación exacta.

Usar como entradas de autoridad las tres evidencias COR-140 recibidas y los contratos literalmente consultados de MP132. No reinterpretar `OWNER_DECISION=PENDING` de COR-140 como aprobación de la opción A. No declarar PASS por el mero desarrollo local del operador.

Fases únicas consecutivas: `inspect -> prepare -> Owner confirma B -> migrate -> verify -> Owner confirma descarte -> retire -> package`. El primer switch deja MP detached, el segundo checkout MP en MAIN; ninguno usa `--ignore-other-worktrees` ni elimina datos ignored en MAIN. `retire` es irreversible respecto de ignored del linked y por tanto debe contar con consentimiento separado. Toda comprobación falla cerrada sin alterar refs/commits. Mantener la primera mutación de documentación/metadata Git reservada a R00-03.
