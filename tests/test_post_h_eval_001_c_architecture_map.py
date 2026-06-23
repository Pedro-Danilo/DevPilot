from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH_DOC = ROOT / "docs/02_architecture/post_h_current_architecture_map.md"


def _content() -> str:
    return ARCH_DOC.read_text(encoding="utf-8")


def test_post_h_eval_001_c_architecture_map_exists():
    assert ARCH_DOC.exists()


def test_post_h_eval_001_c_required_sections_present():
    content = _content()
    required_sections = [
        "# Mapa arquitectónico actual DevPilot post-H",
        "## 1. Resumen arquitectónico",
        "## 2. Vista por capas",
        "## 3. Vista por paquetes Python",
        "## 4. Vista CLI/API/UI",
        "## 5. Vista de estado local .devpilot",
        "## 6. Vista de seguridad",
        "## 7. Vista de testing y quality gates",
        "## 8. Vista de observabilidad",
        "## 9. Vista de release y auditoría",
        "## 10. Puntos de acoplamiento",
        "## 11. Riesgos arquitectónicos",
        "## 12. Recomendaciones de refactor",
        "## 13. Decisiones pendientes",
    ]
    for section in required_sections:
        assert section in content, section


def test_post_h_eval_001_c_layers_and_interfaces_are_covered():
    content = _content()
    required_terms = [
        "User Interfaces",
        "Core / Application Layer",
        "Governance Layer",
        "Agentic Layer",
        "Knowledge Layer",
        "Integration Layer",
        "Operations Layer",
        "CLI",
        "API local",
        "UI web",
    ]
    for term in required_terms:
        assert term in content, term


def test_post_h_eval_001_c_architectural_risks_are_explicit():
    content = _content()
    required_risks = [
        "ARCH-001",
        "CLI monolítico",
        "Remote runner como stub experimental",
        "Plugin ecosystem sin sandbox real",
        "Connectors read-only",
        "Testing histórico abundante",
        "Runtime artifacts",
    ]
    for risk in required_risks:
        assert risk in content, risk


def test_post_h_eval_001_c_safety_boundaries_remain_intact():
    content = _content()
    forbidden_claims = [
        "remote execution enabled",
        "write connectors enabled",
        "production-ready enterprise",
    ]
    lowered = content.lower()
    for claim in forbidden_claims:
        assert claim not in lowered, claim
    required_boundaries = [
        "Remote/enterprise sigue experimental",
        "no habilitada",
        "Mutaciones runtime: ninguna",
        "Remote execution: no habilitada",
    ]
    for boundary in required_boundaries:
        assert boundary in content, boundary
