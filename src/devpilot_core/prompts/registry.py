from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.prompts.safety import PromptSafetyChecker, redact_prompt_text
from devpilot_core.schemas import SchemaValidator

PROMPT_REGISTRY_DIR = Path("docs/prompts")
PROMPT_SCHEMA_CONTRACT = "Prompt"
_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}|\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class PromptSpec:
    """Versioned prompt contract owned by DevPilot docs-as-code."""

    prompt_id: str
    version: str
    status: str
    owner: str
    task: str
    agent_id: str | None
    description: str
    input_variables: list[dict[str, Any]] = field(default_factory=list)
    template: str = ""
    safety: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PromptSpec":
        return cls(
            prompt_id=str(payload.get("id") or "").strip(),
            version=str(payload.get("version") or "").strip(),
            status=str(payload.get("status") or "").strip(),
            owner=str(payload.get("owner") or "").strip(),
            task=str(payload.get("task") or "").strip(),
            agent_id=(str(payload.get("agent_id")).strip() if payload.get("agent_id") is not None else None),
            description=str(payload.get("description") or "").strip(),
            input_variables=list(payload.get("input_variables") or []),
            template=str(payload.get("template") or ""),
            safety=dict(payload.get("safety") or {}),
            usage=dict(payload.get("usage") or {}),
            metadata=dict(payload.get("metadata") or {}),
        )

    def reference(self) -> dict[str, str | None]:
        return {"prompt_id": self.prompt_id, "version": self.version, "agent_id": self.agent_id, "task": self.task}

    def declared_input_names(self) -> list[str]:
        names: list[str] = []
        for item in self.input_variables:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name:
                    names.append(name)
        return names

    def required_input_names(self) -> list[str]:
        names: list[str] = []
        for item in self.input_variables:
            if isinstance(item, dict) and item.get("required", False):
                name = str(item.get("name") or "").strip()
                if name:
                    names.append(name)
        return names

    def placeholders(self) -> list[str]:
        return sorted({(match.group(1) or match.group(2)) for match in _PLACEHOLDER_PATTERN.finditer(self.template)})

    def to_dict(self, *, include_template: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.prompt_id,
            "version": self.version,
            "status": self.status,
            "owner": self.owner,
            "task": self.task,
            "agent_id": self.agent_id,
            "description": self.description,
            "input_variables": self.input_variables,
            "safety": self.safety,
            "usage": self.usage,
            "metadata": self.metadata,
            "template_sha256": _sha256_text(self.template),
            "template_redacted": True,
        }
        if include_template:
            payload["template"] = redact_prompt_text(self.template)
        return payload


@dataclass(frozen=True)
class PromptRecord:
    """PromptSpec plus file path and raw payload for schema validation."""

    spec: PromptSpec
    path: Path
    payload: dict[str, Any]

    def to_dict(self, *, include_template: bool = False, root: Path | None = None) -> dict[str, Any]:
        data = self.spec.to_dict(include_template=include_template)
        data["path"] = _relative(self.path, root) if root else self.path.as_posix()
        return data


@dataclass(frozen=True)
class RenderedPrompt:
    """Rendered prompt returned internally to model routing code."""

    text: str
    spec: PromptSpec
    inputs_used: dict[str, str]
    safety_findings: list[Finding]

    def reference_payload(self) -> dict[str, Any]:
        return {
            **self.spec.reference(),
            "inputs_used": sorted(self.inputs_used.keys()),
            "payload_redacted": True,
            "raw_prompt_stored": False,
            "preliminary": True,
        }


class PromptRegistry:
    """Read-only Prompt Registry for DevPilot prompt contracts.

    FUNC-SPRINT-49 stores prompts as versioned JSON contracts under
    `docs/prompts/`. The registry is local-first, dependency-free beyond the
    existing SchemaValidator, and never writes prompts from CLI commands.
    """

    def __init__(self, root: Path, prompts_dir: str | Path = PROMPT_REGISTRY_DIR) -> None:
        self.root = Path(root).resolve()
        self.prompts_dir = Path(prompts_dir)
        self.validator = SchemaValidator(self.root)
        self.safety_checker = PromptSafetyChecker()

    @property
    def resolved_prompts_dir(self) -> Path:
        candidate = self.prompts_dir
        return candidate if candidate.is_absolute() else self.root / candidate

    def load_records(self) -> tuple[list[PromptRecord], list[Finding]]:
        findings: list[Finding] = []
        records: list[PromptRecord] = []
        directory = self.resolved_prompts_dir
        if not directory.exists():
            return [], [Finding(id="PROMPT_REGISTRY_DIR_MISSING", message="Prompt registry directory is missing.", severity=Severity.BLOCK, path=_relative(directory, self.root))]
        for path in sorted(directory.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                findings.append(Finding(id="PROMPT_FILE_INVALID_JSON", message=str(exc), severity=Severity.ERROR, path=_relative(path, self.root)))
                continue
            if not isinstance(payload, dict):
                findings.append(Finding(id="PROMPT_FILE_NOT_OBJECT", message="Prompt file must contain one JSON object.", severity=Severity.BLOCK, path=_relative(path, self.root)))
                continue
            records.append(PromptRecord(spec=PromptSpec.from_payload(payload), path=path, payload=payload))
        if not records and not findings:
            findings.append(Finding(id="PROMPT_REGISTRY_EMPTY", message="Prompt registry has no JSON prompt contracts.", severity=Severity.BLOCK, path=_relative(directory, self.root)))
        findings.extend(self._semantic_findings(records))
        return records, findings

    def list(self) -> CommandResult:
        records, findings = self.load_records()
        blocking = _blocking_findings(findings)
        prompts = [record.to_dict(include_template=False, root=self.root) for record in records]
        return CommandResult(
            command="prompt list",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Prompt Registry listed successfully." if not blocking else "Prompt Registry has blocking findings.",
            data={
                "summary": self._summary(records, findings),
                "prompts": prompts,
                "notes": [
                    "FUNC-SPRINT-49 keeps prompts versioned as docs-as-code JSON contracts.",
                    "Prompt list never emits raw rendered prompts or secrets.",
                ],
            },
            findings=findings or [Finding(id="PROMPT_REGISTRY_LIST_PASS", message="Prompt Registry loaded without findings.", severity=Severity.INFO)],
        )

    def validate(self, *, prompt_id: str | None = None) -> CommandResult:
        records, findings = self.load_records()
        selected = [record for record in records if prompt_id is None or record.spec.prompt_id == prompt_id]
        if prompt_id and not selected:
            findings.append(Finding(id="PROMPT_NOT_FOUND", message=f"Prompt id '{prompt_id}' was not found.", severity=Severity.BLOCK, metadata={"prompt_id": prompt_id}))
        schema_results: list[dict[str, Any]] = []
        for record in selected:
            result = self.validator.validate_payload(schema=PROMPT_SCHEMA_CONTRACT, payload=record.payload, instance_label=_relative(record.path, self.root))
            schema_results.append(result.to_dict())
            for finding in result.findings:
                findings.append(finding)
            safety = self.safety_checker.check(record.spec.template, subject=f"prompt:{record.spec.prompt_id}@{record.spec.version}")
            for finding in safety.findings:
                if finding.id != "PROMPT_SAFETY_PASS":
                    findings.append(Finding(id=finding.id, message=finding.message, severity=finding.severity, path=_relative(record.path, self.root), metadata=finding.metadata))
        blocking = _blocking_findings(findings)
        return CommandResult(
            command="prompt validate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Prompt Registry validation passed." if not blocking else "Prompt Registry validation failed.",
            data={
                "summary": {
                    **self._summary(selected if prompt_id else records, findings),
                    "prompt_id": prompt_id,
                    "schema_validations_total": len(schema_results),
                    "schema_validations_failed": sum(1 for result in schema_results if not result.get("ok")),
                    "external_api_used": False,
                    "network_used": False,
                    "preliminary": True,
                },
                "schema_results": schema_results,
                "notes": [
                    "Prompt validation combines JSON Schema, semantic registry checks and basic PromptSafetyChecker findings.",
                    "Prompt injection checks are basic deterministic controls, not a complete adversarial defense.",
                ],
            },
            findings=findings or [Finding(id="PROMPT_REGISTRY_VALIDATE_PASS", message="All prompt contracts passed validation.", severity=Severity.INFO)],
        )

    def show(self, prompt_id: str, *, version: str | None = None) -> CommandResult:
        record = self.get(prompt_id, version=version)
        if record is None:
            return CommandResult(
                command="prompt show",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Prompt was not found.",
                data={"summary": {"prompt_id": prompt_id, "version": version, "found": False, "external_api_used": False, "preliminary": True}},
                findings=[Finding(id="PROMPT_NOT_FOUND", message=f"Prompt id/version not found: {prompt_id} {version or ''}".strip(), severity=Severity.BLOCK, metadata={"prompt_id": prompt_id, "version": version})],
            )
        safety = self.safety_checker.check(record.spec.template, subject=f"prompt:{record.spec.prompt_id}@{record.spec.version}")
        findings = [finding for finding in safety.findings if finding.id != "PROMPT_SAFETY_PASS"]
        if not findings:
            findings = [Finding(id="PROMPT_SHOW_PASS", message="Prompt contract returned with redacted template payload.", severity=Severity.INFO, metadata={"prompt_id": record.spec.prompt_id, "version": record.spec.version, "payload_redacted": True})]
        return CommandResult(
            command="prompt show",
            ok=not _blocking_findings(findings),
            exit_code=ExitCode.PASS if not _blocking_findings(findings) else ExitCode.BLOCK,
            message="Prompt contract returned." if not _blocking_findings(findings) else "Prompt contract contains blocking safety findings.",
            data={
                "summary": {
                    "prompt_id": record.spec.prompt_id,
                    "version": record.spec.version,
                    "status": record.spec.status,
                    "task": record.spec.task,
                    "agent_id": record.spec.agent_id,
                    "template_redacted": True,
                    "external_api_used": False,
                    "network_used": False,
                    "preliminary": True,
                },
                "prompt": record.to_dict(include_template=True, root=self.root),
                "safety": safety.to_dict(),
                "notes": ["Prompt show is read-only and emits a redacted template representation only."],
            },
            findings=findings,
        )

    def get(self, prompt_id: str, *, version: str | None = None) -> PromptRecord | None:
        records, _findings = self.load_records()
        matches = [record for record in records if record.spec.prompt_id == prompt_id]
        if version:
            matches = [record for record in matches if record.spec.version == version]
        if not matches:
            return None
        return sorted(matches, key=lambda record: _version_tuple(record.spec.version), reverse=True)[0]

    def render(self, prompt_id: str, *, version: str | None = None, inputs: dict[str, str] | None = None) -> tuple[RenderedPrompt | None, CommandResult | None]:
        record = self.get(prompt_id, version=version)
        if record is None:
            return None, CommandResult(
                command="prompt render",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Prompt render blocked because prompt id/version was not found.",
                data={"summary": {"prompt_id": prompt_id, "version": version, "external_api_used": False, "preliminary": True}},
                findings=[Finding(id="PROMPT_NOT_FOUND", message=f"Prompt id/version not found: {prompt_id} {version or ''}".strip(), severity=Severity.BLOCK, metadata={"prompt_id": prompt_id, "version": version})],
            )
        input_values = dict(inputs or {})
        required = set(record.spec.required_input_names())
        missing = sorted(name for name in required if name not in input_values or input_values[name] == "")
        declared = set(record.spec.declared_input_names())
        unknown = sorted(name for name in input_values if name not in declared)
        findings: list[Finding] = []
        if missing:
            findings.append(Finding(id="PROMPT_INPUT_REQUIRED_MISSING", message="Required prompt inputs are missing.", severity=Severity.BLOCK, metadata={"prompt_id": prompt_id, "missing_inputs": missing, "payload_redacted": True}))
        if unknown:
            findings.append(Finding(id="PROMPT_INPUT_UNKNOWN", message="Prompt input contains undeclared keys.", severity=Severity.BLOCK, metadata={"prompt_id": prompt_id, "unknown_inputs": unknown, "payload_redacted": True}))
        if findings:
            return None, CommandResult(
                command="prompt render",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Prompt render blocked by input contract.",
                data={"summary": {"prompt_id": prompt_id, "version": record.spec.version, "payload_redacted": True, "external_api_used": False, "preliminary": True}},
                findings=findings,
            )
        rendered = record.spec.template
        for key, value in input_values.items():
            rendered = re.sub(r"\{\{\s*" + re.escape(key) + r"\s*\}\}", value, rendered)
            rendered = rendered.replace("{" + key + "}", value)
        safety = self.safety_checker.check(rendered, subject=f"prompt-render:{record.spec.prompt_id}@{record.spec.version}")
        blocking = _blocking_findings([finding for finding in safety.findings if finding.id != "PROMPT_SAFETY_PASS"])
        if blocking:
            return None, CommandResult(
                command="prompt render",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Prompt render blocked by PromptSafetyChecker.",
                data={"summary": {**record.spec.reference(), "payload_redacted": True, "external_api_used": False, "preliminary": True}, "safety": safety.to_dict()},
                findings=[finding for finding in safety.findings if finding.id != "PROMPT_SAFETY_PASS"],
            )
        return RenderedPrompt(text=rendered, spec=record.spec, inputs_used=input_values, safety_findings=safety.findings), None

    def _semantic_findings(self, records: list[PromptRecord]) -> list[Finding]:
        findings: list[Finding] = []
        seen: dict[tuple[str, str], Path] = {}
        for record in records:
            spec = record.spec
            path = _relative(record.path, self.root)
            key = (spec.prompt_id, spec.version)
            if key in seen:
                findings.append(Finding(id="PROMPT_DUPLICATE_ID_VERSION", message="Duplicate prompt id/version detected.", severity=Severity.BLOCK, path=path, metadata={"prompt_id": spec.prompt_id, "version": spec.version, "first_path": _relative(seen[key], self.root)}))
            else:
                seen[key] = record.path
            if not _VERSION_PATTERN.match(spec.version):
                findings.append(Finding(id="PROMPT_VERSION_INVALID", message="Prompt version must follow semver-like MAJOR.MINOR.PATCH.", severity=Severity.BLOCK, path=path, metadata={"prompt_id": spec.prompt_id, "version": spec.version}))
            declared = set(spec.declared_input_names())
            placeholders = set(spec.placeholders())
            missing_declarations = sorted(placeholders - declared)
            unused_declarations = sorted(declared - placeholders)
            if missing_declarations:
                findings.append(Finding(id="PROMPT_PLACEHOLDER_UNDECLARED", message="Prompt template uses placeholders not declared as inputs.", severity=Severity.BLOCK, path=path, metadata={"prompt_id": spec.prompt_id, "placeholders": missing_declarations}))
            if unused_declarations:
                findings.append(Finding(id="PROMPT_INPUT_DECLARED_UNUSED", message="Prompt declares inputs not used in template.", severity=Severity.WARNING, path=path, metadata={"prompt_id": spec.prompt_id, "inputs": unused_declarations}))
            safety = spec.safety or {}
            if safety.get("store_raw_prompt", False):
                findings.append(Finding(id="PROMPT_RAW_STORAGE_DENIED", message="Prompt contract cannot request raw prompt storage.", severity=Severity.BLOCK, path=path, metadata={"prompt_id": spec.prompt_id}))
        return findings

    def _summary(self, records: list[PromptRecord], findings: list[Finding]) -> dict[str, Any]:
        statuses: dict[str, int] = {}
        for record in records:
            statuses[record.spec.status] = statuses.get(record.spec.status, 0) + 1
        return {
            "prompts_total": len(records),
            "prompt_versions_total": len(records),
            "findings_total": len(findings),
            "blocking_findings_total": len(_blocking_findings(findings)),
            "status_counts": statuses,
            "schema_contract": PROMPT_SCHEMA_CONTRACT,
            "registry_path": _relative(self.resolved_prompts_dir, self.root),
            "external_api_used": False,
            "network_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]


def _version_tuple(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    values: list[int] = []
    for part in parts[:3]:
        try:
            values.append(int(part))
        except ValueError:
            values.append(-1)
    while len(values) < 3:
        values.append(-1)
    return tuple(values)  # type: ignore[return-value]


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _relative(path: Path, root: Path | None = None) -> str:
    if root is not None:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return path.as_posix()
