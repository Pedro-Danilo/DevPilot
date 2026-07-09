from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity

__test__ = False

POST_H_029_C_CREATED_BY = "POST-H-029-C"
TEST_IMPACT_RECOMMENDATION_SCHEMA_ID = "SCHEMA-DEVPL-TEST-IMPACT-RECOMMENDATION-REPORT-V1"
TEST_IMPACT_RECOMMENDATION_CONTRACT = "TestImpactRecommendationReport"
DEFAULT_TEST_IMPACT_RECOMMENDATION_REPORT_JSON = Path("outputs/reports/test_impact_recommendation_report.json")
DEFAULT_TEST_IMPACT_RECOMMENDATION_REPORT_MD = Path("outputs/reports/test_impact_recommendation_report.md")

_DANGEROUS_SHELL_TOKENS = ("&&", "||", ";", "|", ">", "<", "`", "$(", "curl ", "wget ", "powershell", "pwsh", "cmd.exe")
_ALLOWED_COMMAND_PREFIXES = (
    "python -m pytest ",
    "python -m devpilot_core ",
    "npm --prefix ui/web test",
    "npm --prefix ui/web run test:visual",
    "npm --prefix ui/web run test:operator-flows",
    "npm --prefix ui/web run test:route-enforcement",
)


@dataclass(frozen=True)
class TestImpactRecommendationReportOptions:
    __test__ = False

    output_json: str | Path = DEFAULT_TEST_IMPACT_RECOMMENDATION_REPORT_JSON
    output_markdown: str | Path = DEFAULT_TEST_IMPACT_RECOMMENDATION_REPORT_MD


class TestImpactRecommendationReportBuilder:
    __test__ = False

    """Build POST-H-029-C normalized recommendation reports without executing tests."""

    def __init__(self, root: Path, options: TestImpactRecommendationReportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or TestImpactRecommendationReportOptions()
        self.output_json = self._resolve(self.options.output_json)
        self.output_markdown = self._resolve(self.options.output_markdown)

    def build(self, *, analyzer_data: dict[str, Any], findings: list[Finding], ok: bool) -> dict[str, Any]:
        summary = dict(analyzer_data.get("summary") or {})
        matched_contracts = [item for item in analyzer_data.get("matched_contracts", []) if isinstance(item, dict)]
        recommendations = [item for item in analyzer_data.get("heuristic_recommendations", []) if isinstance(item, dict)]
        matched_rules = self._matched_rules(recommendations)
        unmatched_paths = [str(item) for item in analyzer_data.get("unmatched_paths", [])]
        recommended_commands = [str(item) for item in analyzer_data.get("recommended_commands", [])]
        recommended_tests = [str(item) for item in analyzer_data.get("recommended_tests", [])]
        recommended_profiles = [str(item) for item in summary.get("recommended_profiles", [])]
        unsafe_commands = [command for command in recommended_commands if not self._is_safe_command(command)]
        p0_total = int(summary.get("p0_selected_total", 0) or 0)
        p1_total = int(summary.get("p1_selected_total", 0) or 0)
        manual_review_required = bool(unmatched_paths) or any(bool((rule.get("escalation") or {}).get("manual_review_required")) for rule in matched_rules)
        full_regression_required = self._full_regression_required(
            p0_total=p0_total,
            p1_total=p1_total,
            unmatched_paths=unmatched_paths,
            matched_rules=matched_rules,
        )
        residual_risk = self._residual_risk(
            p0_total=p0_total,
            p1_total=p1_total,
            unmatched_paths=unmatched_paths,
            matched_contracts=matched_contracts,
            unsafe_commands=unsafe_commands,
            full_regression_required=full_regression_required,
        )
        decision = "PASS"
        status = "pass"
        if unsafe_commands or not ok:
            decision = "BLOCK"
            status = "blocked"
        elif manual_review_required or full_regression_required:
            decision = "REVIEW_REQUIRED"
            status = "review-required"
        recommendation_groups = self._recommendation_groups(
            full_regression_required=full_regression_required,
            manual_review_required=manual_review_required,
            recommended_profiles=recommended_profiles,
            recommended_commands=recommended_commands,
            recommended_tests=recommended_tests,
        )
        report_summary = {
            "created_by": POST_H_029_C_CREATED_BY,
            "status": "implemented-initial",
            "decision": decision,
            "changed_paths_total": int(summary.get("changed_paths_total", 0) or 0),
            "matched_contracts_total": len(matched_contracts),
            "matched_rules_total": len(matched_rules),
            "recommended_profiles_total": len(recommended_profiles),
            "recommended_tests_total": len(recommended_tests),
            "recommended_commands_total": len(recommended_commands),
            "unmatched_paths_total": len(unmatched_paths),
            "manual_review_required": manual_review_required,
            "full_regression_required": full_regression_required,
            "waiver_required": bool(full_regression_required),
            "waiver_required_if_full_regression_skipped": bool(full_regression_required),
            "residual_risk": residual_risk,
            "unsafe_commands_total": len(unsafe_commands),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return {
            "schema_version": "1.0",
            "schema_id": TEST_IMPACT_RECOMMENDATION_SCHEMA_ID,
            "report_id": "devpilot-test-impact-recommendation-report",
            "created_by": POST_H_029_C_CREATED_BY,
            "status": status,
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": report_summary,
            "changed_paths": [str(item) for item in analyzer_data.get("changed_paths", [])],
            "matched_contracts": matched_contracts,
            "matched_rules": matched_rules,
            "unmatched_paths": unmatched_paths,
            "recommended_profiles": recommended_profiles,
            "recommended_tests": recommended_tests,
            "recommended_commands": recommended_commands,
            "recommendation_groups": recommendation_groups,
            "residual_risk": {
                "level": residual_risk,
                "full_regression_required": full_regression_required,
                "manual_review_required": manual_review_required,
                "waiver_required_if_full_regression_skipped": bool(full_regression_required),
                "reasons": self._risk_reasons(p0_total, p1_total, unmatched_paths, unsafe_commands, full_regression_required),
            },
            "execution_plan": {
                "tests_executed": False,
                "operator_must_run_commands_manually": True,
                "run_now_profiles": recommendation_groups["run_now"]["profiles"],
                "run_before_closure_profiles": recommendation_groups["run_before_closure"]["profiles"],
                "commands": recommended_commands,
            },
            "waiver": {
                "required_if_full_regression_skipped": bool(full_regression_required),
                "allowed_before_post_h_029_e": False,
                "required_fields_future": ["owner", "reason", "risk", "tests_executed", "expiration"],
                "note": "POST-H-029-E will formalize waiver validation and closure blocking semantics.",
            },
            "unsafe_commands": unsafe_commands,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-029-C normalizes test-impact analyze-v2 output for operator decisions; it does not execute tests.",
                "Recommended commands remain data until an operator executes them explicitly.",
                "Full regression is preserved; skipping it when required needs a future POST-H-029-E waiver/guard decision.",
            ],
        }

    def write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        self.output_json.parent.mkdir(parents=True, exist_ok=True)
        self.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        report = dict(report)
        summary = dict(report.get("summary") or {})
        summary["reports_written"] = True
        report["summary"] = summary
        self.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.output_markdown.write_text(self._render_markdown(report), encoding="utf-8")
        return {"json": self.relative(self.output_json), "markdown": self.relative(self.output_markdown)}

    def _matched_rules(self, recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in recommendations:
            if item.get("source") != "test_impact_rule_registry":
                continue
            rule_id = str(item.get("rule_id") or "")
            if not rule_id or rule_id in seen:
                continue
            seen.add(rule_id)
            escalation = item.get("escalation") if isinstance(item.get("escalation"), dict) else {}
            out.append(
                {
                    "rule_id": rule_id,
                    "label": str(item.get("label") or rule_id),
                    "source": "test_impact_rule_registry",
                    "profiles": [str(profile) for profile in item.get("profiles", [])],
                    "recommended_tests": [str(test) for test in item.get("tests", [])],
                    "recommended_commands": [str(command) for command in item.get("commands", [])],
                    "escalation": escalation,
                }
            )
        return out

    def _full_regression_required(self, *, p0_total: int, p1_total: int, unmatched_paths: list[str], matched_rules: list[dict[str, Any]]) -> bool:
        if unmatched_paths and any(self._sensitive_path(path) for path in unmatched_paths):
            return True
        if any(bool((rule.get("escalation") or {}).get("full_regression_required")) for rule in matched_rules):
            return True
        if p0_total > 0:
            return True
        return False

    def _residual_risk(
        self,
        *,
        p0_total: int,
        p1_total: int,
        unmatched_paths: list[str],
        matched_contracts: list[dict[str, Any]],
        unsafe_commands: list[str],
        full_regression_required: bool,
    ) -> str:
        if unsafe_commands:
            return "critical"
        if unmatched_paths and any(self._sensitive_path(path) for path in unmatched_paths):
            return "critical"
        if p0_total > 0 or full_regression_required:
            return "high"
        if p1_total > 0 or matched_contracts or unmatched_paths:
            return "medium"
        return "low"

    def _risk_reasons(self, p0_total: int, p1_total: int, unmatched_paths: list[str], unsafe_commands: list[str], full_regression_required: bool) -> list[str]:
        reasons: list[str] = []
        if p0_total:
            reasons.append(f"{p0_total} P0 contracts selected")
        if p1_total:
            reasons.append(f"{p1_total} P1 contracts selected")
        if unmatched_paths:
            reasons.append("unmatched paths require review")
        if unsafe_commands:
            reasons.append("unsafe recommended commands detected")
        if full_regression_required:
            reasons.append("full regression required before closure/release decision")
        if not reasons:
            reasons.append("mapped impact with no blocking risk signal")
        return reasons

    def _recommendation_groups(
        self,
        *,
        full_regression_required: bool,
        manual_review_required: bool,
        recommended_profiles: list[str],
        recommended_commands: list[str],
        recommended_tests: list[str],
    ) -> dict[str, Any]:
        run_now_profiles = [profile for profile in recommended_profiles if profile not in {"full", "nightly-local", "release-candidate-local"}]
        before_closure_profiles = [profile for profile in recommended_profiles if profile in {"release", "release-candidate-local", "full", "nightly-local"}]
        if full_regression_required and "full" not in before_closure_profiles:
            before_closure_profiles.append("full")
        return {
            "run_now": {
                "profiles": run_now_profiles,
                "tests": recommended_tests,
                "commands": recommended_commands,
                "purpose": "Focal verification for current development/implementation loop.",
            },
            "run_before_closure": {
                "profiles": before_closure_profiles,
                "full_regression_required": full_regression_required,
                "purpose": "Stronger evidence required before backlog, release candidate or high-risk closure.",
            },
            "manual_review": {
                "required": manual_review_required,
                "purpose": "Human review is required for unmatched impact, high-risk escalation or future waiver decision.",
            },
        }

    def _sensitive_path(self, path: str) -> bool:
        normalized = path.replace("\\", "/").lower()
        sensitive_prefixes = (
            ".devpilot/",
            "docs/schemas/",
            "src/devpilot_core/policy",
            "src/devpilot_core/security",
            "src/devpilot_core/approval",
            "src/devpilot_core/rbac",
            "src/devpilot_core/quality",
            "src/devpilot_core/testing",
            "src/devpilot_core/cli.py",
            "pyproject.toml",
        )
        return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in sensitive_prefixes)

    def _is_safe_command(self, command: str) -> bool:
        normalized = re.sub(r"\s+", " ", command.strip())
        lowered = normalized.lower()
        if not normalized:
            return False
        if any(token in lowered for token in _DANGEROUS_SHELL_TOKENS):
            return False
        return any(normalized.startswith(prefix) for prefix in _ALLOWED_COMMAND_PREFIXES)

    def _render_markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = ["# POST-H-029-C — Test impact recommendation report", ""]
        for key in ["decision", "residual_risk", "full_regression_required", "manual_review_required", "waiver_required", "recommended_profiles_total", "recommended_tests_total", "recommended_commands_total", "tests_executed"]:
            lines.append(f"- `{key}`: `{summary.get(key)}`")
        lines.extend(["", "## Recommended profiles", ""])
        for profile in report.get("recommended_profiles", []):
            lines.append(f"- `{profile}`")
        lines.extend(["", "## Notes", ""])
        for note in report.get("notes", []):
            lines.append(f"- {note}")
        return "\n".join(lines) + "\n"

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (self.root / path).resolve()

    def relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()
