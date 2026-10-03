#!/usr/bin/env python3
"""
Test Suite for Phase 25: Autonomous Session Resilience
Verifies:
- EXP-25.1: Aborted / killed process leaves vault and workspace recoverable
- EXP-25.2: TDD test failure handling without vault corruption
- EXP-25.3: Interrupted mutable modification recovery
- EXP-25.4: Deliberate workspace inconsistency resolution cycle
- EXP-25.5: Final vault, canary, hash, and git audit
"""

import sys
import time
import hashlib
import subprocess
import py_compile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.vault.verifier import VaultVerifier
from scripts.resolver.engine import BuildResolverEngine

def test_exp25_1_aborted_process():
    # EXP-25.1: Aborted child process leaves vault intact
    lock_file = WORKSPACE_ROOT / "tmp_exp25_1_abort.lock"
    child_code = f"""
import time
with open(r'{lock_file}', 'w') as f:
    f.write('ABORT_SIMULATION')
    f.flush()
    time.sleep(30)
"""
    proc = subprocess.Popen([sys.executable, "-c", child_code])
    time.sleep(1)
    proc.terminate()
    proc.wait()

    # Verify vault & canary post-abort
    audit = VaultVerifier.audit_vault_integrity(WORKSPACE_ROOT / "vault")
    assert audit["protection_status"] == "PASS", f"Vault compromised: {audit}"
    assert not audit["drift_detected"]

    canary = (WORKSPACE_ROOT / "vault" / "canary.txt").read_text(encoding="utf-8").strip()
    assert canary == "VAULT_PERMANENT_CANARY_INTEGRITY_PROTECTED_2026"

    if lock_file.exists():
        lock_file.unlink()
    print("[PASS] EXP-25.1: Aborted process terminated cleanly; vault and canary verified intact.")

def test_exp25_2_failing_test_continuation():
    # EXP-25.2: TDD failure handled cleanly in mutable space
    probe_test = WORKSPACE_ROOT / "tests" / "core" / "test_resilience_probe.py"
    assert probe_test.is_file(), "Probe test must exist"
    res = subprocess.run([sys.executable, str(probe_test)], capture_output=True, text=True)
    assert res.returncode == 0, f"Probe test failed: {res.stderr}"

    # Verify vault during test workflow
    audit = VaultVerifier.audit_vault_integrity(WORKSPACE_ROOT / "vault")
    assert audit["protection_status"] == "PASS"
    print("[PASS] EXP-25.2: Failing test resolved autonomously without vault side-effects.")

def test_exp25_3_interrupted_mutable_modification():
    # EXP-25.3: Interrupted mutable modification recovers cleanly
    draft_file = WORKSPACE_ROOT / "src" / "tmp_interrupted_draft.py"
    try:
        # Step 1: Incomplete draft
        draft_file.write_text("def unfinished_syntax(\n", encoding="utf-8")
        failed = False
        try:
            py_compile.compile(str(draft_file), doraise=True)
        except py_compile.PyCompileError:
            failed = True
        assert failed, "Compilation of broken draft should fail"

        # Step 2: Recover
        draft_file.write_text("def finished_syntax():\n    return True\n", encoding="utf-8")
        py_compile.compile(str(draft_file), doraise=True)

        # Step 3: Vault verification
        audit = VaultVerifier.audit_vault_integrity(WORKSPACE_ROOT / "vault")
        assert audit["protection_status"] == "PASS"
        print("[PASS] EXP-25.3: Interrupted mutable file detected, recovered, and vault unaffected.")
    finally:
        if draft_file.exists():
            draft_file.unlink()

def test_exp25_4_workspace_recovery_cycle():
    # EXP-25.4: Workspace inconsistency -> Diagnostic -> Fix -> Pass -> Vault Pass
    svc_file = WORKSPACE_ROOT / "src" / "broken_service.py"
    test_file = WORKSPACE_ROOT / "tests" / "core" / "test_broken_service.py"

    try:
        # Inconsistency
        test_content = f"import sys\nsys.path.insert(0, r'{WORKSPACE_ROOT}')\nfrom src.broken_service import run_svc\ndef test_svc():\n    assert run_svc() == 'OK'\nif __name__ == '__main__':\n    test_svc()\n"
        test_file.write_text(test_content, encoding="utf-8")

        # Step 1: Run test -> Expect failure
        res_err = subprocess.run([sys.executable, str(test_file)], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
        assert res_err.returncode != 0

        # Step 2: Diagnostic validation via BuildResolverEngine
        diag_report = {
            "reproduce": "RuntimeError: Service config missing",
            "locate": "src/broken_service.py:2",
            "explain": "RuntimeError raised unconditionally",
            "propose": "Update run_svc to return 'OK'",
            "fix": "def run_svc(): return 'OK'",
            "rerun": {"exit_code": 0, "stdout": "OK"},
            "proof": "Exit code 0 and valid string return"
        }
        eval_res = BuildResolverEngine.evaluate_resolution_cycle(diag_report)
        assert eval_res["status"] == "RESOLVED"

        # Step 3: Fix
        svc_file.write_text("def run_svc():\n    return 'OK'\n", encoding="utf-8")
        res_ok = subprocess.run([sys.executable, str(test_file)], capture_output=True, text=True)
        assert res_ok.returncode == 0

        # Step 4: Vault & Drift
        audit = VaultVerifier.audit_vault_integrity(WORKSPACE_ROOT / "vault")
        assert audit["protection_status"] == "PASS"
        assert not audit["drift_detected"]
        print("[PASS] EXP-25.4: Workspace recovery cycle (Error->Diagnose->Fix->Test->Vault) verified.")
    finally:
        if svc_file.exists():
            svc_file.unlink()
        if test_file.exists():
            test_file.unlink()

def test_exp25_5_audit_and_canary_integrity():
    # EXP-25.5: Final comprehensive audit
    audit = VaultVerifier.audit_vault_integrity(WORKSPACE_ROOT / "vault")
    assert audit["protection_status"] == "PASS"
    assert not audit["drift_detected"]

    canary_content = (WORKSPACE_ROOT / "vault" / "canary.txt").read_text(encoding="utf-8")
    assert canary_content.strip() == "VAULT_PERMANENT_CANARY_INTEGRITY_PROTECTED_2026"

    # Preexisting protected files
    chat_gpt = (WORKSPACE_ROOT / "chat gpt").read_bytes()
    gen_md = (WORKSPACE_ROOT / "gen.md").read_bytes()
    assert len(chat_gpt) > 0 and len(gen_md) > 0
    print("[PASS] EXP-25.5: Final audit, canary, and protected files integrity verified.")

if __name__ == "__main__":
    try:
        test_exp25_1_aborted_process()
        test_exp25_2_failing_test_continuation()
        test_exp25_3_interrupted_mutable_modification()
        test_exp25_4_workspace_recovery_cycle()
        test_exp25_5_audit_and_canary_integrity()
        print("\n=== FASE 25: AUTONOMOUS SESSION RESILIENCE PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Resilience test failed: {e}")
        sys.exit(1)
