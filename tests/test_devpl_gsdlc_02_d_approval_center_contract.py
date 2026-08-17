from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_approval_center_does_not_collect_authoritative_actor_and_shows_session_authority():
    src=(ROOT/"ui/web/src/pages/ApprovalCenterView.ts").read_text(encoding="utf-8")
    assert 'approval-actor' not in src
    assert "Autoridad autenticada" in src
    assert "El servidor es la autoridad" in src
    assert "authCapabilities" in src
    assert "actor: 'local-owner'" not in src

def test_web_client_uses_browser_session_cookie_and_csrf_for_mutations():
    src=(ROOT/"ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "credentials: 'include'" in src
    assert "devpilot_csrf" in src
    assert "'X-DevPilot-CSRF'" in src
