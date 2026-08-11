from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_uoc009_quality_route_and_ux_contract() -> None:
    main=text('ui/web/src/main.ts'); view=text('ui/web/src/pages/QualityOperationsView.ts')
    assert "routeId: 'ui.quality'" in main and "path: '/quality'" in main
    for m in ['Quality, tests y release','Planificar Test Impact','Approval requerido','RUN FULL REGRESSION','Abrir en Job Console','Empaquetar evidencia']: assert m in view
    for forbidden in ['child_process','devpilot_core','shell=True','/tests/run']: assert forbidden not in view

def test_uoc009_quality_ui_is_responsive_and_api_only() -> None:
    css=text('ui/web/src/styles.css'); client=text('ui/web/src/api/client.ts')
    assert '.quality-grid' in css and '@media' in css
    for m in ['/quality/operations','/quality/baseline','/quality/test-impact/plan','/quality/jobs/plan','/quality/evidence/package']: assert m in client

def test_uoc009_quality_approval_scope_is_json_and_403_is_localized_to_quality_ui() -> None:
    view=text('ui/web/src/pages/QualityOperationsView.ts'); client=text('ui/web/src/api/client.ts')
    assert "scope:JSON.stringify({operation_id:op.operation_id,workspace_id:state.workspaceId,source:'ui.quality'})" in view
    assert "DevPilotApiError" in view and "error.status === 403" in view
    assert "Approval BLOCK 403:" in view
    # Preserve the historical shared API-client error contract outside the UOC-009 surface.
    assert "Unauthorized/Forbidden 401/403: token local faltante o inválido." in client

