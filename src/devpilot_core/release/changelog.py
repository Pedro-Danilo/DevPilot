from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
_SPRINT_RE = re.compile(r"(?:FUNC-SPRINT-|functional_sprint_)(\d+)")

_KEEP_A_CHANGELOG_CATEGORIES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

_SECURITY_MARKERS = (
    "secret",
    "secreto",
    "api externa",
    "external api",
    "public",
    "publish",
    "deploy",
    "desplieg",
    "destruct",
    "runtime db",
    "runtime state",
    "outputs",
    "cache",
)


@dataclass(frozen=True)
class ReleaseChangelogOptions:
    """Options for generating a local release changelog.

    The generator is deliberately evidence-driven. It reads local sprint
    manifests and creates a human-readable changelog without calling GitHub,
    external APIs, package registries or LLMs. It never overwrites the canonical
    `docs/release/CHANGELOG.md`; optional report writing is handled by the CLI
    below `outputs/reports`.
    """

    version: str
    from_sprint: str = "FUNC-SPRINT-74"
    to_sprint: str | None = None
    channel: str = "local-candidate"


class ReleaseChangelogBuilder:
    """Build a Keep a Changelog-compatible changelog from local evidence.

    FUNC-SPRINT-78 introduces a deterministic changelog generator over
    `docs/functional_sprint_*_manifest.json`. The output is suitable as release
    evidence, but not a publication mechanism. It does not tag Git, does not
    publish artifacts and does not mutate source files.
    """

    def __init__(self, root: Path, *, options: ReleaseChangelogOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        if not _SEMVER_RE.match(self.options.version):
            findings.append(
                Finding(
                    "CHANGELOG_VERSION_INVALID",
                    "Changelog version must follow SemVer MAJOR.MINOR.PATCH, optionally with prerelease/build metadata.",
                    Severity.ERROR,
                    metadata={"version": self.options.version},
                )
            )
            return CommandResult(
                command="release changelog",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release changelog generation failed because the version is invalid.",
                data={"summary": self._summary_template(valid_version=False)},
                findings=findings,
            )

        from_number = _sprint_number(self.options.from_sprint)
        to_number = _sprint_number(self.options.to_sprint) if self.options.to_sprint else None
        if from_number is None or (self.options.to_sprint and to_number is None):
            findings.append(
                Finding(
                    "CHANGELOG_SPRINT_RANGE_INVALID",
                    "Sprint range must use FUNC-SPRINT-XX identifiers.",
                    Severity.ERROR,
                    metadata={"from_sprint": self.options.from_sprint, "to_sprint": self.options.to_sprint},
                )
            )
            return CommandResult(
                command="release changelog",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Release changelog generation failed because the sprint range is invalid.",
                data={"summary": self._summary_template(valid_version=True)},
                findings=findings,
            )

        manifests = self._load_manifests(from_number=from_number, to_number=to_number)
        if not manifests:
            findings.append(
                Finding(
                    "CHANGELOG_NO_MANIFESTS_FOUND",
                    "No functional sprint manifests were found for the requested changelog range.",
                    Severity.BLOCK,
                    metadata={"from_sprint": self.options.from_sprint, "to_sprint": self.options.to_sprint},
                )
            )
            return CommandResult(
                command="release changelog",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Release changelog generation failed because there is no local manifest evidence.",
                data={"summary": self._summary_template(valid_version=True)},
                findings=findings,
            )

        changelog = self._build_changelog_payload(manifests)
        findings.append(
            Finding(
                "RELEASE_CHANGELOG_CREATED",
                "Release changelog was generated from local sprint manifests without network, publication or source mutation.",
                Severity.INFO,
                metadata={"version": self.options.version, "manifests_total": len(manifests)},
            )
        )
        summary = {
            **self._summary_template(valid_version=True),
            "release_id": f"DEVPL-{self.options.version}",
            "release_status": "candidate-local",
            "manifests_total": len(manifests),
            "categories": _KEEP_A_CHANGELOG_CATEGORIES,
            "categories_total": len(_KEEP_A_CHANGELOG_CATEGORIES),
            "entries_total": sum(len(changelog["sections"][category]) for category in _KEEP_A_CHANGELOG_CATEGORIES),
            "source_manifests_total": len(changelog["source_manifests"]),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return CommandResult(
            command="release changelog",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release changelog generated.",
            data={
                "summary": summary,
                "changelog": changelog,
                "changelog_markdown": self.render_markdown(changelog),
                "notes": [
                    "FUNC-SPRINT-78 introduces an evidence-driven changelog generator only.",
                    "The changelog is generated from local sprint manifests and does not invent changes outside that evidence.",
                    "The CLI never overwrites docs/release/CHANGELOG.md; --write-report persists evidence only under outputs/reports.",
                    "Packaging, SBOM, checksums, signing, tagging and publication remain out of scope for this sprint.",
                ],
            },
            findings=findings,
        )

    def _summary_template(self, *, valid_version: bool) -> dict[str, Any]:
        return {
            "version": self.options.version,
            "valid_version": valid_version,
            "channel": self.options.channel,
            "schema_version": "1.0.0",
            "dry_run": True,
            "preliminary": True,
        }

    def _load_manifests(self, *, from_number: int, to_number: int | None) -> list[dict[str, Any]]:
        manifests: list[dict[str, Any]] = []
        for path in sorted((self.root / "docs").glob("functional_sprint_*_manifest.json")):
            number = _sprint_number(path.name)
            if number is None or number < from_number:
                continue
            if to_number is not None and number > to_number:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if payload.get("status") != "implemented":
                continue
            payload["_path"] = _relative(path, self.root)
            payload["_sprint_number"] = number
            manifests.append(payload)
        return sorted(manifests, key=lambda item: int(item.get("_sprint_number", 0)))

    def _build_changelog_payload(self, manifests: list[dict[str, Any]]) -> dict[str, Any]:
        sections = {category: [] for category in _KEEP_A_CHANGELOG_CATEGORIES}
        references: list[dict[str, Any]] = []

        for manifest in manifests:
            sprint = str(manifest.get("sprint", "UNKNOWN-SPRINT"))
            title = str(manifest.get("title", sprint))
            audit = manifest.get("audit_report")
            source_manifest = str(manifest.get("_path"))
            summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}

            sections["Added"].append(
                _entry(
                    sprint,
                    title,
                    f"Se incorporó `{_short_title(title, sprint)}`.",
                    source_manifest,
                    audit,
                    details=_summarize_paths(manifest.get("created_files") or []),
                )
            )
            modified = manifest.get("modified_files") or []
            if modified:
                sections["Changed"].append(
                    _entry(
                        sprint,
                        title,
                        "Se sincronizaron artefactos de ingeniería y contratos existentes.",
                        source_manifest,
                        audit,
                        details=_summarize_paths(modified),
                    )
                )
            if _has_security_marker(manifest):
                sections["Security"].append(
                    _entry(
                        sprint,
                        title,
                        "Se preservaron límites local-first/dry-run-first, exclusión de secretos/runtime state o bloqueo de publicación/despliegue según el contrato del sprint.",
                        source_manifest,
                        audit,
                        details=_summary_security_details(summary),
                    )
                )
            if _has_fixed_marker(manifest):
                sections["Fixed"].append(
                    _entry(
                        sprint,
                        title,
                        "Se registró una corrección soportada por el manifest funcional del sprint.",
                        source_manifest,
                        audit,
                        details=_summarize_text_list(manifest.get("pass_criteria") or []),
                    )
                )
            references.append(
                {
                    "sprint": sprint,
                    "title": title,
                    "manifest": source_manifest,
                    "audit_report": audit,
                    "commands_total": len(manifest.get("commands") or []),
                    "tests_total": len(manifest.get("tests") or []),
                }
            )

        return {
            "schema_version": "1.0.0",
            "changelog_id": f"CHANGELOG-{_safe_release_id(self.options.version)}",
            "release_id": f"DEVPL-{self.options.version}",
            "release_version": self.options.version,
            "release_channel": self.options.channel,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "format": "keep-a-changelog-compatible",
            "source": "docs/functional_sprint_*_manifest.json",
            "from_sprint": self.options.from_sprint,
            "to_sprint": references[-1]["sprint"] if references else self.options.to_sprint,
            "sections": sections,
            "source_manifests": references,
            "policy": {
                "invented_changes_allowed": False,
                "manual_overwrite_allowed": False,
                "write_scope": "reports-only-when-write-report",
                "canonical_changelog_path": "docs/release/CHANGELOG.md",
            },
            "security": {
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "source_mutations_performed": False,
                "secrets_embedded": False,
            },
            "limitations": [
                "FUNC-SPRINT-78 does not build packages, tag Git, publish releases or deploy.",
                "The generated changelog is evidence-driven and depends on manifest quality.",
                "Commit parsing is not used as the source of truth in this first version to keep the output stable in ZIP-based workflows.",
            ],
        }

    def render_markdown(self, changelog: dict[str, Any]) -> str:
        lines = [
            "# Changelog",
            "",
            "All notable changes to DevPilot Local are documented in this file.",
            "",
            "This changelog follows a Keep a Changelog-compatible category structure and is generated from local sprint manifests.",
            "",
            f"## [{changelog['release_version']}] - {changelog['generated_at_utc'][:10]}",
            "",
            f"Release ID: `{changelog['release_id']}`  ",
            f"Range: `{changelog['from_sprint']}` → `{changelog['to_sprint']}`  ",
            f"Source: `{changelog['source']}`",
            "",
        ]
        sections = changelog.get("sections") or {}
        for category in _KEEP_A_CHANGELOG_CATEGORIES:
            lines.append(f"### {category}")
            lines.append("")
            entries = sections.get(category) or []
            if not entries:
                lines.append("- No entries declared by local sprint manifests for this category.")
            else:
                for entry in entries:
                    lines.append(
                        f"- `{entry['sprint']}` — {entry['message']} "
                        f"Source: `{entry['source_manifest']}`"
                        + (f"; audit: `{entry['audit_report']}`" if entry.get("audit_report") else "")
                        + (f". {entry['details']}" if entry.get("details") else "")
                    )
            lines.append("")
        lines.extend(["### References", ""])
        for item in changelog.get("source_manifests") or []:
            lines.append(f"- `{item['sprint']}` — `{item['manifest']}`")
        lines.extend(
            [
                "",
                "### Policy notes",
                "",
                "- The changelog must not invent changes outside local manifests, commits or approved docs.",
                "- The CLI does not overwrite `docs/release/CHANGELOG.md`; report writing is limited to `outputs/reports`.",
                "- Publication, Git tagging, signing and packaging remain outside FUNC-SPRINT-78.",
                "",
            ]
        )
        return "\n".join(lines)


def _sprint_number(value: str | None) -> int | None:
    if not value:
        return None
    match = _SPRINT_RE.search(str(value))
    return int(match.group(1)) if match else None


def _safe_release_id(version: str) -> str:
    return re.sub(r"[^0-9A-Za-z.-]+", "-", version).upper()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _short_title(title: str, sprint: str) -> str:
    prefix = f"{sprint} — "
    if title.startswith(prefix):
        return title[len(prefix) :]
    return title


def _entry(
    sprint: str,
    title: str,
    message: str,
    source_manifest: str,
    audit_report: Any,
    *,
    details: str | None = None,
) -> dict[str, Any]:
    return {
        "sprint": sprint,
        "title": title,
        "message": message,
        "source_manifest": source_manifest,
        "audit_report": audit_report,
        "details": details,
    }


def _summarize_paths(paths: list[Any], *, limit: int = 4) -> str | None:
    clean = [str(path) for path in paths if str(path).strip()]
    if not clean:
        return None
    visible = ", ".join(f"`{path}`" for path in clean[:limit])
    remaining = len(clean) - limit
    if remaining > 0:
        visible += f" y {remaining} artefactos adicionales"
    return f"Artefactos: {visible}."


def _summarize_text_list(values: list[Any], *, limit: int = 2) -> str | None:
    clean = [str(value).strip() for value in values if str(value).strip()]
    if not clean:
        return None
    visible = "; ".join(clean[:limit])
    if len(clean) > limit:
        visible += f"; +{len(clean) - limit} criterios adicionales"
    return visible


def _has_security_marker(manifest: dict[str, Any]) -> bool:
    fragments: list[str] = []
    for key in ("block_criteria", "pass_criteria", "risks"):
        value = manifest.get(key)
        fragments.append(json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else "")
    text = "\n".join(fragments).lower()
    return any(marker in text for marker in _SECURITY_MARKERS)


def _has_fixed_marker(manifest: dict[str, Any]) -> bool:
    text = json.dumps(manifest, ensure_ascii=False, sort_keys=True).lower()
    return any(marker in text for marker in ("fixed", "fix", "corrección", "correg", "ajuste correctivo"))


def _summary_security_details(summary: dict[str, Any]) -> str | None:
    if not summary:
        return None
    interesting: list[str] = []
    for key, value in sorted(summary.items()):
        normalized = str(key).lower()
        if any(marker.replace(" ", "_") in normalized for marker in _SECURITY_MARKERS):
            interesting.append(f"`{key}={value}`")
    if not interesting:
        return None
    return "Controles declarados: " + ", ".join(interesting[:6]) + "."
