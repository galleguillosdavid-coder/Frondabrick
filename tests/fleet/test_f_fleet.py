#!/usr/bin/env python3
"""
Test Suite for Phase 11: F-Fleet
Verifies fleet roles, permissions matrix, and role authorization logic.
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.fleet.orchestrator import FleetOrchestrator, FLEET_ROLES

PERMISSIONS_DOC = WORKSPACE_ROOT / "docs" / "AGENT_PERMISSIONS.md"
BROWSER_QA_ROLE = WORKSPACE_ROOT / "agents" / "browser_qa" / "ROLE.md"

def test_documents_exist():
    assert PERMISSIONS_DOC.is_file(), f"AGENT_PERMISSIONS.md missing at {PERMISSIONS_DOC}"
    assert BROWSER_QA_ROLE.is_file(), f"ROLE.md missing for browser_qa at {BROWSER_QA_ROLE}"
    print("[PASS] AGENT_PERMISSIONS.md and Browser-QA ROLE.md verified.")

def test_all_7_roles_defined():
    expected_roles = {"planner", "reviewer", "builder", "shield", "build_resolver", "memory", "browser_qa"}
    assert set(FLEET_ROLES.keys()) == expected_roles, f"Fleet roles mismatch: {set(FLEET_ROLES.keys())} != {expected_roles}"
    print(f"[PASS] All {len(expected_roles)} fleet roles registered in orchestrator.")

def test_orchestrator_authorization_matrix():
    # 1. Reviewer write denied
    auth, reason = FleetOrchestrator.authorize_tool_for_role("reviewer", "write_to_file")
    assert not auth, "Reviewer must not be authorized to use write_to_file"

    # 2. Planner writing code denied, writing doc allowed
    auth_code, _ = FleetOrchestrator.authorize_tool_for_role("planner", "write_to_file", target_file="src/index.js")
    assert not auth_code, "Planner must not write source code"
    auth_doc, _ = FleetOrchestrator.authorize_tool_for_role("planner", "write_to_file", target_file="docs/feature_plan.md")
    assert auth_doc, "Planner should be allowed to write documentation/plans"

    # 3. Builder write allowed
    auth_build, _ = FleetOrchestrator.authorize_tool_for_role("builder", "write_to_file")
    assert auth_build, "Builder must have write permissions"

    # 4. BrowserQA browser_subagent allowed
    auth_browser, _ = FleetOrchestrator.authorize_tool_for_role("browser_qa", "browser_subagent")
    assert auth_browser, "BrowserQA must have browser_subagent permission"

    # 5. Unknown role denied
    auth_unk, _ = FleetOrchestrator.authorize_tool_for_role("super_admin", "write_to_file")
    assert not auth_unk, "Arbitrary non-registered role must be denied"

    print("[PASS] Fleet orchestrator authorization policies fully verified.")

if __name__ == "__main__":
    try:
        test_documents_exist()
        test_all_7_roles_defined()
        test_orchestrator_authorization_matrix()
        print("\n=== FASE 11: F-FLEET TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Fleet: {e}")
        sys.exit(1)
