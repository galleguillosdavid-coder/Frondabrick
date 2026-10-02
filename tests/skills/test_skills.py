#!/usr/bin/env python3
"""
Test Suite for Phase 8: F-Skills
Validates all 6 core skills against Section 20 Schema & Progressive Disclosure.
"""

import sys
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_ROOT = WORKSPACE_ROOT / ".agents" / "skills"

MANDATORY_SKILLS = [
    "fronda-planner",
    "fronda-reviewer",
    "fronda-shield",
    "fronda-tdd",
    "fronda-build",
    "fronda-memory"
]

SECTION_20_HEADINGS = [
    "## PROPÓSITO",
    "## CUÁNDO USAR",
    "## CUÁNDO NO USAR",
    "## PROCEDIMIENTO",
    "## REGLAS CRÍTICAS",
    "## REFERENCIAS"
]

def test_all_skills_exist_and_conform():
    for skill_name in MANDATORY_SKILLS:
        skill_file = SKILLS_ROOT / skill_name / "SKILL.md"
        assert skill_file.is_file(), f"Skill file missing for {skill_name} at {skill_file}"

        content = skill_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # 1. Frontmatter check
        match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
        assert match is not None, f"Skill {skill_name} missing YAML frontmatter delimiters (---)"
        frontmatter = match.group(1)
        body = match.group(2)

        assert f"name: {skill_name}" in frontmatter, f"Skill {skill_name} incorrect name in frontmatter"
        assert "description:" in frontmatter, f"Skill {skill_name} missing description in frontmatter"

        # 2. Section 20 mandatory headings
        for heading in SECTION_20_HEADINGS:
            assert heading in body, f"Skill {skill_name} missing mandatory Section 20 heading: '{heading}'"

        # 3. Conciseness check (Progressive disclosure: no encyclopedia in SKILL.md)
        assert len(lines) <= 80, f"Skill {skill_name} exceeds conciseness limit ({len(lines)} > 80 lines). Move details to references/!"

        print(f"[PASS] Skill '{skill_name}' conforms 100% to Section 20 schema ({len(lines)} lines).")

if __name__ == "__main__":
    try:
        test_all_skills_exist_and_conform()
        print("\n=== FASE 8: F-SKILLS TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Skills: {e}")
        sys.exit(1)
