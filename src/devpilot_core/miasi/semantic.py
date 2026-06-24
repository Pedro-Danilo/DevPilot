from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.miasi.registry import AGENT_REGISTRY_FILE, POLICY_MATRIX_FILE, TOOL_REGISTRY_FILE
from devpilot_core.miasi.semantic_models import MiasiSemanticReport


class MiasiSemanticReportBuilder:
    """Build preliminary Policy/MIASI semantic report payloads.

    POST-H-004-A does not execute semantic rules. It provides the stable report
    contract and a deterministic empty-report builder used by tests, docs and
    future rule implementations.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def source_paths(self) -> dict[str, str]:
        return {
            "agent_registry": AGENT_REGISTRY_FILE.as_posix(),
            "tool_registry": TOOL_REGISTRY_FILE.as_posix(),
            "policy_matrix": POLICY_MATRIX_FILE.as_posix(),
            "semantic_report_schema": "docs/schemas/miasi_semantic_report.schema.json",
        }

    def build_empty_report(self, *, report_id: str = "miasi-semantic-post-h-004-a") -> MiasiSemanticReport:
        return MiasiSemanticReport(
            report_id=report_id,
            created_by="POST-H-004-A",
            status="schema-only",
            source_paths=self.source_paths(),
            no_go_gates=(
                "remote.execute must remain blocked",
                "plugin.execute must remain blocked until sandboxed",
                "connector.write must remain blocked unless future ADR/sandbox/test-contract gates approve it",
            ),
            notes=(
                "POST-H-004-A defines the semantic report schema and model only; semantic rules start in POST-H-004-B.",
                "This report builder does not execute agents, tools, remote runners, plugins, connectors, network calls or tests.",
            ),
        )

    def build_empty_payload(self, *, report_id: str = "miasi-semantic-post-h-004-a") -> dict[str, Any]:
        return self.build_empty_report(report_id=report_id).to_dict()
