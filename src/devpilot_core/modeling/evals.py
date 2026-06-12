from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.budget import BudgetLedger
from devpilot_core.modeling.contracts import ModelProviderKind
from devpilot_core.modeling.health import ModelHealthService
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.modeling.router import ModelAdapterRouter, ModelRouterConfig
from devpilot_core.prompts import PromptRegistry
from devpilot_core.reports import ReportEngine

DEFAULT_MODEL_EVAL_SUITE = "model-local-smoke"
DEFAULT_MODEL_EVAL_FIXTURE = Path("evals/model_fixtures/model_eval_cases.json")
DEFAULT_MODEL_EVAL_OUTPUT = Path("outputs/evals/model_eval_matrix.json")


@dataclass(frozen=True)
class ModelEvalRunnerConfig:
    """Configuration for local model evaluation suites.

    FUNC-SPRINT-50 deliberately keeps evaluations offline and reproducible. By
    default the suite targets the deterministic mock provider; local providers
    can be selected, but unavailable/disabled providers are reported as skipped
    unless explicit execution is safe and configured.
    """

    suite_path: Path = DEFAULT_MODEL_EVAL_FIXTURE
    output_path: Path = DEFAULT_MODEL_EVAL_OUTPUT
    timeout_seconds: float = 3.0
    fallback_to_mock: bool = False


class ModelEvalRunner:
    """Evaluate model providers against versioned prompt fixtures.

    The runner executes small deterministic tasks through ModelAdapterRouter,
    integrates PromptRegistry references, records redacted BudgetLedger events,
    and emits a matrix with quality/cost/latency evidence. It never calls
    external API providers and never stores raw prompts, completions or secrets
    in its report payload.
    """

    def __init__(self, root: Path, *, config: ModelEvalRunnerConfig | None = None) -> None:
        self.root = Path(root).resolve()
        self.config = config or ModelEvalRunnerConfig()

    def run(
        self,
        *,
        suite: str = DEFAULT_MODEL_EVAL_SUITE,
        provider: str = "mock",
        model: str | None = None,
        case_id: str | None = None,
        write_report: bool = False,
    ) -> CommandResult:
        fixture = self._load_fixture(suite)
        cases = list(fixture.get("cases") or [])
        if case_id:
            cases = [case for case in cases if str(case.get("case_id")) == case_id]
            if not cases:
                return CommandResult(
                    command="model eval run",
                    ok=False,
                    exit_code=ExitCode.ERROR,
                    message="Requested model evaluation case was not found.",
                    data={"summary": {"suite": suite, "case_id": case_id, "provider": provider, "external_api_used": False, "preliminary": True}},
                    findings=[Finding(id="MODEL_EVAL_CASE_NOT_FOUND", message="Requested model eval case was not found.", severity=Severity.ERROR, metadata={"suite": suite, "case_id": case_id})],
                )

        provider_id = provider.strip().lower() or "mock"
        readiness = self._provider_readiness(provider_id)
        if not readiness["can_execute"]:
            result = self._skipped_result(suite=suite, provider=provider_id, model=model, cases=cases, readiness=readiness, fixture=fixture)
        else:
            result = self._execute_cases(suite=suite, provider=provider_id, model=model, cases=cases, fixture=fixture)

        if write_report:
            paths = self.write_matrix_report(result)
            data = dict(result.data or {})
            data["reports"] = paths
            result = CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)
        return result

    def write_matrix_report(self, result: CommandResult) -> dict[str, str]:
        """Write sanitized model eval matrix evidence under outputs/evals and outputs/reports."""

        output = self._resolve_inside_root(self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = result.to_dict()
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        report_paths = ReportEngine(self.root).write_command_report(
            result,
            report_id="model_eval_matrix",
            subject="evals/model_fixtures/model_eval_cases.json",
            metadata={"sprint": "FUNC-SPRINT-50", "component": "ModelEvalRunner"},
        )
        return {"matrix_json": _relative(output, self.root), **report_paths.to_dict()}

    def _execute_cases(self, *, suite: str, provider: str, model: str | None, cases: list[dict[str, Any]], fixture: dict[str, Any]) -> CommandResult:
        router = ModelAdapterRouter(
            self.root,
            config=ModelRouterConfig(
                local_timeout_seconds=self.config.timeout_seconds,
                fallback_to_mock_on_local_unavailable=self.config.fallback_to_mock,
            ),
        )
        rows: list[dict[str, Any]] = []
        findings: list[Finding] = []
        started = time.perf_counter()
        for case in cases:
            row, case_findings, command_result = self._run_case(case, router=router, provider=provider, model=model)
            rows.append(row)
            findings.extend(case_findings)
            if command_result is not None:
                BudgetLedger(self.root).record_model_result(command_result, source="model-eval-runner")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        failed_total = sum(1 for row in rows if row["status"] == "fail")
        passed_total = sum(1 for row in rows if row["status"] == "pass")
        skipped_total = sum(1 for row in rows if row["status"] == "skipped")
        cost_total = round(sum(float(row.get("cost_estimate_usd") or 0.0) for row in rows), 8)
        tokens_total = sum(int(row.get("tokens_estimated") or 0) for row in rows)
        if failed_total:
            findings.insert(0, Finding(id="MODEL_EVAL_MATRIX_FAIL", message="One or more model evaluation cases failed expected criteria.", severity=Severity.FAIL, metadata={"failed_total": failed_total}))
        else:
            findings.insert(0, Finding(id="MODEL_EVAL_MATRIX_PASS", message="Model evaluation matrix completed without failed cases.", severity=Severity.INFO, metadata={"passed_total": passed_total, "skipped_total": skipped_total}))
        ok = failed_total == 0
        return CommandResult(
            command="model eval run",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.FAIL,
            message="Model evaluation matrix passed." if ok else "Model evaluation matrix failed.",
            data={
                "summary": {
                    "suite": suite,
                    "provider": provider,
                    "model": model,
                    "cases_total": len(rows),
                    "passed_total": passed_total,
                    "failed_total": failed_total,
                    "skipped_total": skipped_total,
                    "tokens_estimated_total": tokens_total,
                    "cost_estimate_total_usd": cost_total,
                    "latency_ms_total": elapsed_ms,
                    "external_api_used": False,
                    "network_used": provider not in {"mock"},
                    "raw_prompts_stored": False,
                    "raw_outputs_stored": False,
                    "preliminary": True,
                },
                "matrix": rows,
                "fixture": {
                    "path": _relative(self._fixture_path(), self.root),
                    "schema_version": fixture.get("schema_version"),
                    "description": fixture.get("description"),
                },
                "notes": [
                    "FUNC-SPRINT-50 evaluates providers through ModelAdapterRouter and PromptRegistry.",
                    "Reports store prompt references, hashes and metrics only; raw prompts/completions are not persisted.",
                    "External API providers are never executed by this runner in Fase D.",
                ],
            },
            findings=findings,
        )

    def _run_case(self, case: dict[str, Any], *, router: ModelAdapterRouter, provider: str, model: str | None) -> tuple[dict[str, Any], list[Finding], CommandResult | None]:
        case_id = str(case.get("case_id") or "unnamed-case")
        task = str(case.get("task") or "generate").strip().lower()
        prompt_reference: dict[str, Any] | None = None
        rendered_text: str | None = None
        prompt_id = case.get("prompt_id")
        findings: list[Finding] = []
        if prompt_id:
            rendered, render_error = PromptRegistry(self.root).render(str(prompt_id), version=case.get("prompt_version"), inputs={str(k): str(v) for k, v in dict(case.get("inputs") or {}).items()})
            if render_error is not None:
                return self._case_row(case, status="fail", provider=provider, model=model, error_id="PROMPT_RENDER_FAILED", prompt_reference={"prompt_id": prompt_id, "payload_redacted": True}), [Finding(id="MODEL_EVAL_PROMPT_RENDER_FAILED", message="Prompt render failed for model eval case.", severity=Severity.FAIL, metadata={"case_id": case_id, "prompt_id": prompt_id, "payload_redacted": True})], None
            assert rendered is not None
            rendered_text = rendered.text
            prompt_reference = rendered.reference_payload()
        else:
            rendered_text = str(case.get("prompt") or case.get("text") or "")

        started = time.perf_counter()
        if task == "generate":
            command_result = router.generate(prompt=rendered_text or "", provider=provider, model=model)
        elif task == "classify":
            labels = tuple(str(label) for label in case.get("labels", []))
            command_result = router.classify(text=str(case.get("text") or rendered_text or ""), labels=labels, provider=provider, model=model)
        elif task == "embed":
            command_result = router.embed(text=str(case.get("text") or rendered_text or ""), provider=provider, model=model)
        else:
            return self._case_row(case, status="fail", provider=provider, model=model, error_id="MODEL_EVAL_TASK_UNSUPPORTED", prompt_reference=prompt_reference), [Finding(id="MODEL_EVAL_TASK_UNSUPPORTED", message="Unsupported model eval task.", severity=Severity.FAIL, metadata={"case_id": case_id, "task": task})], None
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        if prompt_reference:
            command_result = _attach_prompt_reference(command_result, prompt_reference)
        metrics = self._quality_metrics(case, command_result)
        status = "pass" if command_result.ok and metrics["quality_pass"] else "fail"
        if not command_result.ok:
            status = "fail"
        row = self._case_row(case, status=status, provider=provider, model=(command_result.data or {}).get("summary", {}).get("model") or model, prompt_reference=prompt_reference)
        row.update(
            {
                "latency_ms": latency_ms,
                "tokens_estimated": int((command_result.data or {}).get("summary", {}).get("tokens_estimated") or 0),
                "cost_estimate_usd": float((command_result.data or {}).get("summary", {}).get("cost_estimate_usd") or 0.0),
                "external_api_used": bool((command_result.data or {}).get("summary", {}).get("external_api_used") or False),
                "quality": metrics,
                "result_digest": _result_digest(command_result),
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            }
        )
        if status == "fail":
            findings.append(Finding(id="MODEL_EVAL_CASE_FAIL", message="Model eval case failed expected criteria.", severity=Severity.FAIL, metadata={"case_id": case_id, "task": task, "provider": provider, "payload_redacted": True}))
        return row, findings, command_result

    def _quality_metrics(self, case: dict[str, Any], result: CommandResult) -> dict[str, Any]:
        data = result.data or {}
        result_payload = dict(data.get("result") or {})
        task = str(case.get("task") or "generate")
        quality_pass = bool(result.ok)
        details: dict[str, Any] = {"result_ok": bool(result.ok)}
        if task == "generate":
            content = str(result_payload.get("content") or "")
            required = [str(value) for value in case.get("expected_contains", [])]
            missing = [value for value in required if value not in content]
            quality_pass = quality_pass and not missing
            details.update({"expected_contains_total": len(required), "missing_expected_total": len(missing), "content_length": len(content)})
        elif task == "classify":
            expected_label = case.get("expected_label")
            actual_label = result_payload.get("label")
            quality_pass = quality_pass and (expected_label is None or actual_label == expected_label)
            details.update({"expected_label": expected_label, "actual_label": actual_label})
        elif task == "embed":
            embedding = result_payload.get("embedding") or []
            min_dimensions = int(case.get("min_dimensions") or 1)
            quality_pass = quality_pass and len(embedding) >= min_dimensions
            details.update({"embedding_dimensions": len(embedding), "min_dimensions": min_dimensions})
        details["quality_pass"] = quality_pass
        return details

    def _case_row(self, case: dict[str, Any], *, status: str, provider: str, model: str | None, error_id: str | None = None, prompt_reference: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "case_id": str(case.get("case_id") or "unnamed-case"),
            "task": str(case.get("task") or "generate"),
            "provider": provider,
            "model": model,
            "prompt_id": (prompt_reference or {}).get("prompt_id") or case.get("prompt_id"),
            "prompt_version": (prompt_reference or {}).get("version") or case.get("prompt_version"),
            "prompt_inputs_used": (prompt_reference or {}).get("inputs_used") or sorted((case.get("inputs") or {}).keys()),
            "prompt_payload_redacted": True,
            "status": status,
            "error_id": error_id,
        }

    def _provider_readiness(self, provider_id: str) -> dict[str, Any]:
        registry = ProviderRegistry.load(self.root)
        provider = registry.get(provider_id)
        if provider is None:
            return {"can_execute": False, "availability": "unknown", "reason": "provider_not_registered", "provider": provider_id, "external_api_used": False}
        if provider.kind == ModelProviderKind.API:
            return {"can_execute": False, "availability": "blocked", "reason": "external_api_blocked", "provider": provider_id, "provider_config": provider.to_dict(), "external_api_used": False}
        if provider.kind == ModelProviderKind.MOCK:
            return {"can_execute": True, "availability": "available", "reason": "mock_offline", "provider": provider_id, "provider_config": provider.to_dict(), "external_api_used": False}
        if not provider.enabled:
            return {"can_execute": False, "availability": "disabled", "reason": "local_provider_disabled", "provider": provider_id, "provider_config": provider.to_dict(), "external_api_used": False}
        health = ModelHealthService(self.root, timeout_seconds=self.config.timeout_seconds).check_all()
        rows = {row.get("provider"): row for row in (health.data or {}).get("providers", [])}
        row = rows.get(provider_id, {})
        availability = row.get("availability", "unknown")
        return {"can_execute": availability == "available", "availability": availability, "reason": "local_provider_health", "provider": provider_id, "provider_config": provider.to_dict(), "health": row, "external_api_used": False}

    def _skipped_result(self, *, suite: str, provider: str, model: str | None, cases: list[dict[str, Any]], readiness: dict[str, Any], fixture: dict[str, Any]) -> CommandResult:
        rows = [self._case_row(case, status="skipped", provider=provider, model=model, error_id=str(readiness.get("reason")), prompt_reference={"payload_redacted": True}) for case in cases]
        return CommandResult(
            command="model eval run",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Model evaluation matrix skipped unavailable provider in controlled mode.",
            data={
                "summary": {
                    "suite": suite,
                    "provider": provider,
                    "model": model,
                    "cases_total": len(cases),
                    "passed_total": 0,
                    "failed_total": 0,
                    "skipped_total": len(cases),
                    "tokens_estimated_total": 0,
                    "cost_estimate_total_usd": 0.0,
                    "external_api_used": False,
                    "network_used": False,
                    "raw_prompts_stored": False,
                    "raw_outputs_stored": False,
                    "preliminary": True,
                },
                "matrix": rows,
                "provider_readiness": readiness,
                "fixture": {"path": _relative(self._fixture_path(), self.root), "schema_version": fixture.get("schema_version"), "description": fixture.get("description")},
                "notes": ["Provider was unavailable/disabled/blocked; Sprint 50 reports skip without breaking the hermetic mock baseline."],
            },
            findings=[Finding(id="MODEL_EVAL_PROVIDER_SKIPPED", message="Model eval provider is not executable in current local configuration; cases were skipped in controlled mode.", severity=Severity.WARNING, metadata={"provider": provider, "reason": readiness.get("reason"), "availability": readiness.get("availability"), "payload_redacted": True})],
        )

    def _load_fixture(self, suite: str) -> dict[str, Any]:
        path = self._fixture_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        if str(payload.get("suite_id")) != suite:
            raise ValueError(f"Model eval suite mismatch: requested {suite}, fixture declares {payload.get('suite_id')}")
        return payload

    def _fixture_path(self) -> Path:
        return self._resolve_inside_root(self.config.suite_path)

    def _resolve_inside_root(self, path: Path) -> Path:
        candidate = path if path.is_absolute() else self.root / path
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("ModelEvalRunner paths must remain inside the project root.") from exc
        return candidate


def _attach_prompt_reference(result: CommandResult, prompt_reference: dict[str, Any] | None) -> CommandResult:
    if not prompt_reference:
        return result
    data = dict(result.data or {})
    summary = dict(data.get("summary") or {})
    summary["prompt_id"] = prompt_reference.get("prompt_id")
    summary["prompt_version"] = prompt_reference.get("version")
    summary["prompt_payload_redacted"] = True
    data["summary"] = summary
    data["prompt_reference"] = dict(prompt_reference)
    return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)


def _result_digest(result: CommandResult) -> dict[str, Any]:
    payload = dict((result.data or {}).get("result") or {})
    content = str(payload.get("content") or payload.get("label") or payload.get("embedding") or "")
    return {"sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(), "length": len(content), "payload_redacted": True}


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
