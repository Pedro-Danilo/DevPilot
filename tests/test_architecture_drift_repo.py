from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.repo import ArchitectureDriftConfig, ArchitectureDriftDetector

ROOT = Path(__file__).resolve().parents[1]


def _write_architecture_doc(root: Path, body: str) -> Path:
    doc = root / "docs/02_architecture/c4_component.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(body, encoding="utf-8")
    return doc


def _write_module(root: Path, name: str) -> None:
    package = root / "src/devpilot_core" / name
    package.mkdir(parents=True, exist_ok=True)
    (root / "src/devpilot_core/__init__.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "src/devpilot_core/__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")


def test_architecture_drift_matches_documented_component_to_module(tmp_path: Path) -> None:
    _write_module(tmp_path, "repo")
    doc = _write_architecture_doc(
        tmp_path,
        """
# C4 Component

| Componente | Ruta principal | Estado | Responsabilidad |
|---|---|---|---|
| Repo | `src/devpilot_core/repo` | `implemented-initial` | Repo analysis. |
""".strip(),
    )

    result = ArchitectureDriftDetector(
        tmp_path,
        config=ArchitectureDriftConfig(architecture_docs=(str(doc.relative_to(tmp_path)),)),
    ).detect()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["drift_counts"].get("in_sync", 0) >= 1
    assert any(row["documented_component"] == "Repo" and row["code_module"] == "repo" for row in result.data["matrix"])


def test_architecture_drift_reports_code_missing_for_implemented_component(tmp_path: Path) -> None:
    (tmp_path / "src/devpilot_core").mkdir(parents=True)
    (tmp_path / "src/devpilot_core/__init__.py").write_text("", encoding="utf-8")
    doc = _write_architecture_doc(
        tmp_path,
        """
# C4 Component

| Componente | Ruta principal | Estado | Responsabilidad |
|---|---|---|---|
| Missing Engine | `src/devpilot_core/missing_engine` | `implemented` | Expected implementation. |
""".strip(),
    )

    result = ArchitectureDriftDetector(
        tmp_path,
        config=ArchitectureDriftConfig(architecture_docs=(str(doc.relative_to(tmp_path)),)),
    ).detect()

    assert result.ok is True
    assert any(finding.id == "ARCH_DRIFT_CODE_MISSING" for finding in result.findings)
    row = next(row for row in result.data["matrix"] if row["documented_component"] == "Missing Engine")
    assert row["drift_type"] == "code_missing"
    assert row["severity"] == "warning"


def test_architecture_drift_reports_doc_missing_for_undocumented_module(tmp_path: Path) -> None:
    _write_module(tmp_path, "undocumented")
    doc = _write_architecture_doc(
        tmp_path,
        """
# C4 Component

| Componente | Ruta principal | Estado | Responsabilidad |
|---|---|---|---|
| Repo | `src/devpilot_core/repo` | `planned` | Future repo component. |
""".strip(),
    )

    result = ArchitectureDriftDetector(
        tmp_path,
        config=ArchitectureDriftConfig(architecture_docs=(str(doc.relative_to(tmp_path)),)),
    ).detect()

    assert result.ok is True
    assert any(finding.id == "ARCH_DRIFT_DOC_MISSING" for finding in result.findings)
    assert any(row["code_module"] == "undocumented" and row["drift_type"] == "doc_missing" for row in result.data["matrix"])


def test_architecture_drift_does_not_block_future_components_without_code(tmp_path: Path) -> None:
    (tmp_path / "src/devpilot_core").mkdir(parents=True)
    (tmp_path / "src/devpilot_core/__init__.py").write_text("", encoding="utf-8")
    doc = _write_architecture_doc(
        tmp_path,
        """
# C4 Component

| Componente | Ruta principal | Estado | Responsabilidad |
|---|---|---|---|
| Desktop UI | `src/devpilot_core/desktop` | `future` | Future interface. |
""".strip(),
    )

    result = ArchitectureDriftDetector(
        tmp_path,
        config=ArchitectureDriftConfig(architecture_docs=(str(doc.relative_to(tmp_path)),)),
    ).detect()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    row = next(row for row in result.data["matrix"] if row["documented_component"] == "Desktop UI")
    assert row["drift_type"] == "code_missing"
    assert row["severity"] == "info"
    assert not any(finding.severity.value == "block" for finding in result.findings)


def test_architecture_drift_cli_writes_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report_json = ROOT / "outputs/reports/repo_architecture_drift.json"
    report_md = ROOT / "outputs/reports/repo_architecture_drift.md"
    if report_json.exists():
        report_json.unlink()
    if report_md.exists():
        report_md.unlink()

    exit_code = cli.main(["repo", "architecture-drift", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "repo architecture-drift"
    assert payload["data"]["summary"]["mutations_performed"] is False
    assert payload["data"]["summary"]["external_api_used"] is False
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/repo_architecture_drift.json",
        "markdown": "outputs/reports/repo_architecture_drift.md",
    }
    assert report_json.exists()
    assert report_md.exists()
