"""R02-01: active documentation authority audit, no attempt to modernize historical timelines."""
from pathlib import Path
import json
import pytest
from devpilot_core.generation.product_definition import DeterministicProductDefinitionProvider
from devpilot_core.application.project_entry_planning_service import ProjectEntryPlanningApplicationService
from devpilot_core.workspace.project_layout import ProjectLayoutPlanner
ROOT=Path(__file__).resolve().parents[1]
BASE='docs/programs/DEVPL_MP_SUCCESSOR_132/v1_1_0_owner_approved_133/'
CURRENT='MP132-R02-01/AUDIT-DOC-DRIFT'

def data(name):return json.loads((ROOT/name).read_text(encoding='utf8'))

def test_active_state_in_lockstep_and_next_denied():
 p=data('.devpilot/project_state.json');s=data('.devpilot/docs_governance/source_registry.json')
 assert p['current_micro_sprint']==s['current_micro_sprint'] == 'MP132-R03-02/TECH-CONTEXT-PROFILE'
 assert p['next_micro_sprint']==s['next_micro_sprint'] == 'R03_03_NOT_AUTHORIZED'
 assert p['external_api_allowed'] is False
 assert len(s['documents'])>=1752 and s['summary']['documents_total']==len(s['documents'])
 assert len({(d['doc_id'],d['path']) for d in s['documents']})==len(s['documents'])

@pytest.mark.parametrize('section',[ '0_program/00_LEEME_INDICE_Y_ORDEN_132.md', '0_program/01_PROGRAMA_MAESTRO_132.md', '2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md', '2_contratos/PROGRAM_ACCEPTANCE_AND_MATURITY_MATRIX_132.md', '4_backlogs/BACKLOG_R01_132.md', '4_backlogs/BACKLOG_R02_132.md'])
def test_installed_active_program_explicit_scope(section):
 p=ROOT/BASE/section;text=p.read_text(encoding='utf8')
 assert '## Actualización operativa MP132 post-M1 — R02-01' in text
 assert 'R02-02' in text and 'OWNER_APPROVED_PROGRAM' in text
 assert 'status: "OWNER_APPROVED_PROGRAM"' in text

def test_source_registry_paths_referenced_and_no_added_entries():
 r=data('.devpilot/docs_governance/source_registry.json')
 paths={x['path']:x for x in r['documents']}
 for suffix in ('BACKLOG_R01_132.md','BACKLOG_R02_132.md'):
  key=next(k for k in paths if k.endswith('/'+suffix))
  assert (ROOT/key).is_file() and paths[key]['lifecycle']=='active'
 assert not any('R02_01_AUDIT' in d['path'] for d in r['documents'])

def test_reuse_existing_generation_and_planning_boundaries():
 assert DeterministicProductDefinitionProvider.provider_id=='devpilot-local'
 assert callable(ProjectEntryPlanningApplicationService.bootstrap_plan)
 assert callable(ProjectLayoutPlanner.preview)

def test_no_runtime_egress_or_pilot_mutation_claimed():
 p=data('.devpilot/project_state.json')
 for k in ('external_api_allowed','external_api_used','connector_write_enabled'):
  assert p[k] is False
 assert p['current_micro_sprint']=='MP132-R03-02/TECH-CONTEXT-PROFILE'  # current-active successor; R02-01 remains historical


def test_first_real_d_provider_candidate_is_non_mutative(tmp_path):
    from devpilot_core.generation import GenerationRequest, ProviderClass
    req=GenerationRequest(request_id='r02-d-preview', artifact_type='product-vision',
        profile_version='vision-v1',dependency_profile_version='deps-v1',
        upstream_hashes={'intake':'a'*64}, preferred_route='deterministic',
        allowed_routes=('deterministic',), policy_snapshot={'external_api':False},
        budget_snapshot={'max_cost_usd':0.0},context_reference='r02-fixture')
    provider=DeterministicProductDefinitionProvider(lambda m: '# Visión de '+str(m['business_need']))
    before=set(tmp_path.iterdir())
    candidate=provider.generate(req,{'stage_id':'product-vision','business_need':'inventario local'})
    assert candidate.payload['stage_id']=='product-vision'
    assert candidate.payload['content']=='# Visión de inventario local'
    assert candidate.origin.provider_class is ProviderClass.DETERMINISTIC
    assert candidate.provenance.network_used is False
    assert candidate.provenance.external_api_used is False
    assert candidate.provenance.cost_usd==0.0
    assert candidate.evaluation_summary['source_write'] is False
    assert set(tmp_path.iterdir())==before
    with pytest.raises(ValueError):
        provider.generate(req,{'stage_id':'unsupported','business_need':'x'})
