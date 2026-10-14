---
doc_id: DEVPL-MP-SUCCESSOR-132-00_FUENTES_VERIFICADAS_Y_METODO_132
title: "Fuentes de verdad consultadas literalmente, hashes y límites"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Fuentes de verdad consultadas literalmente, hashes y límites

## 1. Fuentes primarias leídas (contenido completo de archivos disponibles)

| Fuente | Consulta / alcance | SHA-256 ZIP |
|---|---|---|
| `DEVPL_MP_SUCCESSOR_131.zip` | 12/12 Markdown leídos literalmente; todos sustituidos por documentos 132 | `2be0e345c29f0794339acbb3ebd6ddd473480af1fea151a5737471e3fc86c947` |
| `DEVPL_MULTIPROVIDER_V2_1_APPROVED_PACKAGE-AJUSTAR.zip` | 101 Markdown de 114 entradas leídos literalmente, incluidos programa maestro, ADRs 001–010, perfiles y Pilot B | `b0136f245556b05687204e8ef4c3226547bb485d318e3485740e1e9d5fc94231` |
| `repo_MP_POST_G5_REBIND_8db5b44694ab_CLEAN(1).zip` | 4510 entradas ZIP/CRC; lectura de autoridad `project_state`, Source Registry, overlay, catálogos/contratos/rutas existentes | `fb9bd0755f702891cb0804c8e2ac03e6477e34ce4e11b77b449c8670b3d483b8` |
| `AUDITORIA_PROFUNDA_BASELINE_MP_POST_SYNC1_130.md` | Informe A–L y 14 hallazgos, leído | Ver archivo histórico/audit original |
| `ledger_v1_32_MP0F_REB117_INTEGRADO.md` | Histórico de 2773 líneas incl. Configuración, D05, MP0F, D06 y adenda G5, leído | Ver archivo original |
| `REBASELINE_P0_P3_117.zip` | ZIP 30 entradas, método/autoridad P0–P3, sin reactivar sus prompts | Archivo histórico aprobado |
| Salida Git decisión Owner `salida_consola_decision_git.txt` | Confirma Git común, worktrees, heads y vinculaciones; no valida nuevos estados dirty | Evidencia usuario de octubre 2026 |

## 2. Método para evitar sustitución simulada de fuentes

Se abrieron archivos originales como ZIP, `testzip()` verificó CRC, sus bytes Markdown se decodificaron íntegramente y se conservaron para cotejar IDs y contenido. Se tomó de 131 el contenido y se redistribuyeron **exactamente sus 66 IDs**; se comparan por script al cerrar el ZIP 132. Los ADRs del paquete MP v2.1 se contrastaron con la auditoría 130; no se declaran fuentes de autorización posterior automáticamente por haber sido históricamente `APPROVED`.

## 3. Qué NO se ha hecho

No se ha accedido a los worktrees Windows **en vivo** desde este entorno, ni ejecutado Ollama/LM Studio, APIs, browser Pilot B, agent handoffs reales o Full Regression. El snapshot `git archive` no contiene los objetos `.git` ni acredita remoto nuevo por sí solo. Ninguna recomendación de Git es una acción aplicada.

## 4. Autoridad y precisión

Fuente Git HEAD de entrada `8db5b44694abcced3231183e05731e732f5b8f24`; futuros artefactos requieren auditoría focal al HEAD real. La matriz de riesgo/ledger propone priorización, **no** altera estados de defectos históricos. Para cerrar sprints se necesita evidencia Windows; este paquete es sólo autoridad propuesta de organización del trabajo.
