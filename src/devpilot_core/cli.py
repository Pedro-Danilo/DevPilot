from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import __version__
from .cli_models import CommandResult, ExitCode, Finding, Severity
from .errors import DevPilotError
from .validators.artifact import validate_artifact_file
from .validators.frontmatter import validate_frontmatter_file

ROOT_MARKERS = ["pyproject.toml", "docs"]

REQUIRED_PRE_CODE_ARTIFACTS = [
    "docs/00_product/product_vision.md",
    "docs/00_product/business_case.md",
    "docs/00_product/mvp_scope.md",
    "docs/01_requirements/requirements_specification.md",
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/adrs/ADR-0001-adoptar-mipsoftware-y-miasi.md",
    "docs/03_security/security_threat_model.md",
    "docs/04_quality/test_strategy.md",
    "docs/checklists/checklist_pre_code.md",
]

REQUIRED_MIASI_ARTIFACTS = [
    "docs/06_miasi/agent_card.md",
    "docs/06_miasi/tool_card.md",
    "docs/06_miasi/policy_card.md",
    "docs/06_miasi/eval_card.md",
    "docs/06_miasi/human_approval_card.md",
    "docs/06_miasi/observability_card.md",
]


def project_root() -> Path:
    """Return the current working directory as DevPilot project root.

    FUNC-SPRINT-01 keeps this simple to preserve backwards compatibility. A
    later Workspace Manager sprint will replace this with explicit workspace
    discovery and `.devpilot/` metadata.
    """

    return Path.cwd()


def check_required_artifacts(root: Path) -> dict[str, Any]:
    """Compatibility helper used by the bootstrap test.

    It keeps the original shape: `{"ok": bool, "checks": [...]}`. New code
    should prefer `build_readiness_result()` because it returns CommandResult.
    """

    checks = []
    for rel in REQUIRED_PRE_CODE_ARTIFACTS:
        path = root / rel
        checks.append(
            {
                "artifact": rel,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    passed = all(item["exists"] and item["size_bytes"] > 0 for item in checks)
    return {"ok": passed, "checks": checks}


def build_readiness_result(root: Path) -> CommandResult:
    """Build the normalized result for the `readiness-check` command."""

    legacy_result = check_required_artifacts(root)
    findings: list[Finding] = []
    for item in legacy_result["checks"]:
        if not item["exists"]:
            findings.append(
                Finding(
                    id="READINESS_MISSING_ARTIFACT",
                    message=f"Required artifact is missing: {item['artifact']}",
                    severity=Severity.FAIL,
                    path=item["artifact"],
                )
            )
        elif item["size_bytes"] <= 0:
            findings.append(
                Finding(
                    id="READINESS_EMPTY_ARTIFACT",
                    message=f"Required artifact is empty: {item['artifact']}",
                    severity=Severity.FAIL,
                    path=item["artifact"],
                )
            )

    ok = legacy_result["ok"]
    return CommandResult(
        command="readiness-check",
        ok=ok,
        exit_code=ExitCode.PASS if ok else ExitCode.FAIL,
        message="Pre-code readiness artifacts found." if ok else "Pre-code readiness check failed.",
        data=legacy_result,
        findings=findings,
    )


def build_miasi_required_result() -> CommandResult:
    """Build the normalized result for the `miasi-required` command."""

    data = {
        "project": "DevPilot Local",
        "miasi_required": True,
        "reason": "La plataforma será agent-assisted y tendrá validadores/agentes para SDLC.",
        "required_artifacts": REQUIRED_MIASI_ARTIFACTS,
    }
    return CommandResult(
        command="miasi-required",
        ok=True,
        exit_code=ExitCode.PASS,
        message="MIASI is required for DevPilot Local.",
        data=data,
        findings=[
            Finding(
                id="MIASI_REQUIRED",
                message="DevPilot Local activates MIASI because it is an agent-assisted SDLC platform.",
                severity=Severity.INFO,
            )
        ],
    )


def write_readiness_report(root: Path, result: CommandResult) -> Path:
    """Persist readiness evidence in the historical report path."""

    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    out = report_dir / "readiness_check.json"
    out.write_text(json.dumps(result.data, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def print_result(result: CommandResult, *, json_output: bool = False) -> None:
    """Render a CommandResult for CLI users."""

    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    # Backwards-compatible human output for bootstrap commands.
    if result.command == "readiness-check":
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return
    if result.command == "miasi-required":
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return

    print(result.message)
    for finding in result.findings:
        path = f" [{finding.path}]" if finding.path else ""
        print(f"- {finding.severity.value.upper()}: {finding.id}{path} — {finding.message}")


def readiness_check(*, json_output: bool = False) -> int:
    root = project_root()
    result = build_readiness_result(root)
    write_readiness_report(root, result)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def miasi_required(*, json_output: bool = False) -> int:
    result = build_miasi_required_result()
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def validate_frontmatter_command(path: str, *, json_output: bool = False, strict: bool = False) -> int:
    """Validate frontmatter metadata for one Markdown artifact."""

    root = project_root()
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    result = validate_frontmatter_file(target, root=root, strict=strict)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def validate_artifact_command(path: str, *, json_output: bool = False, strict: bool = False) -> int:
    """Validate one Markdown artifact against its MIPSoftware/MIASI profile."""

    root = project_root()
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    result = validate_artifact_file(target, root=root, strict=strict)
    print_result(result, json_output=json_output)
    return int(result.exit_code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devpilot", description="DevPilot Local CLI")
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    readiness = sub.add_parser("readiness-check", help="Check pre-code readiness artifacts")
    readiness.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    miasi = sub.add_parser("miasi-required", help="Explain MIASI activation for this project")
    miasi.add_argument("--json", action="store_true", help="Emit normalized JSON command result")

    frontmatter = sub.add_parser("validate-frontmatter", help="Validate Markdown frontmatter metadata")
    frontmatter.add_argument("path", help="Markdown document path to validate")
    frontmatter.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    frontmatter.add_argument("--strict", action="store_true", help="Treat approved documents without approval as failures")

    artifact = sub.add_parser("validate-artifact", help="Validate Markdown artifact structure by profile")
    artifact.add_argument("path", help="Markdown document path to validate")
    artifact.add_argument("--json", action="store_true", help="Emit normalized JSON command result")
    artifact.add_argument("--strict", action="store_true", help="Run strict frontmatter validation before structure checks")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.version:
            print(f"devpilot-local {__version__}")
            return int(ExitCode.PASS)
        if args.command == "readiness-check":
            return readiness_check(json_output=args.json)
        if args.command == "miasi-required":
            return miasi_required(json_output=args.json)
        if args.command == "validate-frontmatter":
            return validate_frontmatter_command(args.path, json_output=args.json, strict=args.strict)
        if args.command == "validate-artifact":
            return validate_artifact_command(args.path, json_output=args.json, strict=args.strict)
        parser.print_help()
        return int(ExitCode.PASS)
    except DevPilotError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return int(exc.exit_code)
    except Exception as exc:  # defensive boundary for CLI users
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return int(ExitCode.ERROR)
