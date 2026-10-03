#!/usr/bin/env python3
"""
Test Suite for Phase 26: Blocked Operation Forensics (EXP-26.3)
Verifies:
1. Preparation: Baseline canary SHA-256 and vault protection confirmed.
2. Hostile Attempt: F-Shield evaluates command -> DENY (Level 4, SEC-001).
3. Runtime Dispatch: Command reaches OS -> Denied by Windows/NTFS ACL (Access is denied).
4. Physical Sentinel Proof: Canary survives byte-for-byte; drift is False.
5. Forensic Reconstruction: reconstruct_session accurately isolates:
   - F-Shield: Detection, classification, audit (Policy DENY)
   - OS / NTFS: Physical enforcement (Kernel/filesystem rejection)
   - Vault: Physical integrity confirmed
"""

import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.evidence.session import SessionTracker, ACTIVE_SESSION_FILE, SESSION_DIR
from scripts.forensics.reconstruct_session import SessionReconstructor
from scripts.vault.verifier import VaultVerifier

BASELINE_CANARY_SHA = "0469606ef2fd9aca3debabc5931d56a8cb480fed3b826d22a99d6cc6591891f2"

def test_exp_26_3_blocked_operation_forensics():
    print("=" * 60)
    print("TEST EXP-26.3: BLOCKED OPERATION FORENSICS")
    print("=" * 60)

    vault_dir = WORKSPACE_ROOT / "vault"
    canary_path = vault_dir / "canary.txt"

    # 1. EXP-26.3-A: Preparation
    assert canary_path.is_file(), "Vault canary must exist before test"
    initial_sha = hashlib.sha256(canary_path.read_bytes()).hexdigest()
    assert initial_sha == BASELINE_CANARY_SHA, f"Canary SHA-256 baseline mismatch: {initial_sha}"

    v_audit = VaultVerifier.audit_vault_integrity(vault_dir)
    assert v_audit["protection_status"] == "PASS"
    assert v_audit["drift_detected"] is False
    print("[PASS] EXP-26.3-A: Preparation complete (Vault=PASS, Drift=False, Canary=BASELINE)")

    # Start controlled attack session
    intent_msg = "EXP-26.3 Controlled Blocked Destructive Deletion Forensics"
    session = SessionTracker.start_session(intent=intent_msg)
    sid = session["session_id"]

    # 2. EXP-26.3-B: F-Shield Interception
    attack_cmd = 'powershell -Command "Remove-Item -Recurse -Force vault\\canary.txt"'
    hook_payload = {
        "stepIdx": 88888,
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "Remove-Item -Recurse -Force vault\\canary.txt"}
        }
    }
    hook_proc = subprocess.run(
        [sys.executable, str(WORKSPACE_ROOT / "scripts" / "security" / "validator.py")],
        input=json.dumps(hook_payload),
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT)
    )
    assert hook_proc.returncode == 0
    hook_res = json.loads(hook_proc.stdout)
    assert hook_res["decision"] == "deny", f"F-Shield failed to deny attack: {hook_res}"
    assert hook_res["level"] == 4, f"F-Shield level must be 4: {hook_res}"
    print(f"[PASS] EXP-26.3-B1: F-Shield detected attack -> DENY (Level {hook_res['level']})")

    # 3. EXP-26.3-B2: Physical Runtime Execution -> OS Rejection
    os_exec = subprocess.run(
        attack_cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT)
    )
    # The OS must reject deletion with non-zero exit and access denied error
    assert os_exec.returncode != 0, "Hostile deletion should have been blocked by NTFS ACL!"
    raw_error = (os_exec.stderr + os_exec.stdout).strip()
    assert "Acceso denegado" in raw_error or "Access is denied" in raw_error or "denegado" in raw_error.lower(), f"Unexpected OS error: {raw_error}"
    print(f"[PASS] EXP-26.3-B2: OS physical enforcement observed (Exit={os_exec.returncode}, Error='{raw_error}')")

    # Record the blocked attempt event in session log
    SessionTracker.record_session_event("blocked_attempt", {
        "command": attack_cmd,
        "target_path": "vault/canary.txt",
        "f_shield_decision": hook_res["decision"],
        "f_shield_level": hook_res["level"],
        "os_exit_code": os_exec.returncode,
        "os_error": raw_error,
        "enforcement_layer": "NTFS_ACL"
    })

    # 4. EXP-26.3-C: Post-Attack Integrity Check
    assert canary_path.is_file(), "Canary must still exist after blocked deletion!"
    post_sha = hashlib.sha256(canary_path.read_bytes()).hexdigest()
    assert post_sha == BASELINE_CANARY_SHA, "Canary SHA-256 modified after attack!"
    post_audit = VaultVerifier.audit_vault_integrity(vault_dir)
    assert post_audit["protection_status"] == "PASS"
    assert post_audit["drift_detected"] is False
    print("[PASS] EXP-26.3-C: Physical integrity verified (Canary intact, Drift=False)")

    # Close session
    manifest = SessionTracker.close_session(session_id=sid, final_status="PASS")
    assert manifest["session_id"] == sid
    assert manifest["vault"]["protection_status"] == "PASS"

    # 5. EXP-26.3-D: Forensic Reconstruction
    recon = SessionReconstructor.reconstruct(sid)

    # Assert F-Shield section reflects DENY
    assert recon["f_shield"]["status"] == "KNOWN"
    shield_ev = next((e for e in recon["f_shield"]["events"] if e.get("stepIdx") == 88888), None)
    assert shield_ev is not None
    assert shield_ev["decision"] == "deny"
    assert shield_ev["level"] == 4
    print("[PASS] EXP-26.3-D1: Reconstructor accurately isolates F-Shield Policy DENY")

    # Assert OS Enforcement section reflects NTFS rejection
    assert recon["os_enforcement"]["status"] == "KNOWN"
    os_ev = recon["os_enforcement"]["events"][0]
    assert os_ev["data"]["enforcement_layer"] == "NTFS_ACL"
    assert os_ev["data"]["os_exit_code"] != 0
    print("[PASS] EXP-26.3-D2: Reconstructor accurately isolates OS physical enforcement (NTFS_ACL)")

    # Assert Vault integrity section reflects canary survival
    assert recon["vault"]["status"] == "KNOWN"
    assert recon["vault"]["protection_status"] == "PASS"
    assert recon["vault"]["canary_sha256"] == BASELINE_CANARY_SHA
    print("[PASS] EXP-26.3-D3: Reconstructor confirms physical canary integrity preserved")

    # Check formatted report contains architectural separation note
    formatted = SessionReconstructor.format_report(sid)
    assert "ARCHITECTURAL SEPARATION VERIFIED:" in formatted
    assert "F-Shield : DETECTION / CLASSIFICATION / AUDIT" in formatted
    assert "OS/NTFS  : PHYSICAL ENFORCEMENT" in formatted
    assert "Vault    : PHYSICAL INTEGRITY CONFIRMED" in formatted
    print("[PASS] EXP-26.3-D4: Architectural separation explicitly proven in report:")
    print("-" * 50)
    for line in formatted.splitlines()[-9:]:
        print(line)
    print("-" * 50)

if __name__ == "__main__":
    test_exp_26_3_blocked_operation_forensics()
    print("\n=== EXP-26.3: BLOCKED OPERATION FORENSICS PASSED (100%) ===")
