from __future__ import annotations

import json
import re
import tomllib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_PACKAGE_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class ReleaseSbomOptions:
    """Options for FUNC-SPRINT-80 local SBOM baseline generation.

    The SBOM builder is local-first and evidence-driven. It parses local project
    manifests such as `pyproject.toml`, `ui/web/package.json` and
    `ui/web/package-lock.json` without calling vulnerability databases,
    package registries, GitHub, PyPI, npm or external APIs.
    """

    version: str | None = None
    channel: str = "local-candidate"


class ReleaseSbomBuilder:
    """Create a local CycloneDX-compatible SBOM baseline for DevPilot.

    FUNC-SPRINT-80 intentionally implements an initial SBOM and supply-chain
    baseline, not a full SCA scanner. It inventories declared runtime/dev/build
    dependencies and locked UI packages when available, while preserving
    deterministic, no-network behavior.
    """

    def __init__(self, root: Path, *, options: ReleaseSbomOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ReleaseSbomOptions()

    def build(self) -> CommandResult:
        pyproject = self._read_pyproject()
        package_json = self._read_package_json()
        package_lock = self._read_package_lock()

        project = pyproject.get("project", {}) if isinstance(pyproject.get("project"), dict) else {}
        name = str(project.get("name") or "devpilot-local")
        version = str(self.options.version or project.get("version") or "0.0.0")

        python_runtime = [_dependency_record(dep, ecosystem="pypi", scope="required", group="runtime") for dep in project.get("dependencies") or []]
        optional_groups = project.get("optional-dependencies") if isinstance(project.get("optional-dependencies"), dict) else {}
        python_optional: list[dict[str, Any]] = []
        for group, deps in sorted(optional_groups.items()):
            for dep in deps or []:
                scope = "optional-dev" if group == "dev" else "optional"
                python_optional.append(_dependency_record(dep, ecosystem="pypi", scope=scope, group=str(group)))

        build_system = pyproject.get("build-system", {}) if isinstance(pyproject.get("build-system"), dict) else {}
        python_build = [_dependency_record(dep, ecosystem="pypi", scope="build", group="build-system") for dep in build_system.get("requires") or []]

        node_direct = self._node_direct_dependencies(package_json)
        node_locked = self._node_locked_components(package_lock)

        components = _deduplicate_components([
            *python_runtime,
            *python_optional,
            *python_build,
            *node_direct,
            *node_locked,
        ])
        cyclonedx_components = [_cyclonedx_component(item) for item in components]
        cyclonedx_bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, f'devpilot.local/sbom/{name}/{version}')}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "tools": [
                    {
                        "vendor": "DevPilot Local",
                        "name": "devpilot_core.release.ReleaseSbomBuilder",
                        "version": "FUNC-SPRINT-80",
                    }
                ],
                "component": {
                    "type": "application",
                    "name": name,
                    "version": version,
                    "purl": f"pkg:pypi/{name}@{version}",
                },
            },
            "components": cyclonedx_components,
        }
        sbom = {
            "schema_version": "1.0.0",
            "sbom_id": f"SBOM-{_safe_token(name)}-{_safe_token(version)}",
            "release_id": f"DEVPL-{version}",
            "release_version": version,
            "release_channel": self.options.channel,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": {
                "pyproject": "pyproject.toml",
                "pyproject_exists": bool(pyproject),
                "package_json": "ui/web/package.json",
                "package_json_exists": bool(package_json),
                "package_lock": "ui/web/package-lock.json",
                "package_lock_exists": bool(package_lock),
            },
            "project": {
                "name": name,
                "version": version,
                "requires_python": project.get("requires-python"),
            },
            "dependency_groups": {
                "python_runtime": python_runtime,
                "python_optional": python_optional,
                "python_build": python_build,
                "node_direct": node_direct,
                "node_locked": node_locked,
            },
            "components": components,
            "cyclonedx": cyclonedx_bom,
            "slsa_baseline": {
                "level": "local-baseline",
                "provenance_available": False,
                "build_service_attested": False,
                "artifact_signing_available": False,
                "source_control_integrity_checked": False,
                "rationale": "FUNC-SPRINT-80 creates a local inventory baseline; provenance, signing and attestation remain future release-hardening steps.",
            },
            "security": {
                "network_used": False,
                "external_api_used": False,
                "vulnerability_scan_performed": False,
                "license_scan_performed": False,
                "publish_performed": False,
                "deploy_performed": False,
                "source_mutations_performed": False,
                "secrets_embedded": False,
            },
            "limitations": [
                "FUNC-SPRINT-80 creates a local SBOM baseline only; it is not a complete SCA or vulnerability scanner.",
                "No external vulnerability, license, reputation or package-registry lookup is performed.",
                "CycloneDX output is compatibility-oriented and should evolve into a dedicated schema/validator in a later hardening sprint.",
                "Runtime, dev, optional, build and locked UI dependencies are inventoried from local manifests when present.",
            ],
        }
        summary = {
            "version": version,
            "channel": self.options.channel,
            "schema_version": "1.0.0",
            "preliminary": True,
            "sbom_id": sbom["sbom_id"],
            "release_id": sbom["release_id"],
            "components_total": len(components),
            "cyclonedx_components_total": len(cyclonedx_components),
            "python_runtime_dependencies_total": len(python_runtime),
            "python_optional_dependencies_total": len(python_optional),
            "python_dev_dependencies_total": sum(1 for item in python_optional if item.get("group") == "dev"),
            "python_build_dependencies_total": len(python_build),
            "node_direct_dependencies_total": len(node_direct),
            "node_locked_components_total": len(node_locked),
            "runtime_dependencies_declared": bool(python_runtime or [item for item in node_direct if item.get("scope") == "required"]),
            "dev_dependencies_declared": bool([item for item in python_optional if item.get("group") == "dev"] or [item for item in node_direct if item.get("scope") == "dev"]),
            "cyclonedx_compatible": True,
            "slsa_baseline_declared": True,
            "network_used": False,
            "external_api_used": False,
            "vulnerability_scan_performed": False,
            "license_scan_performed": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
        }
        findings = [
            Finding(
                "SBOM_BASELINE_CREATED",
                "Local SBOM baseline was generated from project manifests without network, external APIs or source mutation.",
                Severity.INFO,
                metadata={"components_total": len(components), "version": version},
            )
        ]
        return CommandResult(
            command="release sbom",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release SBOM baseline generated.",
            data={
                "summary": summary,
                "sbom": sbom,
                "sbom_markdown": self.render_markdown(sbom, summary),
                "notes": [
                    "FUNC-SPRINT-80 introduces a local SBOM and supply-chain baseline only.",
                    "The command parses local manifests and never calls vulnerability services, registries or external APIs.",
                    "The SBOM is CycloneDX-compatible at baseline level and must evolve with checksums, provenance and smoke-release evidence in later sprints.",
                ],
            },
            findings=findings,
        )

    def _read_pyproject(self) -> dict[str, Any]:
        path = self.root / "pyproject.toml"
        if not path.is_file():
            return {}
        return tomllib.loads(path.read_text(encoding="utf-8"))

    def _read_package_json(self) -> dict[str, Any]:
        path = self.root / "ui" / "web" / "package.json"
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _read_package_lock(self) -> dict[str, Any]:
        path = self.root / "ui" / "web" / "package-lock.json"
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _node_direct_dependencies(self, package_json: dict[str, Any]) -> list[dict[str, Any]]:
        if not package_json:
            return []
        records: list[dict[str, Any]] = []
        for section, scope in [("dependencies", "required"), ("devDependencies", "dev")]:
            deps = package_json.get(section) if isinstance(package_json.get(section), dict) else {}
            for name, specifier in sorted(deps.items()):
                records.append(
                    {
                        "ecosystem": "npm",
                        "name": str(name),
                        "specifier": str(specifier),
                        "version": None,
                        "scope": scope,
                        "group": section,
                        "direct": True,
                        "source": "ui/web/package.json",
                        "purl": f"pkg:npm/{name}",
                    }
                )
        return records

    def _node_locked_components(self, package_lock: dict[str, Any]) -> list[dict[str, Any]]:
        packages = package_lock.get("packages") if isinstance(package_lock.get("packages"), dict) else {}
        records: list[dict[str, Any]] = []
        for path, payload in sorted(packages.items()):
            if not path or not isinstance(payload, dict) or not path.startswith("node_modules/"):
                continue
            name = path.removeprefix("node_modules/")
            version = payload.get("version")
            records.append(
                {
                    "ecosystem": "npm",
                    "name": name,
                    "specifier": None,
                    "version": str(version) if version else None,
                    "scope": "dev" if payload.get("dev") is True else "required",
                    "group": "package-lock",
                    "direct": False,
                    "source": "ui/web/package-lock.json",
                    "purl": f"pkg:npm/{name}@{version}" if version else f"pkg:npm/{name}",
                    "optional": bool(payload.get("optional", False)),
                }
            )
        return records

    def render_markdown(self, sbom: dict[str, Any], summary: dict[str, Any]) -> str:
        groups = sbom.get("dependency_groups", {})
        lines = [
            "# DevPilot Local — SBOM baseline",
            "",
            f"Release: `{sbom.get('release_id')}`",
            f"Version: `{sbom.get('release_version')}`",
            "",
            "## 1. Resumen",
            "",
            f"- Components total: `{summary.get('components_total')}`",
            f"- Python runtime dependencies: `{summary.get('python_runtime_dependencies_total')}`",
            f"- Python dev dependencies: `{summary.get('python_dev_dependencies_total')}`",
            f"- Node direct dependencies: `{summary.get('node_direct_dependencies_total')}`",
            f"- Node locked components: `{summary.get('node_locked_components_total')}`",
            f"- CycloneDX compatible baseline: `{summary.get('cyclonedx_compatible')}`",
            "",
            "## 2. Python runtime dependencies",
            "",
            _table(groups.get("python_runtime") or []),
            "",
            "## 3. Python optional/dev/build dependencies",
            "",
            _table((groups.get("python_optional") or []) + (groups.get("python_build") or [])),
            "",
            "## 4. Node direct dependencies",
            "",
            _table(groups.get("node_direct") or []),
            "",
            "## 5. Supply-chain controls",
            "",
            "- No network calls.",
            "- No external vulnerability service calls.",
            "- No publication or deployment.",
            "- No source mutation.",
            "- SLSA baseline is declared as local-baseline only.",
            "",
            "## 6. Limitations",
            "",
        ]
        for item in sbom.get("limitations") or []:
            lines.append(f"- {item}")
        lines.append("")
        return "\n".join(lines)


def _dependency_record(requirement: str, *, ecosystem: str, scope: str, group: str) -> dict[str, Any]:
    name_match = _PACKAGE_NAME_RE.match(requirement)
    name = name_match.group(1) if name_match else requirement
    return {
        "ecosystem": ecosystem,
        "name": name,
        "specifier": requirement,
        "version": None,
        "scope": scope,
        "group": group,
        "direct": True,
        "source": "pyproject.toml",
        "purl": f"pkg:pypi/{name}",
    }


def _deduplicate_components(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str | None, str | None], dict[str, Any]] = {}
    for item in items:
        key = (str(item.get("ecosystem")), str(item.get("name")), item.get("version"), item.get("specifier"))
        if key not in merged:
            merged[key] = dict(item)
            merged[key]["groups"] = [item.get("group")]
        else:
            groups = merged[key].setdefault("groups", [])
            if item.get("group") not in groups:
                groups.append(item.get("group"))
    return sorted(merged.values(), key=lambda item: (str(item.get("ecosystem")), str(item.get("name")), str(item.get("version") or ""), str(item.get("specifier") or "")))


def _cyclonedx_component(item: dict[str, Any]) -> dict[str, Any]:
    component = {
        "type": "library",
        "name": item.get("name"),
        "scope": "required" if item.get("scope") in {"required", "build"} else "optional",
        "purl": item.get("purl"),
        "properties": [
            {"name": "devpilot:ecosystem", "value": str(item.get("ecosystem"))},
            {"name": "devpilot:group", "value": str(item.get("group"))},
            {"name": "devpilot:source", "value": str(item.get("source"))},
            {"name": "devpilot:direct", "value": str(bool(item.get("direct"))).lower()},
        ],
    }
    if item.get("version"):
        component["version"] = item.get("version")
    if item.get("specifier"):
        component["properties"].append({"name": "devpilot:specifier", "value": str(item.get("specifier"))})
    return component


def _table(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No dependencies declared in this category."
    lines = ["| Ecosystem | Name | Specifier/version | Scope | Source |", "|---|---|---|---|---|"]
    for item in items:
        version = item.get("version") or item.get("specifier") or "n/a"
        lines.append(f"| {item.get('ecosystem')} | `{item.get('name')}` | `{version}` | {item.get('scope')} | `{item.get('source')}` |")
    return "\n".join(lines)


def _safe_token(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", value)
