from __future__ import annotations

from typing import Any


def build_traceability_markdown_summary(payload: dict[str, Any]) -> str:
    """Render a compact Markdown summary for TraceabilityEngine payloads.

    The central ReportEngine remains the persisted evidence writer. This helper
    is intentionally side-effect free and can be reused by future UI/report
    layers that need a concise traceability summary.
    """

    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    lines = [
        "# DevPilot Traceability Summary",
        "",
        f"- Requirements: `{summary.get('requirements_total', 0)}`",
        f"- Requirements with AC: `{summary.get('requirements_with_acceptance_criteria', 0)}`",
        f"- Requirements with test/eval: `{summary.get('requirements_with_test_or_eval_evidence', 0)}`",
        f"- Gaps: `{summary.get('gaps_total', 0)}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total', 0)}`",
    ]
    return "\n".join(lines) + "\n"
