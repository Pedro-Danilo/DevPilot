#!/usr/bin/env python3
"""
FUNC-SPRINT-00 cleanup helper for DevPilot Local.

Purpose
-------
Detect generated artifacts that should not be committed to the repository:
Python caches, pytest caches, package metadata, build outputs and local ZIP exports.

Default behavior is dry-run. It only prints what would be removed.
Use --execute to delete the detected artifacts.

This Python version exists because some Windows PowerShell environments block
unsigned .ps1 scripts through ExecutionPolicy. The cleanup logic itself is not
PowerShell-specific, so this script provides a portable, local-first fallback.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".cache"}
DIR_SUFFIXES = (".egg-info",)
FILE_SUFFIXES = (".pyc", ".pyo", ".pyd")
FILE_PREFIX_PATTERNS = ("DevPilot_Local", "repo_DevPilot_Local", "patch_")
FILE_SUFFIX_PATTERNS = (".zip",)
EXCLUDED_ROOT_DIRS = {".git", ".venv", "venv", "env", ".idea", ".vscode"}


def is_zip_export(path: Path) -> bool:
    return path.suffix.lower() == ".zip" and any(path.name.startswith(prefix) for prefix in FILE_PREFIX_PATTERNS)


def collect_targets(root: Path) -> list[Path]:
    targets: list[Path] = []
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if rel_parts and rel_parts[0] in EXCLUDED_ROOT_DIRS:
            continue
        if path.is_dir():
            if path.name in DIR_NAMES or path.name.endswith(DIR_SUFFIXES):
                targets.append(path)
        elif path.is_file():
            if path.suffix in FILE_SUFFIXES or is_zip_export(path):
                targets.append(path)
    # Remove nested duplicates: if parent dir is already a target, skip child.
    unique: list[Path] = []
    for candidate in sorted(set(targets), key=lambda p: (len(p.parts), str(p))):
        if not any(parent in candidate.parents for parent in unique):
            unique.append(candidate)
    return unique


def remove_target(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean generated DevPilot Local artifacts.")
    parser.add_argument("--execute", action="store_true", help="Delete detected artifacts. Default is dry-run.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root. Defaults to current directory.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}")
        return 2

    targets = collect_targets(root)
    if not targets:
        print("FUNC-SPRINT-00 cleanup: no generated artifacts found.")
        return 0

    print("FUNC-SPRINT-00 cleanup: artifacts detected:")
    for target in targets:
        print(f" - {target.relative_to(root)}")

    if not args.execute:
        print("Dry-run only. Re-run with --execute to delete these artifacts.")
        return 0

    for target in targets:
        remove_target(target)
    print("FUNC-SPRINT-00 cleanup: generated artifacts removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
