from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')

def test_uoc010_ai_route_and_ux_contract() -> None:
    main=text('ui/web/src/main.ts'); view=text('ui/web/src/pages/AiOperationsView.ts')
    assert "routeId: 'ui.ai'" in main and "path: '/ai'" in main
    for m in ['IA / RAG gobernados','Mock obligatorio','External API','insufficient-evidence','Memoria local opt-in','Handoff','Approval requerido','Abrir Job Console']:
        assert m in view
    for bad in ['child_process','devpilot_core','shell=True','OPENAI_API_KEY','GEMINI_API_KEY']:
        assert bad not in view

def test_uoc010_ui_persists_operation_and_approval_across_approval_center_navigation() -> None:
    view=text('ui/web/src/pages/AiOperationsView.ts')
    assert 'sessionStorage.getItem(OP_KEY)' in view and 'sessionStorage.setItem(OP_KEY' in view
    assert 'sessionStorage.getItem(APPROVAL_KEY)' in view and 'sessionStorage.setItem(APPROVAL_KEY' in view
    assert "scope:JSON.stringify({operation_id:op.operation_id,workspace_id:state.workspaceId,source:'ui.ai'})" in view

def test_uoc010_ui_is_responsive_and_api_only() -> None:
    css=text('ui/web/src/styles.css'); client=text('ui/web/src/api/client.ts')
    assert '.ai-grid' in css and '.ai-status-grid' in css and '@media' in css
    for p in ['/ai/operations','/ai/status','/ai/jobs/plan','/ai/evidence/package']:
        assert p in client
