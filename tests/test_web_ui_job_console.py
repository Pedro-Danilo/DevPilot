from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def text(path: str) -> str: return (ROOT / path).read_text(encoding="utf-8")

def test_uoc008_jobs_route_and_console_contract() -> None:
    main = text("ui/web/src/main.ts"); view = text("ui/web/src/pages/JobsView.ts")
    assert "routeId: 'ui.jobs'" in main and "path: '/jobs'" in main
    for marker in ["Job Console", "Polling activo 3s", "Solicitar cancelación", "Crear retry gobernado", "Logs sanitizados", "STale".upper()]:
        assert marker in view or marker.capitalize() in view
    assert "child_process" not in view and "subprocess.run" not in view and "shell=True" not in view

def test_uoc008_client_uses_typed_jobs_api_only() -> None:
    client = text("ui/web/src/api/client.ts")
    for marker in ["/jobs", "/logs", "/cancel", "/retry"]: assert marker in client
    for forbidden in ["/git/push", "child_process", "exec("]: assert forbidden not in client

def test_uoc008_responsive_job_console_css() -> None:
    styles = text("ui/web/src/styles.css")
    assert ".jobs-grid" in styles and ".job-metrics" in styles and "@media" in styles


def test_job_console_supports_opaque_job_deep_links() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/JobsView.ts").read_text(encoding="utf-8")
    assert "jobsDetail" in main
    assert "/^\\/jobs\\/(job_[A-Za-z0-9_-]+)$/" in main
    assert "initialJobId" in view
    assert "history.replaceState" in view
    assert "`/jobs/${job.job_id}`" in view
