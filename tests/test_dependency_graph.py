from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.repo import DependencyGraphBuilder


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_dependency_graph_extracts_internal_imports_without_executing_code(tmp_path: Path) -> None:
    root = tmp_path
    package = root / "src" / "sample_pkg"
    _write(package / "__init__.py", "")
    _write(package / "service.py", "import os\nfrom sample_pkg import utils\nfrom sample_pkg.domain import model\n")
    _write(package / "utils.py", "VALUE = 1\n")
    _write(package / "domain" / "__init__.py", "")
    _write(package / "domain" / "model.py", "from .. import utils\n")

    result = DependencyGraphBuilder(root).build(target="src/sample_pkg")

    assert result.ok
    assert result.data["summary"]["root_package"] == "sample_pkg"
    edges = {(edge["source"], edge["target"]) for edge in result.data["edges"]}
    assert ("sample_pkg.service", "sample_pkg.utils") in edges
    assert ("sample_pkg.service", "sample_pkg.domain.model") in edges
    assert ("sample_pkg.domain.model", "sample_pkg.utils") in edges
    service = next(node for node in result.data["nodes"] if node["module"] == "sample_pkg.service")
    assert service["fan_out"] == 2
    assert "os" in service["external_imports"]


def test_dependency_graph_excludes_external_imports_from_internal_edges(tmp_path: Path) -> None:
    root = tmp_path
    package = root / "src" / "app"
    _write(package / "__init__.py", "")
    _write(package / "main.py", "import json\nimport requests\nfrom app.local import thing\n")
    _write(package / "local.py", "thing = 1\n")

    result = DependencyGraphBuilder(root).build(target="src/app")

    assert result.ok
    assert {edge["target"] for edge in result.data["edges"]} == {"app.local"}
    assert {"json", "requests"}.issubset(set(result.data["external_imports"]))


def test_dependency_graph_reports_syntax_errors_as_findings(tmp_path: Path) -> None:
    root = tmp_path
    package = root / "src" / "broken"
    _write(package / "__init__.py", "")
    _write(package / "bad.py", "def broken(:\n")

    result = DependencyGraphBuilder(root).build(target="src/broken")

    assert result.ok
    assert result.data["summary"]["syntax_error_files_total"] == 1
    assert result.findings[0].id == "DEPENDENCY_GRAPH_SYNTAX_ERROR"
    bad_node = next(node for node in result.data["nodes"] if node["module"] == "broken.bad")
    assert bad_node["syntax_error"] is True


def test_dependency_graph_blocks_target_outside_workspace(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _write(outside / "x.py", "import os\n")

    result = DependencyGraphBuilder(root).build(target=outside)

    assert not result.ok
    assert result.exit_code == 2
    assert result.findings[0].id == "PATHGUARD_OUTSIDE_ROOT"


def test_dependency_graph_cli_writes_report(capsys) -> None:
    exit_code = cli.main(["repo", "dependency-graph", "--target", "src/devpilot_core", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "repo dependency-graph"
    assert payload["data"]["summary"]["nodes_total"] > 0
    assert payload["data"]["reports"]["json"].endswith("repo_dependency_graph.json")
    assert payload["data"]["reports"]["markdown"].endswith("repo_dependency_graph.md")
