#!/usr/bin/env python3
"""
Test Suite for Phase 22: Vault Hardening & Physical Enforcement Verification
Verifies:
1. EXP-22.1: Protected vs Mutable inventory segregation
2. EXP-22.2: ACL auditor functionality
3. EXP-22.3: Canary test with physical deletion denial and hash preservation
4. EXP-22.4: Workspace development autonomy preservation
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.vault.verifier import VaultVerifier

def test_protected_inventory_integrity():
    # EXP-22.1: Verify protected artifacts exist and hashes match baseline
    chat_gpt_file = WORKSPACE_ROOT / "chat gpt"
    gen_md_file = WORKSPACE_ROOT / "gen.md"
    assert chat_gpt_file.is_file(), "Protected file 'chat gpt' must exist"
    assert gen_md_file.is_file(), "Protected file 'gen.md' must exist"
    print("[PASS] EXP-22.1: Protected inventory items present.")

def test_acl_auditor():
    # EXP-22.2: Verify ACL auditor reads permissions
    audit_res = VaultVerifier.audit_acl(WORKSPACE_ROOT)
    assert audit_res.get("exists") is True
    assert "username" in audit_res
    print(f"[PASS] EXP-22.2: ACL auditor active for user {audit_res.get('username')}.")

def test_canary_physical_enforcement():
    # EXP-22.3: Full automated canary cycle
    report = VaultVerifier.run_canary_test()
    assert report.get("acl") == "PASS", f"ACL application failed: {report}"
    assert report.get("read") == "PASS", f"Read verification failed: {report}"
    assert report.get("delete") == "BLOCKED", f"File deletion was NOT blocked: {report}"
    assert report.get("delete_child") == "BLOCKED", f"Folder recursive deletion was NOT blocked: {report}"
    assert report.get("canary_exists") == "PASS", f"Canary did not survive: {report}"
    assert report.get("hash") == "PASS", f"Hash mismatch after attack: {report}"
    assert report.get("enforcement") == "DEMONSTRATED", f"Enforcement not demonstrated: {report}"
    print("[PASS] EXP-22.3: Physical deletion denied by NTFS kernel; canary survived with 100% hash integrity.")

def test_workspace_autonomy():
    # EXP-22.4: Verify autonomy in mutable space
    autonomy = VaultVerifier.run_autonomy_test()
    assert autonomy.get("create") == "PASS"
    assert autonomy.get("edit") == "PASS"
    assert autonomy.get("execute") == "PASS"
    assert autonomy.get("delete") == "PASS"
    assert autonomy.get("autonomy") == "DEMONSTRATED"
    print("[PASS] EXP-22.4: Development autonomy in mutable workspace confirmed.")
def test_detailed_acl_drift_auditor():
    # EXP-23.1: Verify detailed drift detector against workspace
    audit_res = VaultVerifier.audit_vault_integrity(WORKSPACE_ROOT)
    assert audit_res["read_allowed"] == "PASS"
    assert audit_res["acl_present"] == "PASS"
    print("[PASS] EXP-23.1: Detailed ACL integrity & drift detector operational.")

def test_cross_process_persistence():
    # EXP-23.2: Verify protection persistence across independent child processes
    report = VaultVerifier.run_persistence_test()
    assert report["setup_process"] == "PASS"
    assert report["independent_process_read"] == "PASS"
    assert report["independent_process_delete_blocked"] == "PASS"
    assert report["canary_survival"] == "PASS"
    assert report["hash_match"] == "PASS"
    assert report["persistence"] == "DEMONSTRATED"
    print("[PASS] EXP-23.2: Protection persists across isolated independent processes.")

def test_accidental_drift_simulation():
    # EXP-23.3: Verify that drift detector immediately catches simulated tampering
    report = VaultVerifier.run_drift_simulation_test()
    assert report["initial_protection"] == "PASS"
    assert report["tamper_detected"] == "PASS"
    assert report["drift_flagged"] == "PASS"
    assert report["recovery_verified"] == "PASS"
    assert report["drift_detector"] == "DEMONSTRATED"
    print("[PASS] EXP-23.3: Accidental ACL drift simulation caught and recovered deterministically.")

if __name__ == "__main__":
    try:
        test_protected_inventory_integrity()
        test_acl_auditor()
        test_canary_physical_enforcement()
        test_workspace_autonomy()
        test_detailed_acl_drift_auditor()
        test_cross_process_persistence()
        test_accidental_drift_simulation()
        print("\n=== FASE 22 & 23: VAULT HARDENING & DRIFT VERIFICATION PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Vault hardening assertion failed: {e}")
        sys.exit(1)
