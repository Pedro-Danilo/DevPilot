"""Focused R03_04-C02 tests: real local-adapter boundary, no source mutation."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from devpilot_core.application.r03_04_local_authoring import (
    R0304LocalAuthoring,
    compose_architecture,
    validate_adr,
    validate_technology,
)
from devpilot_core.modeling.contracts import ModelCallResult, ModelTask
from devpilot_core.application.pre_code_adr_bundle_service import ArchitectureAdrBundleService


TECH = """# Technology Options
## Drivers y restricciones
Ventas a domicilio, inventario consistente y aprobación humana de promociones.
## Opción T1 — API local y SQLite
- **Stack:** Python, SQLite y UI móvil responsiva.
- **Costo y licencias:** Licencias abiertas; infraestructura por evaluar.
- **Soporte:** Comunidad estable y documentación disponible.
- **Seguridad:** Sesión autenticada y autorización explícita para cambios.
- **Operación:** Respaldo periódico y funcionamiento local-first.
- **Riesgos:** Conflictos de sincronización entre dispositivos.
## Opción T2 — API Postgres
- **Stack:** Python, PostgreSQL y UI móvil responsiva.
- **Costo y licencias:** Licencias abiertas; hosting no cotizado.
- **Soporte:** Comunidad madura; requiere administrador básico.
- **Seguridad:** Roles por recurso y cifrado de conexiones.
- **Operación:** Backups y mantenimiento del servidor.
- **Riesgos:** Mayor complejidad para empresa unipersonal.
## Recomendación razonada
T1 minimiza costos y operación del MVP; evaluar sincronización antes de expandir a nube.
"""

ADR = """# ADR-001 — Persistencia local inicial
## Contexto
El MVP exige ventas y stock consistente en una empresa unipersonal sin sede comercial.
## Decisión
La opción T1, elegida por Owner, usa persistencia local transaccional con aprobación previa para efectos sensibles.
## Alternativas
La opción T2 usa PostgreSQL, cuya operación centralizada genera sobrecarga en el MVP.
## Consecuencias
Se reducen costos y complejidad; las futuras sincronizaciones necesitarán una decisión separada.
## Riesgos y mitigaciones
Resguardar copias, probar consistencia en ventas y auditar todas las acciones del agente.
"""

ARCH = """---
doc_id: ARCH_TEST
status: draft
---
# Architecture
## Contexto
Negocio de cuidado personal a domicilio.
## Tecnología y alternativas
Texto viejo.
## ADRs materiales
Texto antiguo.
## Riesgos
Integridad de inventario.
"""


class FakeOllama:
    def __init__(self, content: str):
        self.content = content
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        assert request.provider == "ollama"
        assert request.metadata["ollama_options"]["num_predict"] == 768
        return ModelCallResult(ok=True, provider="ollama", model=request.model or "gemma3:4b",
                               task=ModelTask.GENERATE, content=self.content,
                               external_api_used=False, tokens_estimated=330)


def test_two_domains_validate_without_product_specific_contract():
    assert validate_technology(TECH) == []
    assert validate_adr(ADR) == []
    assert validate_technology(TECH.replace('Ventas a domicilio, inventario consistente',
                                            'Reservas médicas, agenda consistente')) == []
    assert validate_adr(ADR.replace('ventas y stock consistente', 'agenda y turnos consistentes')) == []


def test_resumable_immutable_candidates_and_no_project_files(tmp_path: Path):
    writer = R0304LocalAuthoring(tmp_path)
    model = FakeOllama(TECH)
    args = dict(workspace_id='pilot-b', kind='technology', input_binding={'architecture_sha': 'a'*64},
                prompt='grounded prompt', model='gemma3:4b', adapter=model)
    first = writer.infer(**args)
    second = writer.infer(**args)
    assert first['candidate_sha256'] == second['candidate_sha256']
    assert first['status'] == 'COMPLETE'
    assert first['external_api_used'] is False
    assert model.calls == 1
    assert writer.bound_candidate('pilot-b', first) == TECH.strip()
    assert not (tmp_path / 'docs').exists()
    third = writer.infer(**{**args, 'successor': True})
    assert model.calls == 2 and third['attempt'] == 2


def test_complete_markdown_fence_is_unwrapped_without_false_block(tmp_path: Path):
    writer=R0304LocalAuthoring(tmp_path)
    model=FakeOllama('```markdown\n'+TECH.strip()+'\n```')
    received=writer.infer(workspace_id='pilot-c',kind='technology',input_binding={'architecture_sha':'c'*64},
                          prompt='grounded',model='gemma3:4b',adapter=model)
    assert received['status']=='COMPLETE'
    assert writer.bound_candidate('pilot-c',received)==TECH.strip()


def test_failed_generation_never_retried_implicitly(tmp_path: Path):
    writer = R0304LocalAuthoring(tmp_path)
    invalid = FakeOllama('# No hay opciones estructuradas')
    args = dict(workspace_id='pilot-a', kind='technology', input_binding={'architecture_sha': 'b'*64},
                prompt='grounded prompt', model='gemma3:4b', adapter=invalid)
    with pytest.raises(ValueError, match='R0304_GENERATED_STRUCTURE_BLOCK'):
        writer.infer(**args)
    with pytest.raises(ValueError, match='EXPLICIT_SUCCESSOR_REQUIRED'):
        writer.infer(**args)
    assert invalid.calls == 1
    replacement = FakeOllama(TECH)
    result = writer.infer(**{**args, 'adapter': replacement, 'successor': True})
    assert result['status'] == 'COMPLETE' and replacement.calls == 1


def test_architecture_reconciliation_preserves_other_sections_and_hashes():
    t = hashlib.sha256((TECH.strip() + '\n').encode()).hexdigest()
    a = hashlib.sha256((ADR.strip() + '\n').encode()).hexdigest()
    merged = compose_architecture(ARCH, TECH, 'T1', ADR, t, a)
    assert '## Riesgos\nIntegridad de inventario.' in merged
    assert f'`{t}`' in merged and f'`{a}`' in merged
    assert 'Texto viejo' in merged and 'Texto antiguo' in merged  # preservar Owner
    assert compose_architecture(merged, TECH, 'T1', ADR, t, a) == merged
    with pytest.raises(ValueError, match='CANDIDATE_SELECTION_DRIFT'):
        compose_architecture(ARCH, TECH, 'T3', ADR, t, a)


def test_rejects_ungoverned_or_missing_decision_fields():
    assert validate_technology(TECH.replace('- **Seguridad:**', '- **Configuración:**'))
    assert validate_adr(ADR.replace('## Consecuencias', '## Texto libre'))
    assert validate_technology(TECH + '\nTODO: instalar automáticamente sin aprobación')


def test_frozen_architecture_projects_exact_two_governed_documents(tmp_path: Path):
    platform=tmp_path/'platform';project=tmp_path/'independent_domain'
    folder=project/'docs'/'02_architecture'
    (folder/'adrs').mkdir(parents=True)
    generator=R0304LocalAuthoring(platform)
    options=generator.infer(workspace_id='another-domain',kind='technology',
                            input_binding={'architecture_sha':'a'*64},prompt='x',model='gemma3:4b',adapter=FakeOllama(TECH))
    decision=generator.infer(workspace_id='another-domain',kind='adr',
                             input_binding={'technology_sha':options['candidate_sha256'],'selected':'T1'},
                             prompt='y',model='gemma3:4b',adapter=FakeOllama(ADR))
    draft_sha='7'*64
    source=(ARCH.replace('status: draft','status: frozen')+f'\n<!-- Technology {options["candidate_sha256"]} ADR {decision["candidate_sha256"]} -->\n').encode()
    (folder/'architecture_document.md').write_bytes(source)
    published_sha=hashlib.sha256(source).hexdigest()
    arch={'mode':'LOCAL_MODEL','status':'FROZEN','content_sha256':draft_sha,
          'approved_sha256':published_sha,'approval_id':'approval-genuine-test',
          'derivation':{'technology_selection':{'architecture_sha256':draft_sha,
             'technology_sha256':options['candidate_sha256'],
             'adr_sha256':decision['candidate_sha256'],'selected_option_id':'T1'}}}
    state={'stages':{'architecture':arch},'r03_04_authoring':{
        'technology':options,'adr':decision,'selected_option_id':'T1',
        'reconciled_architecture_sha256':draft_sha}}
    service=ArchitectureAdrBundleService(platform)
    projected=service._expected_from_frozen(workspace_root=project,workspace_id='another-domain',arch=arch,state=state)
    assert isinstance(projected,dict)
    assert len(projected['adrs'])==2
    assert {x['relative_path'].split('/')[-1] for x in projected['adrs']} >= {'technology_options.md'}
    assert any(x['relative_path'].endswith('.md') and '/adrs/' in x['relative_path'] for x in projected['adrs'])
    assert not (folder/'technology_options.md').exists()
    # The DRAFT digest is a separate authority from the frozen source-byte digest.
    state['r03_04_authoring']['reconciled_architecture_sha256']='0'*64
    blocked=service._expected_from_frozen(workspace_root=project,workspace_id='another-domain',arch=arch,state=state)
    assert not isinstance(blocked,dict)
    assert not blocked.ok
