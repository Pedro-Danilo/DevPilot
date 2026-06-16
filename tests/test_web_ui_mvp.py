from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"


def _read(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


def test_web_ui_package_and_entrypoints_exist() -> None:
    package = json.loads(_read("package.json"))

    assert package["name"] == "devpilot-local-web-ui"
    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-70"
    assert package["devpilot"]["apiOnly"] is True
    assert package["devpilot"]["readOnly"] is True
    assert package["scripts"]["test"] == "node scripts/smoke-test.mjs"

    for path in [
        "index.html",
        "src/main.ts",
        "src/api/client.ts",
        "src/pages/Dashboard.ts",
        "src/components/StatusCard.ts",
        "src/components/FindingList.ts",
        "scripts/smoke-test.mjs",
    ]:
        assert (WEB / path).is_file(), path


def test_web_ui_consumes_api_only_and_never_imports_core() -> None:
    source_files = list((WEB / "src").rglob("*.ts"))
    assert source_files

    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    assert "devpilot_core" not in combined
    assert "from 'fs'" not in combined
    assert "child_process" not in combined
    assert "outputs/" not in combined
    assert ".devpilot/" not in combined
    assert "http://127.0.0.1:8787/api/v1" in combined
    assert "X-DevPilot-Token" in combined

    for endpoint in ["/workspace/status", "/validation/readiness", "/standards/status", "/miasi/status", "/reports", "/traces", "/metrics/summary"]:
        assert endpoint in combined

    for forbidden_endpoint in ["/patch/apply", "/rollback/execute", "/refactor/execute"]:
        assert forbidden_endpoint not in combined


def _assert_web_ui_smoke_contract_without_node() -> None:
    package = json.loads(_read("package.json"))
    client = _read("src/api/client.ts")
    dashboard = _read("src/pages/Dashboard.ts")
    status_card = _read("src/components/StatusCard.ts")
    main = _read("src/main.ts")
    sources = [client, dashboard, status_card, main]

    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-70"
    assert package["devpilot"]["apiOnly"] is True
    assert package["devpilot"]["readOnly"] is True
    assert package["scripts"]["test"] == "node scripts/smoke-test.mjs"

    for source in sources:
        assert "devpilot_core" not in source
        assert "child_process" not in source
        assert "outputs/" not in source

    for expected_path in ["/workspace/status", "/validation/readiness", "/standards/status", "/miasi/status", "/reports", "/traces", "/metrics/summary"]:
        assert expected_path in client

    assert "X-DevPilot-Token" in client
    assert "PASS" in status_card
    assert "WARN" in status_card
    assert "BLOCK" in status_card
    assert "/patch/apply" not in client
    assert "/rollback/execute" not in client


def test_web_ui_smoke_contract_passes_without_node_or_npm() -> None:
    _assert_web_ui_smoke_contract_without_node()


def _is_truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_npm_executable() -> str | None:
    candidates = ["npm.cmd", "npm.exe", "npm"] if os.name == "nt" else ["npm"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def test_web_ui_npm_smoke_test_is_explicit_opt_in() -> None:
    _assert_web_ui_smoke_contract_without_node()

    if not _is_truthy_env("DEVPILOT_RUN_WEB_UI_NPM_TEST"):
        return

    npm = _resolve_npm_executable()
    assert npm is not None, (
        "DEVPILOT_RUN_WEB_UI_NPM_TEST was enabled, but npm/npm.cmd was not found. "
        "Install Node.js 20+ or unset DEVPILOT_RUN_WEB_UI_NPM_TEST for the core pytest gate."
    )

    try:
        completed = subprocess.run(
            [npm, "test"],
            cwd=WEB,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise AssertionError(
            "npm was detected but could not be executed. On Windows this usually means "
            "npm.cmd is not resolvable from PATH. Reinstall Node.js or run npm test manually from ui/web."
        ) from exc

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "DEVPL WEB UI SMOKE TEST: PASS" in completed.stdout
