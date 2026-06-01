from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__

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


def project_root() -> Path:
    return Path.cwd()


def check_required_artifacts(root: Path) -> dict:
    checks = []
    for rel in REQUIRED_PRE_CODE_ARTIFACTS:
        path = root / rel
        checks.append({"artifact": rel, "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    passed = all(item["exists"] and item["size_bytes"] > 0 for item in checks)
    return {"ok": passed, "checks": checks}


def readiness_check() -> int:
    root = project_root()
    result = check_required_artifacts(root)
    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    out = report_dir / "readiness_check.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


def miasi_required() -> int:
    result = {
        "project": "DevPilot Local",
        "miasi_required": True,
        "reason": "La plataforma será agent-assisted y tendrá validadores/agentes para SDLC.",
        "required_artifacts": [
            "docs/06_miasi/agent_card.md",
            "docs/06_miasi/tool_card.md",
            "docs/06_miasi/policy_card.md",
            "docs/06_miasi/eval_card.md",
            "docs/06_miasi/human_approval_card.md",
            "docs/06_miasi/observability_card.md",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devpilot", description="DevPilot Local MVP bootstrap CLI")
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("readiness-check", help="Check pre-code readiness artifacts")
    sub.add_parser("miasi-required", help="Explain MIASI activation for this project")
    args = parser.parse_args(argv)

    if args.version:
        print(f"devpilot-local {__version__}")
        return 0
    if args.command == "readiness-check":
        return readiness_check()
    if args.command == "miasi-required":
        return miasi_required()
    parser.print_help()
    return 0
