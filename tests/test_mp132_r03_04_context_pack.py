"""P3: huge legitimate FROZEN docs must not fail before local Ollama inference."""
from __future__ import annotations

import hashlib

import pytest

from devpilot_core.application.r03_04_context_pack import (
    ADR_PROMPT_LIMIT, TECH_PROMPT_LIMIT, PROFILE, adr_context,
    technology_context, excerpt,
)
from devpilot_core.application.r03_04_local_authoring import (
    adr_prompt, technology_prompt,
)


def _large_docs():
    vision = ("# Visión del producto\n## Usuarios y valor\n"
              "Empresa unipersonal, ventas a domicilio y gestión móvil con supervisión humana.\n"
              + "## Beneficios\n" + "Beneficiarios necesitan confianza, privacidad y bajo costo.\n" * 240)
    scope = ("# MVP Scope\n## Incluido\nGestión de productos, inventario y ventas a domicilio.\n"
             "## Exclusiones\nNo instalar ni comprar automáticamente; recomendaciones de agente requieren aprobación humana.\n"
             + "## Flujos\n" + "La dueña registra ventas y debe confirmar decisiones sensibles.\n" * 240)
    requirements = ("# Requisitos\n## Funcionales\nRF-01: Toda venta descuenta stock una sola vez y genera comprobante.\n"
                    "RF-02: Agentes solo sugieren promociones, nunca publican sin permiso Owner.\n"
                    "## No funcionales\nRNF-01: El sistema debe operar local-first y preservar trazabilidad.\n"
                    + "RNF-02: La privacidad y respaldo son obligatorios para datos de clientes.\n" * 880)
    architecture = ("# Architecture\n## Componentes\nAPI local Python, catálogo de productos y ventas consistentes.\n"
                    "## Tecnología y alternativas\nMotor transaccional y seguridad por roles.\n"
                    "## ADRs materiales\nDecisión de persistencia debe tener aprobación Owner.\n"
                    + "## Integraciones y riesgos\n" + "Inventario y ventas necesitan transacciones y auditoría.\n" * 420)
    return architecture, {'product-vision':vision,'scope':scope,'requirements':requirements}


def test_oversized_frozen_sources_use_honest_bounded_context_without_rewriting():
    architecture,frozen=_large_docs()
    originals=[architecture,*frozen.values()]
    snapshots=[hashlib.sha256(s.encode()).hexdigest() for s in originals]
    assert sum(len(s) for s in originals)>56000
    context,receipt=technology_context(architecture,frozen)
    prompt=technology_prompt('Pilot B',architecture,frozen)
    assert len(prompt)<=TECH_PROMPT_LIMIT
    assert len(context)<len(''.join(originals))
    assert receipt['profile']==PROFILE and receipt['excerpted_source_count']>=1
    assert all(sha in prompt for sha in snapshots)
    assert 'EXTRACTO EXPLÍCITO' in prompt and 'no infieras ausencia' in prompt
    assert 'RF-01' in prompt and 'RNF-01' in prompt
    assert 'ventas a domicilio' in prompt.lower()
    assert originals==[architecture,*frozen.values()]
    assert prompt==technology_prompt('Pilot B',architecture,frozen)


def test_small_context_preserves_entire_source_content():
    architecture='# Architecture\n## Riesgos\nSin publicar cambios sin permiso Owner.'
    frozen={'product-vision':'# Visión\nNegocio pequeño.',
            'scope':'# Alcance\nSólo ventas e inventario.',
            'requirements':'# Requisitos\nRF-01: Actualización de stock transaccional.'}
    prompt=technology_prompt('Proyecto general',architecture,frozen)
    for original in [architecture,*frozen.values()]:
        assert original in prompt
    _,receipt=technology_context(architecture,frozen)
    assert receipt['excerpted_source_count']==0


def test_adr_prompt_bounded_preserves_selected_option_and_full_source_hash():
    architecture,_=_large_docs()
    technology=("# Technology Options\n## Drivers y restricciones\nMVP local.\n"
                "## Opción T1 — SQLite\n- **Stack:** SQLite y Python.\n- **Riesgos:** sincronización futura.\n"
                + "- **Operación:** respaldo y auditoría diaria.\n" * 160
                + "## Opción T2 — PostgreSQL\n- **Stack:** PostgreSQL y Python.\n- **Riesgos:** operación más compleja.\n"
                + "- **Seguridad:** mínimo privilegio, confirmación Owner.\n" * 200
                + "## Recomendación razonada\nT1 conviene para MVP pequeño, T2 es alternativa cuando crece el servicio.\n")
    context,receipt=adr_context(architecture,technology,'T2')
    prompt=adr_prompt(architecture,technology,'T2')
    assert len(prompt)<=ADR_PROMPT_LIMIT
    assert '<SELECTED>T2</SELECTED>' in prompt
    assert 'PostgreSQL' in context
    assert hashlib.sha256(technology.encode()).hexdigest() in prompt
    assert hashlib.sha256(architecture.encode()).hexdigest() in prompt
    assert receipt['context_sha256']


def test_large_indivisible_source_fails_honestly_before_model_call():
    with pytest.raises(ValueError,match='R0304_CONTEXT_UNEXTRACTABLE'):
        excerpt('requirements','x'*90000,budget=2300)


def test_upstream_change_changes_context_hash_deterministically():
    arch,frozen=_large_docs()
    _,one=technology_context(arch,frozen)
    modified=dict(frozen)
    modified['scope'] += '\n## Cambio material\nRestricción de inventario y seguridad adicional.'
    _,two=technology_context(arch,modified)
    assert one['context_sha256']!=two['context_sha256']
    assert one['sources'][2]['full_sha256']!=two['sources'][2]['full_sha256']
