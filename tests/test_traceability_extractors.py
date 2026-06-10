from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.traceability import MarkdownTraceabilityExtractor, TraceEntity, TraceGraph, TraceLink

ROOT = Path(__file__).resolve().parents[1]


def test_traceability_models_are_json_serializable() -> None:
    entity = TraceEntity(
        entity_id="FR-MVP-001",
        entity_type=MarkdownTraceabilityExtractor(ROOT).extract_from_text("FR-MVP-001", source_path="x.md")[0][0].entity_type,
        source_path="docs/01_requirements/requirements_specification.md",
        line=1,
        column=1,
        context="FR-MVP-001",
    )
    link = TraceLink(
        source_entity_id="FR-MVP-001",
        target_entity_id="AC-MVP-001",
        link_type="explicit_reference",
        source_path="docs/01_requirements/traceability_matrix.md",
        evidence="FR-MVP-001 -> AC-MVP-001",
    )
    graph = TraceGraph(entities=[entity], links=[link])

    payload = graph.to_dict()
    json.dumps(payload, ensure_ascii=False)

    assert payload["summary"]["entities_total"] == 1
    assert payload["summary"]["links_total"] == 1


def test_markdown_extractor_detects_valid_ids_duplicates_and_invalid_tokens() -> None:
    source = ROOT / "tests/fixtures/traceability/traceability_fixture.md"

    result = MarkdownTraceabilityExtractor(ROOT).scan(targets=[source])

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    entity_ids = [item["entity_id"] for item in result.data["entities"]]
    assert "FR-MVP-001" in entity_ids
    assert "AC-MVP-001" in entity_ids
    assert "TEST-FUNC-25-001" in entity_ids
    assert "ADR-0010" in entity_ids
    assert "FR-MVP-001" in result.data["duplicate_entity_ids"]
    assert any(finding.id == "TRACEABILITY_ENTITY_DUPLICATE" for finding in result.findings)
    assert any(finding.id == "TRACEABILITY_ENTITY_ID_INVALID" for finding in result.findings)


def test_traceability_scan_default_repo_sources_detect_entities() -> None:
    result = MarkdownTraceabilityExtractor(ROOT).scan()

    assert result.ok is True
    assert result.data["summary"]["entities_total"] > 0
    assert result.data["summary"]["unique_entities_total"] > 0
    assert result.data["summary"]["links_total"] == 0
    assert result.data["summary"]["inferred_links"] is False
    assert any(entity["entity_id"].startswith("FR-") for entity in result.data["entities"])
    assert any(path.endswith("requirements_specification.md") for path in result.data["source_paths"])
    assert any("functional_sprint_" in path for path in result.data["source_paths"])


def test_traceability_scan_rejects_target_outside_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("FR-MVP-001", encoding="utf-8")

    try:
        MarkdownTraceabilityExtractor(ROOT).scan(targets=[outside])
    except ValueError as exc:
        assert "inside" in str(exc) or "root" in str(exc)
    else:
        raise AssertionError("Expected ValueError for target outside project root")


def test_traceability_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["traceability", "scan", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "traceability scan"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["entities_total"] > 0
    assert payload["data"]["summary"]["inferred_links"] is False


def test_traceability_cli_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report_json = ROOT / "outputs/reports/traceability_scan.json"
    report_md = ROOT / "outputs/reports/traceability_scan.md"
    if report_json.exists():
        report_json.unlink()
    if report_md.exists():
        report_md.unlink()

    exit_code = cli.main(["traceability", "scan", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/traceability_scan.json",
        "markdown": "outputs/reports/traceability_scan.md",
    }
    assert report_json.exists()
    assert report_md.exists()
