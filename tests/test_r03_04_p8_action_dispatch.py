"""P8: verify the real dispatcher -> facade -> pre-code service boundary.

P7 tested the inner service and missed the extra `content` kwarg on the
ApplicationService facade. These tests deliberately enter at the dispatcher.
"""
from __future__ import annotations

import inspect

import pytest

from devpilot_core.application.services import ApplicationService, _operation_dispatch
from devpilot_core.interfaces.api.routers.guided_sdlc import TechnologyActionBody


class _PreCodeSpy:
    def __init__(self):
        self.calls = []

    def technology_action(self, **kwargs):
        self.calls.append(kwargs)
        return {"forwarded": True, "action": kwargs["action"]}


class _FacadeWithTestWizard(ApplicationService):
    """Override a read-only lazy property; do not assign to the property."""

    @property
    def pre_code_wizard(self):
        return self._test_wizard


def _facade_with_spy(spy):
    facade = object.__new__(_FacadeWithTestWizard)
    facade._test_wizard = spy
    return facade


@pytest.mark.parametrize("action", [
    "generate_options", "owner_revise_options", "select_option",
    "generate_adr", "owner_revise_adr", "reconcile",
])
def test_every_technology_action_survives_the_full_dispatch_boundary(action):
    spy = _PreCodeSpy()
    facade = _facade_with_spy(spy)
    content = "# Technology Options\nTexto de revisión Owner con caracteres: ñ, á, é"
    request = TechnologyActionBody(action=action, content=content,
                                   option_id="T1", model="gemma3:4b")
    payload = {"action": request.action, "option_id": request.option_id,
               "content": request.content, "model": request.model,
               "successor": request.successor, "actor": "owner-id",
               "actor_role": "owner", "session_principal": "owner-id",
               "effective_roles": ["owner"], "workspace_scopes": ["pilot-b"]}
    result = _operation_dispatch(facade)["guided_sdlc.pre_code.technology_action"](payload)
    assert result == {"forwarded": True, "action": action}
    assert len(spy.calls) == 1
    assert spy.calls[0]["content"] == content
    assert spy.calls[0]["workspace_scopes"] == ["pilot-b"]
    assert spy.calls[0]["effective_roles"] == ["owner"]


def test_action_facade_explicitly_forwards_content_and_keeps_defaults():
    signature = inspect.signature(ApplicationService.guided_pre_code_technology_action)
    assert "content" in signature.parameters
    assert signature.parameters["content"].default == ""
    spy = _PreCodeSpy()
    facade = _facade_with_spy(spy)
    result = facade.guided_pre_code_technology_action(
        action="owner_revise_options", actor="owner-id", actor_role="owner",
        session_principal="owner-id", effective_roles=["owner"],
        workspace_scopes=["pilot-b"], content="## Owner\nPython + SQLite")
    assert result["forwarded"] is True
    assert spy.calls[0]["content"] == "## Owner\nPython + SQLite"
    facade.guided_pre_code_technology_action(
        action="reconcile", actor="owner-id", actor_role="owner",
        session_principal="owner-id", effective_roles=["owner"],
        workspace_scopes=["pilot-b"])
    assert spy.calls[-1]["content"] == ""
