from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase_f_web_first_strategy_artifacts_are_synchronized() -> None:
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    adr = _read("docs/02_architecture/adrs/ADR-0013-web-ui-first.md")
    runbook = _read("docs/05_operations/runbook.md")
    c4 = _read("docs/02_architecture/c4_container.md")
    contract = _read("docs/07_interfaces/internal_application_contract.md")
    readme = _read("README.md")

    for text in [backlog, adr, runbook, c4, contract, readme]:
        assert "Web UI local" in text
        assert "Desktop" in text

    assert 'ui_strategy: "web_local_first_web_real_ready_desktop_deferred"' in backlog
    assert "Web UI local web-ready" in backlog
    assert "Desktop queda fuera del alcance de implementación de Fase F" in backlog
    assert "Web UI first" in adr
    assert "Desktop queda diferida" in adr or "Desktop queda diferido" in adr
    assert "planned-fase-f" in c4
    assert "deferred" in c4
    assert "CLI/API/Web UI" in contract
    assert "Web UI local primero" in runbook
    assert "web-first" in readme.lower()


def test_phase_f_backlog_no_longer_requires_desktop_shell_as_deliverable() -> None:
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    lowered = backlog.lower()

    assert "desktop shell preliminar" not in lowered
    assert "desktop shell debe" not in lowered
    assert "desktop queda fuera" in lowered
    assert "desktop diferido" in lowered or "desktop queda diferido" in lowered
    assert "web ui real" in lowered
    assert "web ui local" in lowered


def test_phase_f_strategy_preserves_safety_boundaries() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "docs/devpilot_backlog_fase_F_producto_visual.md",
            "docs/02_architecture/adrs/ADR-0013-web-ui-first.md",
            "docs/05_operations/runbook.md",
            "docs/07_interfaces/internal_application_contract.md",
        ]
    ).lower()

    for term in ["127.0.0.1", "applicationservice", "policyengine", "approval", "dry-run", "cors", "secret"]:
        assert term in combined
