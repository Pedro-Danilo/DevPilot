"""C02-P4: provider gating, model readiness and no false durable attempts."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from devpilot_core.application import r03_04_local_authoring as local
from devpilot_core.modeling.contracts import ModelProviderConfig, ModelProviderKind


def _setup(monkeypatch, *, enabled=False, example=True, ok=True, models=None, truncated=False):
    config=ModelProviderConfig(provider_id='ollama',kind=ModelProviderKind.LOCAL,
        enabled=enabled,default_model='gemma3:4b',endpoint='http://127.0.0.1:11434')
    registry=SimpleNamespace(semantic_valid=True,used_example=example,
                             get=lambda provider_id:config if provider_id=='ollama' else None)
    monkeypatch.setattr(local.ProviderRegistry,'load',lambda *args,**kwargs:registry)
    health=SimpleNamespace(ok=ok,data={'models':['gemma3:4b'] if models is None else models,
               'summary':{'models_truncated':truncated}})
    monkeypatch.setattr(local.OllamaAdapter,'health',lambda self:health)


def test_architecture_local_example_allows_explicit_owner_gated_technology_call(tmp_path,monkeypatch):
    _setup(monkeypatch,enabled=False,example=True)
    assert isinstance(local.R0304LocalAuthoring(tmp_path)._local_adapter(None,'gemma3:4b',explicit_owner_action=True),local.OllamaAdapter)


def test_global_disable_remains_effective_without_authenticated_owner_action(tmp_path,monkeypatch):
    _setup(monkeypatch,enabled=False,example=False)
    with pytest.raises(ValueError,match='R0304_OLLAMA_OWNER_ACTION_REQUIRED'):
        local.R0304LocalAuthoring(tmp_path)._local_adapter(None,'gemma3:4b')


def test_explicit_disabled_provider_permits_only_narrow_owner_local_inference(tmp_path,monkeypatch):
    _setup(monkeypatch,enabled=False,example=False)
    adapter=local.R0304LocalAuthoring(tmp_path)._local_adapter(None,'gemma3:4b',explicit_owner_action=True)
    assert isinstance(adapter,local.OllamaAdapter)
    assert adapter.provider_config.enabled is False


def test_unavailable_ollama_does_not_reserve_in_progress_or_increment_attempt(tmp_path,monkeypatch):
    _setup(monkeypatch,ok=False)
    writer=local.R0304LocalAuthoring(tmp_path)
    with pytest.raises(ValueError,match='R0304_OLLAMA_NOT_RUNNING_OR_UNREACHABLE'):
        writer.infer(workspace_id='test-project',kind='technology',
            input_binding={'profile_version':'2.2.0'},prompt='fuente exacta',model='gemma3:4b',explicit_owner_action=True)
    folder=tmp_path/'outputs/mp132_r03_04/test-project'
    assert not list(folder.glob('*.current.json'))


def test_model_uninstalled_blocked_before_attempt(tmp_path,monkeypatch):
    _setup(monkeypatch,models=['qwen2.5:3b-instruct'])
    writer=local.R0304LocalAuthoring(tmp_path)
    with pytest.raises(ValueError,match='R0304_MODEL_NOT_INSTALLED:gemma3:4b'):
        writer.infer(workspace_id='test-project',kind='adr',
            input_binding={'profile_version':'2.2.0'},prompt='Contexto material',model='gemma3:4b',explicit_owner_action=True)
    assert not list((tmp_path/'outputs/mp132_r03_04/test-project').glob('*.current.json'))


def test_truncated_ollama_model_list_never_yields_false_missing_model(tmp_path,monkeypatch):
    _setup(monkeypatch,models=['another:small'],truncated=True)
    assert isinstance(local.R0304LocalAuthoring(tmp_path)._local_adapter(None,'gemma3:4b',explicit_owner_action=True),local.OllamaAdapter)


def test_frontend_selects_model_explicitly_and_filters_successor_for_preflight_failures():
    ui=(Path(__file__).resolve().parents[1]/'ui/web/src/pages/PreCodeWizardView.ts').read_text(encoding='utf-8')
    assert 'r0304ModelSelect' in ui
    assert 'r0304CustomModel' in ui and 'model:chosenModel()' in ui
    assert 'const modelAttemptBlocked=' in ui
    assert 'OLLAMA_EXPLICITLY_DISABLED' not in ui  # pre-inference refusal does not consume attempts
