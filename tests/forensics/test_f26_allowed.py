#!/usr/bin/env python3
"""
Test Suite for Phase 26: Allowed Development Operation Forensics (EXP-26.4)
Verifies the legitimate branch of the causal tree:
1. Start Session with legitimate intent
2. Edit mutable file in src/ (with structured filesystem event)
3. F-Shield evaluates -> ALLOW (Level 1)
4. Execute test suite -> Exit 0 (PASS)
5. EvidenceRecorder correlates test run with session_id
6. Close Session -> Captures Git state & Vault integrity
7. Forensic Reconstruction accurately asserts:
   - F-Shield: ALLOW
   - Filesystem: KNOWN (modified files documented)
   - Tests: KNOWN (PASS)
   - Process / Command: exit 0
   - OS Enforcement: UNKNOWN (no denial, operation legitimate)
   - Recovery: UNKNOWN (no failure occurred)
   - Event Classification: ALLOWED_DEVELOPMENT
"""

import sys
import os
import json
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.evidence.session import SessionTracker, ACTIVE_SESSION_FILE, SESSION_DIR
from scripts.evidence.recorder import EvidenceRecorder
from scripts.forensics.reconstruct_session import SessionReconstructor
from scripts.vault.verifier import VaultVerifier

BASELINE_CANARY_SHA = "0469606ef2fd9aca3debabc5931d56a8cb480fed3b826d22a99d6cc6591891f2"

def test_exp_26_4_allowed_development_forensics():
    print("=" * 60)
    print("TEST EXP-26.4: ALLOWED DEVELOPMENT FORENSICS")
    print("=" * 60)

    # 1. Start Session
    intent_msg = "EXP-26.4 Legitimate Development Forensics Verification"
    session = SessionTracker.start_session(intent=intent_msg)
    sid = session["session_id"]
    print(f"[PASS] EXP-26.4.1: Session started ({sid[:8]}...)")

    # 2. Filesystem change on mutable resource
    probe_file = WORKSPACE_ROOT / "src" / "probe.py"
    original_code = probe_file.read_text(encoding="utf-8")
    addition = "\n# Phase 26 Legitimate Probe Touch\ndef forensic_probe_status():\n    return 'OK'\n"
    probe_file.write_text(original_code + addition, encoding="utf-8")

    # Record structured filesystem change event
    SessionTracker.record_session_event("filesystem_change", {
        "files_changed": ["src/probe.py"],
        "action": "modify"
    })
    print("[PASS] EXP-26.4.2: Mutable file modified and structured filesystem event recorded")

    try:
        # 3. F-Shield Hook evaluation (legitimate test execution)
        test_cmd = f"python tests/core/test_resilience_probe.py"
        hook_payload = {
            "stepIdx": 99991,
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": test_cmd}
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
        assert hook_res["decision"] == "allow", f"Legitimate command was denied: {hook_res}"
        assert hook_res["level"] == 1
        print(f"[PASS] EXP-26.4.3: F-Shield evaluated compliant command -> ALLOW (Level 1)")

        # 4. Command Execution
        test_exec = subprocess.run(
            [sys.executable, str(WORKSPACE_ROOT / "tests" / "core" / "test_resilience_probe.py")],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        assert test_exec.returncode == 0, f"Test execution failed: {test_exec.stderr}"
        SessionTracker.record_session_event("action_executed", {
            "command": test_cmd,
            "exit_code": 0
        })
        print("[PASS] EXP-26.4.4: Legitimate test executed successfully (Exit=0)")

        # 5. EvidenceRecorder persistence
        recorder = EvidenceRecorder(root_dir=WORKSPACE_ROOT / "evidence")
        ev_data = {
            "what": "Ejecución de prueba de resiliencia en desarrollo legítimo",
            "why": "Verificar rama ALLOWED en EXP-26.4",
            "files_changed": ["src/probe.py"],
            "command_executed": test_cmd,
            "result": "PASS",
            "tests_passed": ["test_resilience_probe"],
            "tests_failed": []
        }
        ev_path = recorder.record("tests", ev_data, title="Legitimate Development Run", session_id=sid)
        assert ev_path.is_file()
        print(f"[PASS] EXP-26.4.5: EvidenceRecorder correlated test evidence ({ev_path.name})")

        # 6. Session Close
        manifest = SessionTracker.close_session(session_id=sid, final_status="PASS")
        assert manifest["session_id"] == sid
        assert manifest["vault"]["protection_status"] == "PASS"
        assert manifest["vault"]["canary_sha256"] == BASELINE_CANARY_SHA
        print("[PASS] EXP-26.4.6: Session closed with Vault intact & Git metadata captured")

        # 7. Forensic Reconstruction
        recon = SessionReconstructor.reconstruct(sid)

        # Assert F-Shield ALLOW
        assert recon["f_shield"]["status"] == "KNOWN"
        assert all(e["decision"] == "allow" for e in recon["f_shield"]["events"])
        print("[PASS] EXP-26.4.7a: Reconstructor confirms F-Shield ALLOW")

        # Assert Filesystem KNOWN
        assert recon["filesystem"]["status"] == "KNOWN"
        assert "src/probe.py" in recon["filesystem"]["files_changed"]
        print(f"[PASS] EXP-26.4.7b: Reconstructor confirms Filesystem change ({recon['filesystem']['files_changed']})")

        # Assert Tests KNOWN
        assert recon["tests"]["status"] == "KNOWN"
        assert recon["tests"]["records"][0]["record"]["result"] == "PASS"
        print("[PASS] EXP-26.4.7c: Reconstructor confirms Tests PASS")

        # Assert Vault & Git KNOWN
        assert recon["vault"]["status"] == "KNOWN"
        assert recon["vault"]["drift_detected"] is False
        assert recon["git"]["status"] == "KNOWN"
        print("[PASS] EXP-26.4.7d: Reconstructor confirms Vault & Git integrity")

        # Assert OS Enforcement & Recovery are UNKNOWN (none occurred, no hallucination)
        assert recon["os_enforcement"]["status"] == "UNKNOWN"
        assert recon["recovery"]["status"] == "UNKNOWN"
        print("[PASS] EXP-26.4.7e: Absence of OS block and recovery correctly flagged as UNKNOWN")

        # Assert Formatted Report output
        formatted = SessionReconstructor.format_report(sid)
        assert "EVENT CLASSIFICATION: ALLOWED_DEVELOPMENT" in formatted
        assert "F-Shield  : ALLOW" in formatted
        assert "Execution : UNHINDERED" in formatted
        print("[PASS] EXP-26.4.7f: Report displays EVENT CLASSIFICATION: ALLOWED_DEVELOPMENT:")
        print("-" * 50)
        for line in formatted.splitlines()[-9:]:
            print(line)
        print("-" * 50)

    finally:
        # Revert probe file cleanly
        probe_file.write_text(original_code, encoding="utf-8")

if __name__ == "__main__":
    test_exp_26_4_allowed_development_forensics()
    print("\n=== EXP-26.4: ALLOWED OPERATION FORENSICS PASSED (100%) ===")
