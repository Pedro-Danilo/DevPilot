"""Focal tests of ID-neutral model adapter proposal boundary; no network used."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from devpilot_core.application.story_general_provider import GeneralStoryProvider
from devpilot_core.application.story_implementation_candidate_service import StoryImplementationCandidateApplicationService
from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.modeling.contracts import ModelProviderConfig, ModelProviderKind
from test_devpl_gsdlc_13_d_05_general_provider import _rf003_fixture, ROOT


class StubModelRouter:
    def __init__(self, content: str):
        self.content = content
        self.registry = SimpleNamespace(get=lambda name: ModelProviderConfig(provider_id=name, kind=ModelProviderKind.LOCAL,
                enabled=True, default_model="test-local", endpoint="http://127.0.0.1:11434"))

    def generate(self, *, prompt: str, provider: str, model=None):
        assert 'id_for_trace_only' in prompt
        assert 'selected_source' in prompt
        return CommandResult(command='model generate', ok=True, exit_code=ExitCode.PASS, message='PASS',
            data={'result': {'provider': provider, 'model': 'test-local', 'external_api_used': False,
                'content': self.content, 'cost_estimate_usd': 0.0}, 'summary': {}})


def _propose(tmp_path: Path, monkeypatch, payload: str, provider: str = 'ollama'):
    workspace, resolver = _rf003_fixture(tmp_path, story_id="story-catalog-218")
    svc = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver,
                code_workbench=CodeWorkbenchApplicationService(ROOT, context_resolver=resolver))
    monkeypatch.setenv('DEVPILOT_STORY_LLM_PROVIDER',provider)
    by_path = svc.code.list_sources().data['sources']
    general = GeneralStoryProvider(svc, model_router=StubModelRouter(payload))
    return general._local_proposal(story_id='story-catalog-218', title='Generar resumen de ventas',
            requirement={'content': 'La aplicación calcula resumen de ventas por período'},
            acceptance={'content': 'Retorna un resumen observable y verificable'},test_intent={},
            namespace='inventory_sales_local_greenfield',source_rows=by_path,architecture='frozen fastapi sqlite',story_context={})


def _body():
    return '''"""Sales summary helper.\n\nPurpose: Aggregate governed local sales.\nResponsibilities: Return a sales summary.\nBoundaries: No external IO.\nTraceability: story-catalog-218.\n"""\n\ndef sum_sales(rows):\n    return sum(rows)\n'''


def _test_body():
    return '''"""Sales summary test.\n\nPurpose: Verify sales summary.\nResponsibilities: Test bounded aggregation.\nBoundaries: No network.\nTraceability: story-catalog-218.\n"""\n\nfrom src.inventory_sales_local_greenfield.application.sales_summary import sum_sales\n\ndef test_sales_summary():\n    assert sum_sales([1, 2]) == 3\n'''


def test_local_model_generic_selected_story_without_id_switch(tmp_path: Path, monkeypatch):
    payload=json.dumps({'files':[{'operation':'CREATE','target_path':'src/inventory_sales_local_greenfield/application/sales_summary.py','content':_body(),'artifact_role':'application','rationale':'New generic summary'},
                               {'operation':'CREATE','target_path':'tests/test_sales_summary.py','content':_test_body(),'artifact_role':'test','rationale':'Acceptance'}]})
    result=_propose(tmp_path,monkeypatch,payload)
    assert isinstance(result,tuple)
    files,quality,_,meta=result
    assert len(files)==2 and quality['ready_for_draft_materialization']
    assert meta['underlying_provider']=='ollama'
    assert meta['route_kind']=='enabled-local-model-adapter'


@pytest.mark.parametrize('path', ['../secret.py','src/../../evil.py','docs/fake.py','src\\evil.py','/tmp/pwn.py'])
def test_local_model_rejects_unsafe_path(tmp_path: Path,monkeypatch,path):
    result=_propose(tmp_path,monkeypatch,json.dumps({'files':[{'operation':'CREATE','target_path':path,'content':_body()},
                                                                    {'operation':'CREATE','target_path':'tests/test_sum.py','content':_test_body()}]}))
    assert not isinstance(result,tuple) and not result.ok


def test_model_rejects_bad_json(tmp_path:Path,monkeypatch):
    result=_propose(tmp_path,monkeypatch,'```python\nanything\n```')
    assert not isinstance(result,tuple) and not result.ok


def test_local_model_rejects_edit_of_undisclosed_source(tmp_path:Path,monkeypatch):
    result=_propose(tmp_path,monkeypatch,json.dumps({'files':[{'operation':'EDIT','target_path':'src/inventory_sales_local_greenfield/other.py','content':_body()},
                                                                    {'operation':'CREATE','target_path':'tests/test_sum.py','content':_test_body()}]}))
    assert not isinstance(result,tuple) and not result.ok


def test_local_route_default_is_off(tmp_path:Path,monkeypatch):
    workspace,resolver=_rf003_fixture(tmp_path,story_id='story-other-288')
    svc=StoryImplementationCandidateApplicationService(ROOT,context_resolver=resolver,
                code_workbench=CodeWorkbenchApplicationService(ROOT, context_resolver=resolver))
    monkeypatch.delenv('DEVPILOT_STORY_LLM_PROVIDER',raising=False)
    general=GeneralStoryProvider(svc)
    result=general.propose(story_id='story-other-288',title='Reporte de ventas',requirement={'content':'Reporte estadístico'},
              acceptance={},test_intent={},namespace='inventory_sales_local_greenfield',
              source_rows=svc.code.list_sources().data['sources'],architecture='',story_context={})
    assert not isinstance(result,tuple) and not result.ok
    assert result.findings[0].id=='GSDLC13D05_LOCAL_ROUTE_REQUIRED_BLOCK'
