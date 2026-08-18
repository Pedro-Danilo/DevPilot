from pathlib import Path
from fastapi.testclient import TestClient
from devpilot_core.interfaces.api.app import create_app

ORIGIN={"Origin":"http://127.0.0.1:5173"}
PASSWORD="correct horse battery staple"

def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(root=tmp_path, api_token="legacy-local-token"))

def test_first_run_login_session_logout_and_safe_status(tmp_path: Path) -> None:
    c=client(tmp_path)
    assert c.get('/api/v1/auth/bootstrap/status').json()['first_run_required'] is True
    boot=c.post('/api/v1/auth/bootstrap/owner',json={'username':'owner.local','display_name':'Local Owner','password':PASSWORD},headers=ORIGIN)
    assert boot.status_code==201 and 'devpilot_session' in c.cookies and 'devpilot_csrf' in c.cookies
    status=c.get('/api/v1/auth/session/status').json(); assert status['state']=='active' and status['secret_exposed'] is False
    session=c.get('/api/v1/auth/session'); assert session.status_code==200 and session.json()['session']['principal']['roles']==['owner']
    csrf=str(c.cookies.get('devpilot_csrf'))
    logout=c.post('/api/v1/auth/logout',headers={**ORIGIN,'X-DevPilot-CSRF':csrf}); assert logout.status_code==200
    after=c.get('/api/v1/auth/session/status').json(); assert after['state'] in {'missing','revoked'} and 'token' not in str(after).lower()

def test_invalid_credentials_csrf_and_local_login_rate_limit(tmp_path: Path) -> None:
    c=client(tmp_path); c.post('/api/v1/auth/bootstrap/owner',json={'username':'owner.local','display_name':'Owner','password':PASSWORD},headers=ORIGIN)
    csrf=str(c.cookies.get('devpilot_csrf')); c.post('/api/v1/auth/logout',headers={**ORIGIN,'X-DevPilot-CSRF':csrf})
    bad=c.post('/api/v1/auth/login',json={'username':'owner.local','password':'bad'},headers=ORIGIN); assert bad.status_code==401
    statuses=[]
    for _ in range(11): statuses.append(c.post('/api/v1/auth/login',json={'username':'owner.local','password':'bad'},headers=ORIGIN).status_code)
    assert 429 in statuses
    fresh=client(tmp_path); ok=fresh.post('/api/v1/auth/login',json={'username':'owner.local','password':PASSWORD},headers=ORIGIN); assert ok.status_code==200
    denied=fresh.post('/api/v1/auth/logout',headers={**ORIGIN,'X-DevPilot-CSRF':'wrong'}); assert denied.status_code==403

def test_ui_source_has_human_session_route_guard_and_no_normal_token_form() -> None:
    root=Path(__file__).resolve().parents[1]; main=(root/'ui/web/src/main.ts').read_text(encoding='utf-8');
    for marker in ['renderLoginView','renderFirstRunOwnerView','renderSessionBanner','authBootstrapStatus','authSessionStatus','location.replace']:
        assert marker in main
    assert 'Token local' not in main and 'Aplicar token' not in main

def test_normal_authenticated_shell_pages_do_not_require_legacy_token_to_bootstrap() -> None:
    root=Path(__file__).resolve().parents[1]
    pages=[
        'ui/web/src/pages/ReportsView.ts','ui/web/src/pages/TracesView.ts','ui/web/src/pages/ApprovalCenterView.ts',
        'ui/web/src/pages/WorkspaceDocumentsView.ts','ui/web/src/pages/JobsView.ts','ui/web/src/pages/QualityOperationsView.ts',
    ]
    for rel in pages:
        text=(root/rel).read_text(encoding='utf-8')
        assert 'if (tokenProvider())' not in text and 'if(tokenProvider())' not in text, rel


def test_auth_ui_route_registry_is_separate_from_operational_dry_run_registry() -> None:
    import json
    root=Path(__file__).resolve().parents[1]
    operational=json.loads((root/'.devpilot/interfaces/ui_route_contract_registry.json').read_text(encoding='utf-8'))
    auth=json.loads((root/'.devpilot/identity/auth_ui_route_contract_registry.json').read_text(encoding='utf-8'))
    from devpilot_core.schemas import SchemaValidator
    schema_result=SchemaValidator(root).validate_payload(schema='SCHEMA-DEVPL-GSDLC-02-E-AUTH-UI-ROUTE-CONTRACT-REGISTRY-V1',payload=auth,instance_label='memory:auth-ui-route-registry')
    assert schema_result.ok is True, schema_result.to_dict()
    frozen_03b=json.loads((root/'.devpilot/interfaces/ui_route_contract_registry_gsdlc03b_at_close.json').read_text(encoding='utf-8'))
    assert len(frozen_03b['routes']) == 10
    assert len(operational['routes']) >= 10
    assert {r['route_id'] for r in auth['routes']} == {'ui.login','ui.first-run-owner','ui.account-role'}
    assert auth['summary']['routes_total'] == 3
    assert auth['summary']['remote_execution_allowed_total'] == 0
    assert auth['summary']['external_api_allowed_total'] == 0
    for route in auth['routes']:
        assert route['local_only'] is True
        assert route['remote_execution_allowed'] is False
        assert route['external_api_allowed'] is False
