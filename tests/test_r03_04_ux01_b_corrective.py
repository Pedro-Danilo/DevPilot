"""Focal B0 freshness and actionable boilerplate checks; no real model calls."""
from copy import deepcopy

import pytest

from test_r03_04_ux01_b_pipeline import pipeline, SOURCES
from devpilot_core.application.r03_04_quality_contract import (
    candidate_quality, export_candidate_handoff, logical_sha256,
)
from test_mp132_r03_04_c02_p5_flow import TECH, ADR, LocalModel


@pytest.mark.parametrize('target', [
    'select_option', 'generate_adr', 'reconcile', 'owner_revise_options', 'owner_revise_adr',
])
def test_material_b0_change_denies_stale_action_without_mutating_candidates(pipeline, target):
    svc, state, row, action, responses, calls, project = pipeline
    assert action('generate_options').ok
    if target in ('generate_adr', 'reconcile', 'owner_revise_adr'):
        assert action('select_option', option_id='T1').ok
    if target in ('reconcile', 'owner_revise_adr'):
        assert action('generate_adr').ok
    before = deepcopy(state)
    receipts = {p: p.read_bytes() for p in (svc.root/'outputs').rglob('*') if p.is_file()}
    count = len(calls)
    (project/'.devpilot/project.yaml').write_text(
        'project_name: Fixture\nbusiness_need: Reservas y matrículas de formación presencial.\n', encoding='utf-8')
    result = action(target, option_id='T1', content=TECH if target == 'owner_revise_options' else ADR)
    assert not result.ok and result.message == 'UX01_B_BUSINESS_NEED_DRIFT'
    assert len(calls) == count and state == before
    assert {p: p.read_bytes() for p in (svc.root/'outputs').rglob('*') if p.is_file()} == receipts


@pytest.mark.parametrize('change', ['crlf', 'whitespace', 'editorial_metadata'])
def test_b0_equivalent_representation_allows_selection_adr_reconcile_and_export(pipeline, change):
    svc, state, row, action, responses, calls, project = pipeline
    assert action('generate_options').ok
    config = project/'.devpilot/project.yaml'
    if change == 'crlf':
        config.write_bytes(config.read_bytes().replace(b'\n', b'\r\n'))
    elif change == 'whitespace':
        config.write_text('business_need: "  Inventario   y ventas locales.  "\n', encoding='utf-8')
    else:
        config.write_text('# Comentario editorial\nproject_name: Nombre corregido\n'
                          'business_need: Inventario y ventas locales.\n', encoding='utf-8')
    assert action('export_handoff', artifact_kind='technology_options').ok
    assert action('select_option', option_id='T1').ok
    assert action('generate_adr').ok
    assert action('reconcile').ok
    assert action('export_handoff', artifact_kind='adr').ok
    assert len(calls) == 2


def test_reconcile_checks_adr_b0_even_when_technology_is_current(pipeline):
    svc, state, row, action, responses, calls, project = pipeline
    assert action('generate_options').ok
    assert action('select_option', option_id='T1').ok
    assert action('generate_adr').ok
    state['r03_04_authoring']['adr']['quality']['current']['business_need']['text'] = 'B0 anterior.'
    original = row['content']
    result = action('reconcile')
    assert not result.ok and result.message == 'UX01_B_BUSINESS_NEED_DRIFT'
    assert row['content'] == original and len(calls) == 2


def test_missing_b0_provenance_requires_explicit_successor(pipeline):
    svc, state, row, action, responses, calls, project = pipeline
    assert action('generate_options').ok
    state['r03_04_authoring']['technology']['quality']['current'].pop('business_need')
    result = action('select_option', option_id='T1')
    assert not result.ok and result.message == 'UX01_B_BUSINESS_NEED_UNVERIFIED'
    assert len(calls) == 1


@pytest.mark.parametrize('target', ['generate_options', 'generate_adr'])
def test_b0_change_during_inference_preserves_receipt_without_binding_result(pipeline, monkeypatch, target):
    svc, state, row, action, responses, calls, project = pipeline
    if target == 'generate_adr':
        assert action('generate_options').ok
        assert action('select_option', option_id='T1').ok
    before = deepcopy(state)
    class ChangingModel:
        def generate(self, request):
            (project/'.devpilot/project.yaml').write_text('business_need: Un dominio distinto.\n', encoding='utf-8')
            return LocalModel(TECH if target == 'generate_options' else ADR).generate(request)
    monkeypatch.setattr(type(svc.technology_authoring), '_local_adapter', lambda *a, **k: ChangingModel())
    result = action(target)
    assert not result.ok and result.message == 'UX01_B_BUSINESS_NEED_DRIFT'
    assert state == before
    assert list((svc.root/'outputs/mp132_r03_04/isolated').glob('*attempt-1.json'))


def test_b0_change_requires_new_options_without_destroying_prior_receipts(pipeline):
    svc, state, row, action, responses, calls, project = pipeline
    assert action('generate_options').ok
    first = deepcopy(state['r03_04_authoring']['technology'])
    config = project/'.devpilot/project.yaml'
    config.write_text('business_need: Ventas locales y reservas de productos.\n', encoding='utf-8')
    assert not action('generate_options').ok and len(calls) == 1
    responses.insert(0, TECH)
    assert action('generate_options', successor=True).ok
    assert action('select_option', option_id='T1').ok
    assert state['r03_04_authoring']['technology']['candidate_id'] != first['candidate_id']
    assert svc.technology_authoring.bound_candidate('isolated', first) == TECH.strip()


def test_adr_cache_is_bound_to_b0_when_successor_options_have_identical_markdown(pipeline):
    svc, state, row, action, responses, calls, project = pipeline
    assert action('generate_options').ok
    assert action('select_option', option_id='T1').ok
    assert action('generate_adr').ok
    old = deepcopy(state['r03_04_authoring']['adr'])
    (project/'.devpilot/project.yaml').write_text(
        'business_need: Ventas locales y reservas de productos.\n', encoding='utf-8')
    responses.extend([TECH, ADR])
    assert action('generate_options', successor=True).ok
    assert action('select_option', option_id='T1').ok
    assert action('generate_adr').ok
    current = state['r03_04_authoring']['adr']
    assert len(calls) == 4 and current['candidate_id'] != old['candidate_id']
    assert current['quality']['current']['business_need']['text'] == 'Ventas locales y reservas de productos.'
    assert svc.technology_authoring.bound_candidate('isolated', old) == ADR.strip()
    assert action('reconcile').ok


@pytest.mark.parametrize('kind,headings', [
    ('architecture', ['Componentes y límites', 'Datos y consistencia']),
    ('technology_options', ['Drivers y restricciones', 'Recomendación razonada']),
    ('adr', ['Contexto', 'Riesgos y mitigaciones']),
])
def test_explicit_generic_sections_get_scoped_repair_tasks_without_certification(kind, headings):
    text = '# Fixture\n' + '\n'.join(
        f'## {heading}\nRF-001: propuesta pendiente de justificar con detalles del dominio; UNKNOWN.'
        for heading in headings)
    report = candidate_quality(kind, text, frozen=SOURCES,
        hashes={k: logical_sha256(v) for k, v in SOURCES.items()}, candidate_id='generic', epoch='e', actor='fixture')
    packet = export_candidate_handoff(report, text)
    tasks = [t for t in packet['section_tasks'] if t['finding_id'] == 'UX01_B_SECTION_BOILERPLATE']
    assert len(tasks) == 2 and all(t['section_id'] != 'GLOBAL' and t['instruction'] for t in tasks)
    assert report['current']['quality_level'] == 'REVIEW_REQUIRED'
    assert not report['current']['handoff_ready'] and not packet['professional_reviewed']


def test_repeated_prose_without_pending_marker_still_has_localized_repair():
    text = '# ADR\n## Contexto\nUna solución adecuada para las necesidades generales de este proyecto.\n'
    text += '## Consecuencias\nUna solución adecuada para las necesidades generales de este proyecto.\n'
    report = candidate_quality('adr', text, frozen=SOURCES,
        hashes={k: logical_sha256(v) for k, v in SOURCES.items()}, candidate_id='repeat', epoch='e', actor='fixture')
    assert len([f for f in report['current']['findings'] if f['id'] == 'UX01_B_SECTION_BOILERPLATE']) == 2
