from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.workspace.runtime_project_context import activate_project_runtime_context, bind_persisted_project_runtime

ROOT = Path(__file__).resolve().parents[1]
PILOT = (
    'Es una empresa unipersonal dedicada a la comercialización de una línea de productos de bienestar y cuidado personal, '
    'como cosméticos, productos para adelgazar, potenciadores y productos rejuvenecedores, que opera sin instalaciones físicas '
    'y realiza sus ventas mediante entrega a domicilio. La empresa necesita una aplicación sencilla que le permita administrar '
    'los productos disponibles, controlar sus existencias, registrar las ventas y actualizar automáticamente el inventario cada '
    'vez que se realice una venta, así como consultar información básica sobre las ventas e identificar oportunamente los '
    'productos con bajo nivel de stock para facilitar su reposición y mantener la continuidad de la operación.'
)


def _platform(tmp_path: Path) -> Path:
    platform = tmp_path / 'platform'
    shutil.copytree(
        ROOT,
        platform,
        ignore=shutil.ignore_patterns('.git', '.venv', 'node_modules', 'outputs', '.pytest_cache', '__pycache__', '*.pyc', '*.db', '*.db-*', 'dist'),
    )
    return platform


def _workspace(tmp_path: Path) -> Path:
    ws = tmp_path / 'workspaces' / 'approval-recheck-fixture'
    for rel in [
        '.devpilot', 'docs', 'docs/standards', 'docs/00_product', 'docs/01_requirements',
        'docs/02_architecture', 'docs/02_architecture/adrs', 'docs/03_security', 'docs/04_quality',
    ]:
        (ws / rel).mkdir(parents=True, exist_ok=True)
    (ws / '.devpilot/project.yaml').write_text(
        'project_id: approval-recheck-fixture\n'
        'project_name: "Approval Recheck Fixture"\n'
        f'business_need: "{PILOT}"\n'
        'technology_decision_status: deferred-to-architecture\n'
        'model_policy:\n  baseline: "mock-no-api"\n  local_model: "optional-opt-in"\n  external_api: "approval-provenance-only"\n'
        'project_constraints:\n  local_first: true\n  cloud_required: false\n  operator_project_writes_allowed: false\n',
        encoding='utf-8',
    )
    (ws / '.devpilot/workspace-registration.json').write_text(
        json.dumps({'workspace_id': ws.name, 'project_id': ws.name, 'root_path': str(ws.resolve())}, indent=2) + '\n',
        encoding='utf-8',
    )
    subprocess.run(['git', 'init', '-q'], cwd=ws, check=True)
    subprocess.run(['git', 'config', 'user.email', 'fixture@example.invalid'], cwd=ws, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Fixture'], cwd=ws, check=True)
    subprocess.run(['git', 'add', '.'], cwd=ws, check=True)
    subprocess.run(['git', 'commit', '-qm', 'baseline'], cwd=ws, check=True)

    # Mirrors 13-C-01-retest-04: an earlier governed attempt already materialized
    # Product Vision, but that file is intentionally not committed to the baseline.
    (ws / 'docs/00_product/product_vision.md').write_text(
        '---\ndoc_id: "old-product-vision"\nstatus: "draft"\n---\n# Product Vision\n\n## Problema\n\nBaseline anterior.\n',
        encoding='utf-8',
    )
    return ws


def _client(tmp_path: Path, monkeypatch):
    platform = _platform(tmp_path)
    ws = _workspace(tmp_path)
    activate_project_runtime_context(platform, ws, allowed_roots=(ws,))
    for name in [
        'DEVPILOT_ALLOWED_WORKSPACE_ROOTS', 'DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT',
        'DEVPILOT_UI_WORKSPACE_REGISTRY_PATH', 'DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH',
    ]:
        monkeypatch.delenv(name, raising=False)
    assert bind_persisted_project_runtime(platform).applied
    auth = AuthApplicationService(platform)
    auth.bootstrap_owner(username='approval.owner', display_name='Approval Owner', password='ApprovalOwner!2026')
    client = TestClient(create_app(platform, api_token='approval-recheck-token', auth_service=auth))
    origin = {'origin': 'http://127.0.0.1:5173'}
    login = client.post('/api/v1/auth/login', json={'username': 'approval.owner', 'password': 'ApprovalOwner!2026'}, headers=origin)
    assert login.status_code == 200, login.text
    csrf = str(client.cookies.get('devpilot_csrf') or '')
    headers = {**origin, 'X-DevPilot-CSRF': csrf}
    return platform, ws, client, headers


def _prepare_approval_required(client: TestClient, headers: dict[str, str]):
    first = client.post(
        '/api/v1/guided-sdlc/pre-code/stages/product-vision/draft',
        json={'mode': 'DEVPL_MOCK', 'content': ''}, headers=headers,
    )
    assert first.status_code == 200, first.text
    content = first.json()['data']['stage']['draft_content']
    edited = content.replace('## Visión', '## Visión\n\nRevisión editorial del Owner.', 1)
    saved = client.post(
        '/api/v1/guided-sdlc/pre-code/stages/product-vision/draft',
        json={'mode': 'DEVPL_MOCK', 'content': edited, 'semantic_model': None}, headers=headers,
    )
    assert saved.status_code == 200, saved.text
    review = client.post('/api/v1/guided-sdlc/pre-code/stages/product-vision/review', json={}, headers=headers)
    assert review.status_code == 200, review.text
    plan = review.json()['data']['plan']
    assert plan['document']['operation'] == 'modify'
    assert str(plan['document']['document_id']).startswith('artifact:')
    return plan


def test_existing_governed_artifact_modify_can_request_approval(tmp_path: Path, monkeypatch) -> None:
    _, _, client, headers = _client(tmp_path, monkeypatch)
    _prepare_approval_required(client, headers)

    requested = client.post(
        '/api/v1/guided-sdlc/pre-code/stages/product-vision/approval-request',
        json={'reason': 'Owner reviewed the exact Product Vision diff.'}, headers=headers,
    )
    assert requested.status_code == 200, requested.text
    payload = requested.json()
    assert payload['ok'] is True
    assert payload['data']['pre_code']['approval_id'].startswith('APPROVAL-')
    assert all(row['id'] != 'WORKSPACE_DOCUMENT_ID_BLOCK' for row in payload.get('findings', []))


def test_stale_artifact_plan_is_conflict_not_false_forbidden(tmp_path: Path, monkeypatch) -> None:
    _, ws, client, headers = _client(tmp_path, monkeypatch)
    _prepare_approval_required(client, headers)

    # External source drift after immutable plan creation must still fail closed,
    # but it is a state/concurrency conflict rather than an authorization denial.
    target = ws / 'docs/00_product/product_vision.md'
    target.write_text(target.read_text(encoding='utf-8') + '\nExternal drift.\n', encoding='utf-8')

    requested = client.post(
        '/api/v1/guided-sdlc/pre-code/stages/product-vision/approval-request',
        json={'reason': 'Attempt approval after source drift.'}, headers=headers,
    )
    assert requested.status_code == 409, requested.text
    ids = {row['id'] for row in requested.json().get('findings', [])}
    assert 'UOC004_OPTIMISTIC_CONCURRENCY_STALE_BLOCK' in ids
    assert 'UOC005_PRE_APPROVAL_RECHECK_BLOCK' in ids
