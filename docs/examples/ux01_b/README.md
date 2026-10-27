# Muestras UX01-B — exclusivamente offline

Todos los documentos son fixtures sintéticos anonimizados. No son salida de Ollama real ni documentos del Pilot B. La elección T1 es un dato de prueba; no registra aprobación Owner real.

`classifications.json` identifica calidad REVIEW_REQUIRED de Architecture, Options y ADR. `handoff.json` exporta ADR íntegro, fuentes, lineage y límites. `offline_proposal.json` y `adr_refined_offline.md` cambian únicamente riesgos-y-mitigaciones. No se llama a ningún proveedor ni se atribuye calidad profesional.

Reproducir desde la raíz del candidato: `python scripts/ux01_b_offline_example.py`. Las pruebas de integración ejercitan adicionalmente los generadores reales con transporte Ollama simulado y fixtures temporales.
