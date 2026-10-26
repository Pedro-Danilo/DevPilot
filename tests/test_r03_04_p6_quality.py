"""Regression tests for P5's incomplete Technology recommendation and P6 state guards."""
from __future__ import annotations

from devpilot_core.application.r03_04_local_authoring import validate_technology, technology_prompt

OPTION_1 = """## Opción T1 — Local sencilla
- **Stack:** Python y base transaccional local.
- **Costo y licencias:** Licencias abiertas, costos de soporte aún por evaluar.
- **Soporte:** Comunidad y documentación técnica disponibles.
- **Seguridad:** Roles y aprobaciones antes de afectar inventario.
- **Operación:** Un proceso local, respaldos comprobables y restauración.
- **Riesgos:** Sincronizar dispositivos necesitará una revisión.
"""
OPTION_2 = """## Opción T2 — Centralizada
- **Stack:** Python y PostgreSQL en servidor privado.
- **Costo y licencias:** Licencias abiertas; hospedaje NOT_AVAILABLE.
- **Soporte:** Comunidad y soporte comercial opcional.
- **Seguridad:** Accesos por rol, TLS y registros de auditoría.
- **Operación:** Infraestructura administrada y monitoreo.
- **Riesgos:** Mayor dependencia de red y administración.
"""
DRIVERS = """El producto gestiona inventario y ventas a domicilio para una sola persona.
Las escrituras sensibles necesitan aprobación y la operación debe ser recuperable."""
RECOMMENDATION = (
    "Recomiendo T1 por su menor mantenimiento inicial frente a T2, "
    "sin sacrificar transacciones locales; la sincronización futura se "
    "evaluará separadamente antes de introducir servicios remotos."
)


def candidate(recommendation: str = RECOMMENDATION) -> str:
    return (
        "# Technology Options\n## Drivers y restricciones\n"
        + DRIVERS + "\n" + OPTION_1 + OPTION_2
        + "## Recomendación razonada\n" + recommendation
    )


def test_incomplete_p5_recommendation_never_passes():
    truncated = (
        "Se recomienda la Opción T1 (Arquitectura Microservicios Tradicional) "
        "para garantizar el"
    )
    findings = validate_technology(candidate(truncated))
    assert any(row["id"] == "R0304_TECH_RECOMMENDATION_INCOMPLETE" for row in findings)


def test_complete_different_options_can_pass_structural_gate():
    assert validate_technology(candidate()) == []
    assert validate_technology(candidate(RECOMMENDATION[:-1])) != []


def test_options_without_a_real_choice_are_rejected():
    assert any(x["id"] == "R0304_TECH_RECOMMENDATION_INCOMPLETE"
               for x in validate_technology(candidate("Elegir alternativas.")))


def test_prompt_requests_project_fit_without_mandating_one_language():
    prompt = technology_prompt(
        "Empresa Unipersonal", "# Architecture\n## Contexto\nLocal-first",
        {"product-vision": "ventas para una persona",
         "scope": "productos y control de stock",
         "requirements": "aprobaciones humanas y recuperación"},
    )
    assert "proporcional" in prompt
    assert "local-first" in prompt
    assert "Python" in prompt
    assert "No impongas" in prompt
    assert "Máximo 768" in prompt
