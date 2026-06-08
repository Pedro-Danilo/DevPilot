from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard

_DEFAULT_EXCLUDED_DIRS = (".git", ".venv", "__pycache__", ".pytest_cache", "outputs")
_TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".example"}
_HIGH_RISK_NAMES = {".env", ".env.local", ".env.dev", "id_rsa", "id_ed25519"}
_HIGH_RISK_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
_MEDIUM_RISK_SUFFIXES = {".lock", ".sqlite", ".db"}


@dataclass(frozen=True)
class RepoInventoryConfig:
    """Configuration for local repo inventory.

    The initial Sprint 14 config is intentionally conservative and dependency
    free. Runtime directories are excluded by default because outputs and caches
    should not dominate engineering inventory reports.
    """

    max_files: int = 5000
    max_secret_scan_bytes: int = 65536
    excluded_dirs: tuple[str, ...] = _DEFAULT_EXCLUDED_DIRS


@dataclass(frozen=True)
class RepoInventoryItem:
    """One file entry in the repository inventory."""

    path: str
    size_bytes: int
    suffix: str
    category: str
    risk: str
    secret_like: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "suffix": self.suffix,
            "category": self.category,
            "risk": self.risk,
            "secret_like": self.secret_like,
            "reasons": self.reasons,
        }


class RepoInventory:
    """Build a deterministic local inventory of a DevPilot workspace.

    Purpose:
        Provide repo visibility for future repo-analysis, patch review and code
        review agents without modifying files.

    Functioning:
        Walks the workspace root, excludes runtime/cache directories, classifies
        files by type, size and risk, and scans small text files for synthetic
        secret-like content using SecretGuard.

    Integration:
        Exposed through CLI command `repo-inventory`; reports can be written via
        ReportEngine and results are persisted best-effort in LocalStore.

    PASS:
        Inventory stays inside workspace, emits JSON, redacts no raw secret
        values, and flags sensitive files as findings.

    BLOCK:
        Root outside workspace, path policy violation or inventory traversal
        outside the project root.

    Risks:
        This is not a full SAST/SCA scanner. Binary secret scanning, entropy
        analysis, dependency vulnerability checks and license analysis remain
        future work.
    """

    def __init__(self, root: Path, *, config: RepoInventoryConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or RepoInventoryConfig()
        self.secret_guard = SecretGuard()

    def build(self) -> CommandResult:
        decision = PathGuard(self.root).evaluate(".", action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="repo-inventory",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Repository inventory blocked by path policy.",
                findings=[Finding(id=decision.rule_id, message=decision.reason, severity=Severity.BLOCK, path=decision.subject)],
            )

        items: list[RepoInventoryItem] = []
        findings: list[Finding] = []
        skipped_dirs: set[str] = set()
        for path in sorted(self.root.rglob("*")):
            if _is_inside_excluded_dir(path, self.root, self.config.excluded_dirs):
                rel_dir = _display_path(_first_excluded_parent(path, self.root, self.config.excluded_dirs), self.root)
                skipped_dirs.add(rel_dir)
                continue
            if not path.is_file():
                continue
            try:
                path.resolve().relative_to(self.root)
            except ValueError:
                return CommandResult(
                    command="repo-inventory",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message="Repository inventory attempted to leave workspace root.",
                    findings=[Finding(id="REPO_INVENTORY_OUTSIDE_ROOT", message="Inventory traversal left workspace root.", severity=Severity.BLOCK, path=str(path))],
                )
            if len(items) >= self.config.max_files:
                findings.append(Finding(id="REPO_INVENTORY_FILE_LIMIT_REACHED", message="Inventory reached configured max_files limit.", severity=Severity.WARNING, metadata={"max_files": self.config.max_files}))
                break
            item = self._inspect_file(path)
            items.append(item)
            if item.risk == "high":
                findings.append(Finding(id="REPO_INVENTORY_HIGH_RISK_FILE", message="High-risk file pattern detected.", severity=Severity.WARNING, path=item.path, metadata={"reasons": item.reasons}))
            elif item.risk == "medium":
                findings.append(Finding(id="REPO_INVENTORY_MEDIUM_RISK_FILE", message="Medium-risk file pattern detected.", severity=Severity.WARNING, path=item.path, metadata={"reasons": item.reasons}))
            if item.secret_like:
                findings.append(Finding(id="REPO_INVENTORY_SECRET_LIKE_CONTENT", message="Secret-like content detected and not emitted in inventory output.", severity=Severity.WARNING, path=item.path))

        summary = _summarize(items, skipped_dirs)
        return CommandResult(
            command="repo-inventory",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Repository inventory generated in read-only mode.",
            data={
                "summary": summary,
                "items": [item.to_dict() for item in items],
                "preliminary": True,
                "notes": [
                    "FUNC-SPRINT-14 inventory is read-only and local-first.",
                    "Secret-like values are detected but raw file contents are never emitted.",
                ],
            },
            findings=findings or [Finding(id="REPO_INVENTORY_PASS", message="Repository inventory completed without risk findings.", severity=Severity.INFO)],
        )

    def _inspect_file(self, path: Path) -> RepoInventoryItem:
        rel = _display_path(path, self.root)
        size = path.stat().st_size
        suffix = path.suffix.lower()
        category = _category_for(path)
        risk = "low"
        reasons: list[str] = []
        name_lower = path.name.lower()
        if name_lower in _HIGH_RISK_NAMES or suffix in _HIGH_RISK_SUFFIXES:
            risk = "high"
            reasons.append("sensitive_filename_or_suffix")
        elif suffix in _MEDIUM_RISK_SUFFIXES:
            risk = "medium"
            reasons.append("state_or_lock_file")
        secret_like = False
        if suffix in _TEXT_SUFFIXES or path.name.lower().startswith(".env"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[: self.config.max_secret_scan_bytes]
            except OSError:
                text = ""
            redaction = self.secret_guard.redact(text)
            if redaction.changed:
                secret_like = True
                risk = "high"
                reasons.append("secret_like_content")
        return RepoInventoryItem(path=rel, size_bytes=size, suffix=suffix, category=category, risk=risk, secret_like=secret_like, reasons=reasons)


def _category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".md", ".rst"}:
        return "documentation"
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"} or path.name.startswith("."):
        return "configuration"
    if suffix in {".db", ".sqlite", ".lock"}:
        return "state"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
        return "asset"
    return "other"


def _summarize(items: list[RepoInventoryItem], skipped_dirs: set[str]) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    by_risk: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    total_size = 0
    secret_like = 0
    for item in items:
        by_category[item.category] = by_category.get(item.category, 0) + 1
        by_risk[item.risk] = by_risk.get(item.risk, 0) + 1
        total_size += item.size_bytes
        if item.secret_like:
            secret_like += 1
    return {
        "files_total": len(items),
        "size_bytes_total": total_size,
        "by_category": by_category,
        "by_risk": by_risk,
        "secret_like_files": secret_like,
        "skipped_dirs": sorted(skipped_dirs),
    }


def _is_inside_excluded_dir(path: Path, root: Path, excluded_dirs: tuple[str, ...]) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in excluded_dirs for part in parts[:-1] if part)


def _first_excluded_parent(path: Path, root: Path, excluded_dirs: tuple[str, ...]) -> Path:
    try:
        rel_parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return path
    current = root
    for part in rel_parts:
        current = current / part
        if part in excluded_dirs:
            return current
    return path.parent


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/") or "."
    except ValueError:
        return str(path).replace("\\", "/")
