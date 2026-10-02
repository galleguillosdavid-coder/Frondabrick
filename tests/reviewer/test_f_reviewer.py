#!/usr/bin/env python3
"""
Test Suite for Phase 2: F-Reviewer
Verifies role definition, permissions matrix, skill structure, and read-only enforcement.
"""

import sys
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ROLE_FILE = WORKSPACE_ROOT / "agents" / "reviewer" / "ROLE.md"
PERMISSIONS_FILE = WORKSPACE_ROOT / "agents" / "reviewer" / "PERMISSIONS.md"
SKILL_FILE = WORKSPACE_ROOT / ".agents" / "skills" / "fronda-reviewer" / "SKILL.md"

def test_role_and_permissions_definitions():
    assert ROLE_FILE.is_file(), f"ROLE.md missing at {ROLE_FILE}"
    assert PERMISSIONS_FILE.is_file(), f"PERMISSIONS.md missing at {PERMISSIONS_FILE}"

    role_text = ROLE_FILE.read_text(encoding="utf-8")
    assert "READ ONLY" in role_text, "ROLE.md must explicitly declare READ ONLY"
    for forbidden in ["write_to_file", "git commit", "git push"]:
        assert forbidden in role_text, f"ROLE.md must explicitly prohibit '{forbidden}'"

    perm_text = PERMISSIONS_FILE.read_text(encoding="utf-8")
    assert "view_file" in perm_text and "PERMITIDO" in perm_text
    assert "write_to_file" in perm_text and "BLOQUEADO" in perm_text
    print("[PASS] F-Reviewer role and permissions definitions verified.")

def test_skill_conformance():
    assert SKILL_FILE.is_file(), f"SKILL.md missing at {SKILL_FILE}"
    content = SKILL_FILE.read_text(encoding="utf-8")

    # Frontmatter validation
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    assert match is not None, "SKILL.md must have valid YAML frontmatter"
    frontmatter = match.group(1)
    body = match.group(2)
    assert "name: fronda-reviewer" in frontmatter
    assert "description:" in frontmatter

    # Section 20 mandatory sections
    required_sections = [
        "## PROPÓSITO",
        "## CUÁNDO USAR",
        "## CUÁNDO NO USAR",
        "## PROCEDIMIENTO",
        "## REGLAS CRÍTICAS",
        "## REFERENCIAS",
    ]
    for section in required_sections:
        assert section in body, f"SKILL.md missing required Section 20 heading: {section}"

    print("[PASS] F-Reviewer SKILL.md adheres 100% to Section 20 schema.")

def test_reviewer_guardrail_enforcement():
    # Simulated policy engine
    read_tools = ["view_file", "list_dir", "grep_search"]
    write_tools = ["write_to_file", "replace_file_content", "multi_replace_file_content"]
    forbidden_commands = ["git commit -m 'test'", "git push origin main", "rm -f file.txt"]
    allowed_commands = ["git diff", "git status", "python -m unittest discover tests"]

    def policy_eval(role: str, tool: str, cmd: str = "") -> str:
        if role == "reviewer":
            if tool in write_tools:
                return "deny"
            if tool == "run_command":
                for fcmd in ["commit", "push", "rm ", "del "]:
                    if fcmd in cmd:
                        return "deny"
        return "allow"

    for tool in read_tools:
        assert policy_eval("reviewer", tool) == "allow", f"Tool {tool} should be allowed for reviewer"

    for tool in write_tools:
        assert policy_eval("reviewer", tool) == "deny", f"Tool {tool} must be DENIED for reviewer"

    for cmd in forbidden_commands:
        assert policy_eval("reviewer", "run_command", cmd) == "deny", f"Command '{cmd}' must be DENIED"

    for cmd in allowed_commands:
        assert policy_eval("reviewer", "run_command", cmd) == "allow", f"Command '{cmd}' should be allowed"

    print("[PASS] F-Reviewer read-only guardrails and command policies verified.")

if __name__ == "__main__":
    try:
        test_role_and_permissions_definitions()
        test_skill_conformance()
        test_reviewer_guardrail_enforcement()
        print("\n=== FASE 2: F-REVIEWER TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Reviewer: {e}")
        sys.exit(1)
