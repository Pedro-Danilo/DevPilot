"""UX01-A read-only contract: honest levels, Python preference, scoped handoff."""
from __future__ import annotations

from unittest import TestCase

from devpilot_core.application.r03_04_quality_contract import (
    CONTRACT, TECH_CRITERIA, assess_artifact, handoff_packet,
    logical_sha256, scoped_section_refinement, technology_context_requirements,
)

SOURCES = {
    "product-vision": "Una persona opera ventas locales sin instalaciones físicas.",
    "scope": "MVP productos, registro de ventas y bajo stock; agentes solo asesoría.",
    "requirements": (
        "RF-001 registra productos. RF-002 guarda ventas y descontar stock de "
        "modo transaccional. RNF-001 exige uso local y autorización del Owner "
        "para acciones sensibles. Ninguna publicación sin aprobación humana."
    ),
}
_CASE = TestCase()


def refs() -> dict[str, str]:
    return {name: logical_sha256(text) for name, text in SOURCES.items()}


TECH = """# Technology Options
## Drivers y restricciones
RF-002 exige coherencia de ventas e inventario, con una sola operadora local.
## Opción T1 — Python local
- **Stack:** Python, SQLite y UI ligera, monolito modular.
- **Costo y licencias:** licencias abiertas, costo de soporte local limitado.
- **Soporte:** comunidad estable y equipo familiarizado con Python.
- **Seguridad:** separación de roles y aprobación de cambios sensibles.
- **Operación:** un proceso local, copia y restauración verificables.
- **Riesgos:** vigilar crecimiento real antes de migrar persistencia.
## Opción T2 — Python servidor local
- **Stack:** Python, PostgreSQL y UI web separada.
- **Costo y licencias:** abierto, mayor coste operativo del servidor.
- **Soporte:** comunidad estable y mantenimiento de servidor adicional.
- **Seguridad:** controles equivalentes y gestión separada de acceso.
- **Operación:** dos procesos, soporte y respaldo más complejos.
- **Riesgos:** mayor carga para una persona sin ventaja MVP inmediata.
## Recomendación razonada
Preferir T1 por complejidad y mantenimiento menores en el MVP actual; T2
se evaluaría al crecer concurrencia verificada y demanda centralizada.
"""

ADR = """# ADR-001 — Tecnología para ventas locales
## Contexto
RF-002 requiere persistir venta y existencias para una sola propietaria.
## Decisión
El Owner elige T1 Python con SQLite para el MVP local y su carga actual.
## Alternativas
T2 se descarta por operación de servidor adicional sin beneficio comprobado.
## Consecuencias
Positivo: mantenimiento menor. Consecuencia negativa: límites al crecer
la concurrencia, que requiere una migración planificada.
## Riesgos y mitigaciones
Copias verificadas y transacciones atómicas protegen frente a corrupción.
## Reversibilidad
Revisar al superar la concurrencia prevista y comprobar costos de migración.
"""


def audit(kind: str, body: str, **kwargs):
    return assess_artifact(
        kind, body, frozen_sources=SOURCES, verified_source_hashes=refs(),
        candidate_id="candidate-ux01-a", runtime_status="DRAFT",
        **kwargs,
    )


def finding_ids(result: dict) -> set[str]:
    return {row["id"] for row in result["findings"]}


def test_physical_eol_representation_is_not_frozen_source_drift():
    sources = {name: text.replace("\n", "\r\n") for name, text in SOURCES.items()}
    result = assess_artifact(
        "technology_options", TECH.replace("\n", "\r\n"),
        frozen_sources=sources, verified_source_hashes=refs(),
        candidate_id="c1", runtime_status="DRAFT",
    )
    assert not any(x["id"] == "UX01_A_FROZEN_SOURCE_DRIFT" for x in result["findings"])
    assert result["candidate_sha256"] == logical_sha256(TECH)


def test_frozen_source_hash_mismatch_is_real_block():
    bad = refs()
    bad["requirements"] = "0" * 64
    result = assess_artifact(
        "technology_options", TECH, frozen_sources=SOURCES,
        verified_source_hashes=bad, candidate_id="c2", runtime_status="DRAFT",
    )
    assert result["structural_disposition"] == "BLOCK"
    assert result["handoff_ready"] is False
    assert "UX01_A_FROZEN_SOURCE_DRIFT" in finding_ids(result)


def test_structure_is_not_professional_certification():
    result = audit("technology_options", TECH)
    assert result["schema_id"] == CONTRACT
    assert result["structural_disposition"] == "STRUCTURALLY_VALID"
    assert result["quality_level"] == "REVIEW_REQUIRED"
    assert result["handoff_ready"] is False
    assert result["professional_reviewed"] is False
    assert result["owner_review_required"] is True
    assert not result["external_api_used"] and not result["source_mutations_performed"]


def test_missing_project_factors_remain_unknown_not_hallucinated():
    context = technology_context_requirements({"team_capacity": "1 Owner"})
    assert set(context["factors"]) == set(TECH_CRITERIA)
    assert context["factors"]["team_capacity"]["status"] == "GROUNDED"
    assert context["factors"]["users_and_data_volume"]["value"] == "UNKNOWN"
    assert context["policy"]["default_ecosystem"] == "Python"


def test_non_python_without_comparative_advantage_gets_review_not_auto_block():
    body = TECH.replace("Python", "Java").replace("SQLite", "H2").replace(
        "PostgreSQL", "Oracle")
    result = audit("technology_options", body)
    assert "UX01_A_PYTHON_COMPARISON_MISSING" in finding_ids(result)
    assert result["structural_disposition"] == "REVIEW_REQUIRED"


def test_overbuilt_stack_without_project_driver_gets_review():
    body = TECH.replace(
        "Python, PostgreSQL y UI web separada",
        "Python, Kubernetes, microservicios y serverless cloud",
    )
    result = audit("technology_options", body)
    assert "UX01_A_OVERENGINEERING_RISK" in finding_ids(result)
    assert result["structural_disposition"] == "REVIEW_REQUIRED"


def test_adr_praise_only_is_not_a_material_decision():
    weak = """# ADR-001 — Elegir T1
## Contexto
T1 es fácil y útil para todos, con muchas ventajas genéricas.
## Decisión
Seleccionamos T1 porque es la mejor opción disponible hoy.
## Alternativas
No se analizan porque T1 es suficientemente buena.
## Consecuencias
Todas las consecuencias son excelentes para el producto.
## Riesgos y mitigaciones
No hay riesgos de importancia que debamos analizar.
"""
    result = audit("adr", weak, selected_option_id="T1")
    assert "UX01_A_MATERIAL_SECTION_MISSING" in finding_ids(result)
    assert "UX01_A_ADR_NEGATIVE_TRADEOFF_MISSING" in finding_ids(result)
    assert result["quality_level"] == "REVIEW_REQUIRED"


def test_adr_conflicting_owner_option_is_material_block():
    result = audit("adr", ADR.replace("elige T1", "elige T2"), selected_option_id="T1")
    assert result["structural_disposition"] == "BLOCK"
    assert "UX01_A_SELECTED_OPTION_CONFLICT" in finding_ids(result)


def test_explicit_prohibition_is_not_a_false_block():
    safe = ADR + "\nNo publicar automáticamente sin aprobación del Owner.\n"
    result = audit("adr", safe, selected_option_id="T1")
    assert "UX01_A_UNAUTHORIZED_MUTATION" not in finding_ids(result)
    assert "UX01_A_HUMAN_AUTHORITY_CONFLICT" not in finding_ids(result)


def test_positive_unauthorized_action_is_blocked():
    unsafe = ADR + "\nPublicar automáticamente sin autorización del Owner.\n"
    result = audit("adr", unsafe, selected_option_id="T1")
    assert "UX01_A_UNAUTHORIZED_MUTATION" in finding_ids(result)


def test_handoff_packet_supports_section_only_improvement():
    result = audit("adr", ADR, selected_option_id="T1")
    packet = handoff_packet(result, ADR, locked_section_ids=("decision",))
    assert packet["requires_authenticated_owner_review"]
    assert packet["quality_level"] == "REVIEW_REQUIRED"
    assert packet["markdown"] == ADR
    assert packet["section_tasks"] == []
    original = {s["section_id"]: s["body_sha256"] for s in result["sections"]}
    upgraded = scoped_section_refinement(
        packet, section_id="riesgos-y-mitigaciones",
        replacement="Guardar backups probados semanalmente y restaurar una copia "
                    "en ambiente aislado antes de nuevas versiones.",
    )
    new_result = audit("adr", upgraded, selected_option_id="T1")
    assert any(s["body_sha256"] != original[s["section_id"]]
               for s in new_result["sections"] if s["section_id"] == "riesgos-y-mitigaciones")
    assert all(s["body_sha256"] == original[s["section_id"]]
               for s in new_result["sections"] if s["section_id"] != "riesgos-y-mitigaciones")
    with _CASE.assertRaisesRegex(ValueError, "UX01_A_REFINEMENT_TARGET_DENY"):
        scoped_section_refinement(packet, section_id="decision", replacement="Cambiar a T2.")


def test_handoff_denies_opaque_rewrite_and_stale_digest():
    result = audit("technology_options", TECH)
    packet = handoff_packet(result, TECH)
    with _CASE.assertRaisesRegex(ValueError, "UX01_A_REFINEMENT_CONTENT_INVALID"):
        scoped_section_refinement(
            packet, section_id="recomendacion-razonada",
            replacement="## Reescribir todo\nCambiar proyecto y decisiones Owner.",
        )
    with _CASE.assertRaisesRegex(ValueError, "UX01_A_HANDOFF_SOURCE_DRIFT"):
        handoff_packet(result, TECH + "\nCambiado sin nueva revisión.")


def test_missing_architecture_sections_require_review_not_false_pass():
    result = audit(
        "architecture", "# Architecture\n## Propósito\nDescripción vaga de veinte caracteres.",
    )
    assert "UX01_A_MATERIAL_SECTION_MISSING" in finding_ids(result)
    assert result["quality_level"] == "REVIEW_REQUIRED"
    assert result["professional_reviewed"] is False


def test_comparison_matrix_is_symmetric_without_made_up_costs():
    result = audit("technology_options", TECH, project_context={"team_capacity": "1 Owner"})
    rows = result["technology_comparison"]
    assert [x["option_id"] for x in rows] == ["T1", "T2"]
    assert set(rows[0]["axes"]) == set(rows[1]["axes"])
    assert set(v["status"] for row in rows for v in row["axes"].values()) <= {
        "UNKNOWN", "TEXT_PRESENT_UNVERIFIED",
    }
    assert result["technical_context"]["factors"]["concurrency"]["value"] == "UNKNOWN"


def test_non_python_option_needs_comparison_even_when_python_alternative_exists():
    body = TECH.replace(
        "- **Stack:** Python, PostgreSQL y UI web separada.",
        "- **Stack:** Java, Oracle y UI web separada.",
    )
    result = audit("technology_options", body)
    assert "UX01_A_NONPYTHON_ADVANTAGE_UNVERIFIED" in finding_ids(result)
    assert result["structural_disposition"] == "REVIEW_REQUIRED"


def test_runtime_overrules_fictitious_document_approval():
    result = audit("adr", "status: approved\n" + ADR, selected_option_id="T1")
    assert "UX01_A_FICTITIOUS_APPROVAL" in finding_ids(result)
    assert result["structural_disposition"] == "BLOCK"
    assert not handoff_packet(result, "status: approved\n" + ADR)["eligible_for_external_handoff"]


def test_quality_provenance_phase_and_unknown_markers_remain_auditable():
    result = audit(
        "adr", ADR.replace("Copias verificadas", "UNKNOWN: Copias verificadas"),
        document_id="ADR-001", revision_id="v3", author_actor="ollama",
        model_id="local-model", owner_phase="before_owner", selected_option_id="T1",
    )
    assert result["document_id"] == "ADR-001"
    assert result["provenance"]["model_id"] == "local-model"
    assert result["owner_phase"] == "before_owner"
    assert result["assumptions_and_unknowns"]
    packet = handoff_packet(result, ADR.replace("Copias verificadas", "UNKNOWN: Copias verificadas"))
    assert packet["quality_snapshot_phase"] == "before_owner"
    assert packet["provider_transfer_boundary"].startswith("OFFLINE_ONLY")


def test_blocked_source_cannot_authorize_section_refinement():
    hashes = refs()
    hashes["scope"] = "bad" * 21 + "b"
    result = assess_artifact(
        "adr", ADR, frozen_sources=SOURCES, verified_source_hashes=hashes,
        candidate_id="blocked", runtime_status="DRAFT", selected_option_id="T1",
    )
    packet = handoff_packet(result, ADR)
    assert not packet["eligible_for_external_handoff"]
    with _CASE.assertRaisesRegex(ValueError, "UX01_A_HANDOFF_BLOCKING_ISSUES"):
        scoped_section_refinement(packet, section_id="alternativas", replacement="Nueva nota.")
