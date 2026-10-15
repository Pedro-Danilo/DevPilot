"""R01-06: project-scoped, read-only coverage of actual engineering artifacts.

ArtifactProfileRegistry remains the only profile authority. This gate does not
publish, approve, alter documents or claim automatic semantic validation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
import re

from devpilot_core.validators.artifact import extract_headings, normalize_heading

Obligation = Literal["REQUIRED", "CONDITIONAL", "RECOMMENDED", "NOT_APPLICABLE"]
Review = Literal["PASS", "FAIL", "PENDING"]
Stages = ("INTAKE", "REQUIREMENTS", "ARCHITECTURE", "PLANNING", "SOURCE", "RELEASE", "OPERATIONS")
_PRIORITY = {"PASS": 0, "NOT_APPLICABLE": 0, "NOT_DUE": 0, "WARN": 1, "REVIEW_REQUIRED": 2, "BLOCK": 3}
_PLACEHOLDER = re.compile(r"(?im)^\s*(?:todo|tbd|pending|por definir|pendiente|lorem ipsum|\.{3}|\[completar\])\s*[.!]?\s*$")


@dataclass(frozen=True)
class CoverageRule:
    artifact_type: str
    path: str
    stage: str
    obligation: Obligation
    applicability: bool | None = None
    applicability_evidence: tuple[str, ...] = ()
    semantic_review: Review = "PENDING"
    semantic_evidence: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    dependency_freshness: dict[str, str] = field(default_factory=dict)
    dependency_evidence: dict[str, str] = field(default_factory=dict)
    na_reason: str = ""

    def __post_init__(self):
        if self.stage not in Stages or self.obligation not in {"REQUIRED", "CONDITIONAL", "RECOMMENDED", "NOT_APPLICABLE"}:
            raise ValueError("COVERAGE_RULE_STAGE_OR_OBLIGATION_INVALID")
        if not self.artifact_type or self.semantic_review not in {"PASS", "FAIL", "PENDING"}:
            raise ValueError("COVERAGE_RULE_INVALID")
        if type(self.applicability) not in (bool, type(None)):
            raise ValueError("COVERAGE_APPLICABILITY_INVALID")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("COVERAGE_DUPLICATE_DEPENDENCY")
        if (set(self.dependency_freshness) | set(self.dependency_evidence)) - set(self.dependencies):
            raise ValueError("COVERAGE_FRESHNESS_UNBOUND")


class ArtifactCoverageGate:
    """A bounded gate: only the caller's project-specific, stage-bound rules."""

    def __init__(self, registry, documents_root: Path):
        self.registry = registry
        self.documents_root = Path(documents_root).resolve()

    def _locate(self, relative: str) -> Path:
        p=Path(relative)
        if not relative or p.is_absolute() or "\\" in relative or ".." in p.parts:
            raise ValueError("COVERAGE_UNSAFE_PATH")
        found=(self.documents_root / p).resolve()
        if not found.is_relative_to(self.documents_root):
            raise ValueError("COVERAGE_UNSAFE_PATH")
        return found

    def evaluate(self, rules: tuple[CoverageRule, ...], *, stage: str) -> dict:
        if stage not in Stages:
            raise ValueError("COVERAGE_UNKNOWN_STAGE")
        seen=set()
        rows=[]
        for rule in rules:
            if rule.artifact_type in seen:
                raise ValueError("COVERAGE_DUPLICATE_ARTIFACT_TYPE")
            seen.add(rule.artifact_type)
            rows.append(self._evaluate_one(rule, stage))
        if not rows:
            return {"contract":"R01-06-COVERAGE-FIRST-VERTICAL", "stage":stage, "result":"REVIEW_REQUIRED", "reason":"NO_PROJECT_RULES", "items":[], "evaluation_only":True, "automatic_semantic_approval":False}
        result=max((r["result"] for r in rows),key=lambda x:_PRIORITY[x]);result = "PASS" if result in {"NOT_APPLICABLE","NOT_DUE"} else result
        return {"contract":"R01-06-COVERAGE-FIRST-VERTICAL", "stage":stage, "result":result, "items":rows, "evaluation_only":True, "automatic_semantic_approval":False}

    def _evaluate_one(self, rule: CoverageRule, stage: str) -> dict:
        target=self._locate(rule.path)
        for dep in rule.dependencies:self._locate(dep)
        result="PASS";reasons=[]
        def flag(state: str, reason: str):
            nonlocal result
            reasons.append(reason)
            if _PRIORITY[state]>_PRIORITY[result]:result=state
        profile=self.registry.select(Path(rule.path))
        row={"artifact_type":rule.artifact_type,"path":rule.path,"stage":rule.stage,"obligation":rule.obligation,
             "profile_id":profile.id,"profile_version":profile.profile_version,"applicability_evidence":list(rule.applicability_evidence),
             "evidence_refs":list(rule.evidence_refs),"semantic_review":rule.semantic_review,
             "semantic_evidence":list(rule.semantic_evidence),"dependencies":list(rule.dependencies),"dependency_freshness":dict(rule.dependency_freshness),"dependency_evidence":dict(rule.dependency_evidence)}
        if Stages.index(rule.stage)>Stages.index(stage):
            result="NOT_DUE";reasons.append("FUTURE_STAGE")
        elif rule.obligation=="NOT_APPLICABLE":
            if not rule.na_reason.strip() or not rule.applicability_evidence:
                flag("REVIEW_REQUIRED","N_A_UNJUSTIFIED")
            else:
                result="NOT_APPLICABLE";reasons.append("N_A_GROUNDED")
        elif rule.obligation=="CONDITIONAL" and (rule.applicability is None or not rule.applicability_evidence):
            flag("REVIEW_REQUIRED","CONDITION_FACTS_UNVERIFIED")
        elif rule.obligation=="CONDITIONAL" and rule.applicability is False:
            result="NOT_APPLICABLE";reasons.append("CONDITION_FALSE_EVIDENCED")
        else:
            required=rule.obligation!="RECOMMENDED"
            if not target.is_file():
                flag("BLOCK" if required else "WARN","REQUIRED_MISSING" if required else "RECOMMENDED_MISSING")
            else:
                text=target.read_text(encoding="utf-8-sig")
                headings=extract_headings(text)
                body=re.sub(r"(?m)^#{1,6}\s+.*$", "", text)
                nonempty=[line.strip() for line in body.splitlines() if line.strip() and not line.strip().startswith("<!--") and not line.strip().startswith("---")]
                if not nonempty or all(_PLACEHOLDER.fullmatch(line) for line in nonempty):
                    flag("BLOCK" if required else "WARN","EMPTY_OR_PLACEHOLDER_CONTENT")
                missing=[s for s in profile.required_sections if not any(normalize_heading(s) in h.normalized for h in headings)]
                if missing:
                    flag("BLOCK" if required else "WARN","MISSING_REQUIRED_SECTIONS:"+",".join(missing))
                # Even a present heading is not evidence that its section contains content.
                lines=text.splitlines()
                for expected in profile.required_sections:
                    matching=[idx for idx,heading in enumerate(headings) if normalize_heading(expected) in heading.normalized]
                    if not matching:continue
                    selected=headings[matching[0]]
                    following=[h.line_number for h in headings if h.line_number>selected.line_number and h.level<=selected.level]
                    stop=min(following)-1 if following else len(lines)
                    section=[line.strip() for line in lines[selected.line_number:stop] if line.strip() and not line.strip().startswith("<!--")]
                    if not section or all(_PLACEHOLDER.fullmatch(line) for line in section):
                        flag("BLOCK" if required else "WARN","EMPTY_REQUIRED_SECTION:"+expected)
                if rule.semantic_review=="FAIL":
                    flag("BLOCK" if required else "WARN","SEMANTIC_REVIEW_FAILED")
                elif rule.semantic_review!="PASS" or not rule.semantic_evidence:
                    flag("BLOCK" if required else "WARN","SEMANTIC_ACCEPTANCE_NOT_EVIDENCED")
            for dep in rule.dependencies:
                dep_path=self._locate(dep)
                if not dep_path.is_file():
                    flag("BLOCK" if required else "WARN","DEPENDENCY_MISSING:"+dep)
                elif rule.dependency_freshness.get(dep)!="CURRENT" or not rule.dependency_evidence.get(dep):
                    flag("REVIEW_REQUIRED","DEPENDENCY_FRESHNESS_UNPROVEN:"+dep)
        row.update(result=result,reasons=reasons,current_revision=rule.path if target.is_file() else None,
                   lifecycle="EXISTING_UNAPPROVED" if target.is_file() else "ABSENT", owner_action="REVIEW" if result in {"REVIEW_REQUIRED","BLOCK"} else "NONE")
        return row
