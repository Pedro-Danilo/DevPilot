from __future__ import annotations

from dataclasses import dataclass, field

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.policy.prompt_guard import PromptInjectionGuard
from devpilot_core.policy.secrets import SecretGuard, redact_sensitive_string


@dataclass(frozen=True)
class PromptSafetyReport:
    """Sanitized result of deterministic prompt safety checks.

    FUNC-SPRINT-49 deliberately keeps prompt safety local and dependency-free.
    The report records categories, severities and redaction counts, but never
    stores raw secret values or full untrusted prompt payloads in metadata.
    """

    ok: bool
    findings: list[Finding] = field(default_factory=list)
    redactions: int = 0
    injection_matches_total: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "findings_total": len(self.findings),
            "redactions": self.redactions,
            "injection_matches_total": self.injection_matches_total,
            "payload_redacted": True,
            "preliminary": True,
        }


class PromptSafetyChecker:
    """Basic local prompt safety checker for registry and rendered prompts.

    The checker composes DevPilot's existing SecretGuard and
    PromptInjectionGuard. It is not an LLM judge and does not claim full prompt
    injection coverage; it is a deterministic contract gate that catches obvious
    secrets, policy bypass wording and exfiltration instructions.
    """

    def __init__(self) -> None:
        self.secret_guard = SecretGuard()
        self.prompt_injection_guard = PromptInjectionGuard()

    def check(self, text: str | None, *, subject: str = "prompt") -> PromptSafetyReport:
        findings: list[Finding] = []
        redactions = 0
        injection_matches_total = 0
        ok = True

        secret_decision = self.secret_guard.scan_text(text, subject=subject)
        if secret_decision.effect.value != "allow":
            finding = secret_decision.to_finding()
            findings.append(
                Finding(
                    id=finding.id,
                    message=finding.message,
                    severity=finding.severity,
                    path=finding.path,
                    metadata={**(finding.metadata or {}), "prompt_subject": subject, "payload_redacted": True},
                )
            )
            redactions += int((secret_decision.metadata or {}).get("redactions") or 0)
            ok = False

        injection_decision = self.prompt_injection_guard.scan_text(text, subject=subject)
        if injection_decision.effect.value != "allow":
            finding = injection_decision.to_finding()
            severity = finding.severity
            if severity == Severity.BLOCK:
                ok = False
            metadata = dict(finding.metadata or {})
            injection_matches_total += int(metadata.get("matches_total") or 0)
            findings.append(
                Finding(
                    id=finding.id,
                    message=finding.message,
                    severity=severity,
                    path=finding.path,
                    metadata={**metadata, "prompt_subject": subject, "payload_redacted": True},
                )
            )

        if not findings:
            findings.append(
                Finding(
                    id="PROMPT_SAFETY_PASS",
                    message="PromptSafetyChecker did not detect secret or prompt-injection patterns.",
                    severity=Severity.INFO,
                    metadata={"prompt_subject": subject, "payload_redacted": True, "preliminary": True},
                )
            )
        return PromptSafetyReport(ok=ok, findings=findings, redactions=redactions, injection_matches_total=injection_matches_total)


def redact_prompt_text(value: str | None) -> str:
    """Return a prompt/template string safe for stdout and JSON reports."""

    if value is None:
        return ""
    redacted, _count = redact_sensitive_string(value)
    return redacted
