from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import ExitCode, Severity
from devpilot_core.evidence_graph import EvidenceGraphBuilder, EvidenceGraphOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _graph_from_result(result):
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    graph = result.data["graph"]
    assert graph["schema_id"] == "SCHEMA-DEVPL-EVIDENCE-GRAPH-V1"
    return graph


def test_evidence_graph_builds_schema_valid_local_model_without_writes() -> None:
    result = EvidenceGraphBuilder(ROOT).build()
    graph = _graph_from_result(result)

    schema_result = SchemaValidator(ROOT).validate_payload(
        schema="EvidenceGraph",
        payload=graph,
        instance_label="in-memory-evidence-graph",
    )

    assert schema_result.ok is True
    assert graph["summary"]["created_by"] == "POST-H-031-A"
    assert graph["summary"]["graph_declares_readiness"] is False
    assert graph["summary"]["read_only"] is True
    assert graph["summary"]["network_used"] is False
    assert graph["summary"]["external_api_used"] is False
    assert graph["summary"]["mutations_performed"] is False
    assert graph["summary"]["source_mutations_performed"] is False
    assert graph["safety"]["commands_executed"] is False
    assert graph["safety"]["secrets_read"] is False
    assert graph["safety"]["devpilot_db_read"] is False
    assert graph["summary"]["nodes_by_type"]["claim"] >= 5
    assert graph["summary"]["nodes_by_type"]["gate"] >= 8
    assert graph["summary"]["nodes_by_evidence_class"]["versioned_source"] >= 8
    assert graph["summary"]["nodes_by_evidence_class"]["missing_expected"] >= 1


def test_missing_runtime_sources_are_not_promoted_to_pass() -> None:
    graph = _graph_from_result(EvidenceGraphBuilder(ROOT).build())
    missing_runtime_nodes = [
        node
        for node in graph["nodes"]
        if node.get("evidence_class") == "missing_expected" and str(node.get("path", "")).startswith("outputs/")
    ]

    assert missing_runtime_nodes
    assert all(node["status"] == "missing" for node in missing_runtime_nodes)
    assert all(node.get("required") is False for node in missing_runtime_nodes)
    assert graph["summary"]["blocking_gaps_total"] == 0
    assert any(finding["id"] == "EVIDENCE_GRAPH_SOURCE_MISSING" for finding in graph["findings"])


def test_no_go_gates_and_claims_are_represented_without_overclaims() -> None:
    graph = _graph_from_result(EvidenceGraphBuilder(ROOT).build())
    nodes = {node["node_id"]: node for node in graph["nodes"]}
    edges = {(edge["source"], edge["target"], edge["edge_type"]) for edge in graph["edges"]}

    assert nodes["claim:production-ready-local"]["status"] == "allowed"
    assert nodes["claim:enterprise-ready"]["status"] == "prohibited"
    assert nodes["claim:remote-ready"]["status"] == "prohibited"
    assert nodes["claim:compliance-certified"]["status"] == "prohibited"
    assert nodes["claim:saas-ready"]["status"] == "prohibited"
    assert nodes["gate:remote_execution_enabled"]["status"] == "active_blocking"
    assert nodes["gate:connector_write_enabled"]["status"] == "active_blocking"
    assert nodes["gate:plugin_execution_enabled"]["status"] == "active_blocking"
    assert ("gate:enterprise_ready_claim", "claim:enterprise-ready", "blocks") in edges
    assert ("gate:remote_ready_claim", "claim:remote-ready", "blocks") in edges
    assert graph["summary"]["graph_declares_readiness"] is False


def test_application_service_exposes_evidence_graph_read_only() -> None:
    result = ApplicationService(ROOT).evidence_graph()
    graph = _graph_from_result(result)

    assert result.command == "evidence graph"
    assert graph["safety"]["read_only"] is True
    assert graph["safety"]["reports_written"] is False


def test_evidence_graph_write_report_is_explicit_and_limited_to_outputs(tmp_path: Path) -> None:
    output_json = tmp_path / "evidence_graph.json"
    output_markdown = tmp_path / "evidence_graph.md"
    result = EvidenceGraphBuilder(
        ROOT,
        EvidenceGraphOptions(write_report=True, output_json=output_json, output_markdown=output_markdown),
    ).build()

    graph = _graph_from_result(result)
    assert graph["safety"]["reports_written"] is True
    assert output_json.exists()
    assert output_markdown.exists()
    stored = json.loads(output_json.read_text(encoding="utf-8"))
    assert stored["schema_id"] == "SCHEMA-DEVPL-EVIDENCE-GRAPH-V1"
    assert "Evidence Graph" in output_markdown.read_text(encoding="utf-8")


def test_evidence_graph_cli_json_and_report_output(tmp_path: Path) -> None:
    output_json = tmp_path / "evidence_graph.json"
    output_markdown = tmp_path / "evidence_graph.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "evidence",
            "graph",
            "--json",
            "--write-report",
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_markdown),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "evidence graph"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert output_json.exists()
    assert output_markdown.exists()


def test_evidence_graph_blocks_forbidden_secret_or_db_source(tmp_path: Path) -> None:
    config_dir = tmp_path / ".devpilot" / "evidence"
    config_dir.mkdir(parents=True)
    config = config_dir / "evidence_graph_sources.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "sources": [
                    {
                        "source_id": "forbidden-db",
                        "title": "Forbidden DB",
                        "path": ".devpilot/devpilot.db",
                        "node_type": "evidence",
                        "evidence_class": "versioned_source",
                        "required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = EvidenceGraphBuilder(ROOT, EvidenceGraphOptions(sources_path=config)).build()
    graph = result.data["graph"]

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert graph["status"] == "blocked"
    assert any(finding.id == "EVIDENCE_GRAPH_FORBIDDEN_SOURCE" and finding.severity == Severity.BLOCK for finding in result.findings)
