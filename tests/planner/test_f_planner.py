#!/usr/bin/env python3
"""
Test Suite for Phase 3: F-Planner
Verifies planner role, template structure, 10-section contract, and skill schema.
"""

import sys
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ROLE_FILE = WORKSPACE_ROOT / "agents" / "planner" / "ROLE.md"
PERMISSIONS_FILE = WORKSPACE_ROOT / "agents" / "planner" / "PERMISSIONS.md"
TEMPLATE_FILE = WORKSPACE_ROOT / "agents" / "planner" / "PLAN_TEMPLATE.md"
SKILL_FILE = WORKSPACE_ROOT / ".agents" / "skills" / "fronda-planner" / "SKILL.md"

MANDATORY_SECTIONS = [
    "OBJETIVO",
    "ALCANCE",
    "NO-ALCANCE",
    "ARCHIVOS",
    "DEPENDENCIAS",
    "RIESGOS",
    "PLAN",
    "TESTS",
    "CRITERIOS DE ACEPTACIÓN",
    "ROLLBACK",
]

def test_planner_role_and_permissions():
    assert ROLE_FILE.is_file(), f"ROLE.md missing at {ROLE_FILE}"
    assert PERMISSIONS_FILE.is_file(), f"PERMISSIONS.md missing at {PERMISSIONS_FILE}"

    role_text = ROLE_FILE.read_text(encoding="utf-8")
    assert "F-Planner No Programa" in role_text, "ROLE.md must declare 'F-Planner No Programa'"
    assert "No Coding" in role_text or "no programa" in role_text.lower()
    print("[PASS] F-Planner role and permissions definitions verified.")

def test_plan_template_10_sections():
    assert TEMPLATE_FILE.is_file(), f"PLAN_TEMPLATE.md missing at {TEMPLATE_FILE}"
    content = TEMPLATE_FILE.read_text(encoding="utf-8")
    for section in MANDATORY_SECTIONS:
        pattern = re.compile(rf"##\s+\d*\.?\s*{re.escape(section)}", re.IGNORECASE)
        assert pattern.search(content) is not None, f"PLAN_TEMPLATE.md missing mandatory section: {section}"
    print(f"[PASS] PLAN_TEMPLATE.md contains all {len(MANDATORY_SECTIONS)} mandatory sections.")

def test_planner_skill_schema():
    assert SKILL_FILE.is_file(), f"SKILL.md missing at {SKILL_FILE}"
    content = SKILL_FILE.read_text(encoding="utf-8")

    # Frontmatter
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    assert match is not None, "SKILL.md must declare YAML frontmatter"
    frontmatter = match.group(1)
    body = match.group(2)
    assert "name: fronda-planner" in frontmatter

    # Section 20 headings
    for heading in [
        "## PROPÓSITO",
        "## CUÁNDO USAR",
        "## CUÁNDO NO USAR",
        "## PROCEDIMIENTO",
        "## REGLAS CRÍTICAS",
        "## REFERENCIAS",
    ]:
        assert heading in body, f"SKILL.md missing Section 20 heading '{heading}'"

    print("[PASS] F-Planner SKILL.md adheres to Section 20 schema.")

def test_plan_validator_logic():
    def validate_plan(markdown_text: str) -> tuple[bool, list[str]]:
        missing = []
        for sec in MANDATORY_SECTIONS:
            pattern = re.compile(rf"##\s+\d*\.?\s*{re.escape(sec)}", re.IGNORECASE)
            if not pattern.search(markdown_text):
                missing.append(sec)
        return (len(missing) == 0, missing)

    # Valid template test
    valid_text = TEMPLATE_FILE.read_text(encoding="utf-8")
    is_valid, missing = validate_plan(valid_text)
    assert is_valid, f"Template should be valid, but missing: {missing}"

    # Incomplete plan test (missing ROLLBACK)
    incomplete_text = valid_text.replace("## 10. ROLLBACK", "## 10. DEPLOYMENT")
    is_valid_inc, missing_inc = validate_plan(incomplete_text)
    assert not is_valid_inc and "ROLLBACK" in missing_inc
    print("[PASS] Plan 10-section contract validation logic verified.")

if __name__ == "__main__":
    try:
        test_planner_role_and_permissions()
        test_plan_template_10_sections()
        test_planner_skill_schema()
        test_plan_validator_logic()
        print("\n=== FASE 3: F-PLANNER TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Planner: {e}")
        sys.exit(1)
