from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"


def _read(path: str) -> str:
    return (WEB / path).read_text(encoding="utf-8")


def test_settings_ui_is_api_only_and_plan_only() -> None:
    client = _read("src/api/client.ts")
    settings = _read("src/pages/SettingsView.ts")
    provider_component = _read("src/components/ProviderSettings.ts")
    all_sources = client + settings + provider_component
    assert "/settings/workspace" in client
    assert "/settings/providers" in client
    assert "/settings/policy" in client
    assert "/settings/providers/plan" in client
    assert "Provider editor plan-only" in settings
    assert "No escribe el archivo local de providers" in settings
    assert "fs.readFile" not in all_sources
    assert "writeFile" not in all_sources
    assert "devpilot_core" not in all_sources
    assert "outputs/" not in all_sources
    assert "/patch/apply" not in all_sources
    assert "/rollback/execute" not in all_sources


def test_package_and_smoke_test_track_sprint_72_settings_contract() -> None:
    package = json.loads((WEB / "package.json").read_text(encoding="utf-8"))
    smoke = _read("scripts/smoke-test.mjs")
    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-72"
    assert package["devpilot"]["settingsUi"] is True
    assert package["devpilot"]["providerEditorPlanOnly"] is True
    assert "FUNC-SPRINT-72" in smoke
    assert "/settings/providers/plan" in smoke
    assert "Settings UI" in smoke
