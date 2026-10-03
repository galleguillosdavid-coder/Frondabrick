#!/usr/bin/env python3
"""
Test Suite for Phase 26: Forensics & Session Correlation (EXP-26.1)
Verifies:
1. session_id generation and persistence
2. F-Shield audit correlation via active session_id
3. EvidenceRecorder correlation via active session_id
4. PID and process metadata capture (or null/UNKNOWN if missing)
5. VaultVerifier state capture at session close
6. Git commit/branch/dirty capture at session close
7. Strict UNKNOWN / null preservation (no fabrications)
"""

import sys
import os
import json
import uuid
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.evidence.session import SessionTracker, ACTIVE_SESSION_FILE, SESSION_DIR
from scripts.evidence.recorder import EvidenceRecorder
from scripts.vault.verifier import VaultVerifier

def test_session_lifecycle_and_correlation():
    print("=" * 60)
    print("TEST EXP-26.1: SESSION CORRELATION LIFECYCLE")
    print("=" * 60)

    intent_desc = "EXP-26.1 Controlled Verification Session"
    session = SessionTracker.start_session(intent=intent_desc)
    sid = session["session_id"]

    # 1. Verify session_id format and persistence
    assert sid and len(sid) == 36, f"Invalid session_id: {sid}"
    assert ACTIVE_SESSION_FILE.is_file(), "Active session file must exist"
    assert ACTIVE_SESSION_FILE.read_text(encoding="utf-8").strip() == sid
    assert os.environ.get("FRONDABRICK_SESSION_ID") == sid
    print(f"[PASS] EXP-26.1.1: session_id generated and persisted ({sid[:8]}...)")

    # 2. Verify PID captured (real, not fabricated)
    pid = session["process"]["pid"]
    assert isinstance(pid, int) and pid > 0, f"Expected valid PID, got {pid}"
    print(f"[PASS] EXP-26.1.2: Real PID captured ({pid})")

    # 3. Verify F-Shield PreToolUse correlation
    # Simulate hook call via validator.py with active session
    fake_payload = {
        "stepIdx": 77777,
        "toolCall": {
            "name": "run_command",
            "arguments": {"CommandLine": "python -c 'print(\"correlation_probe\")'"}
        }
    }
    hook_proc = subprocess.run(
        [sys.executable, str(WORKSPACE_ROOT / "scripts" / "security" / "validator.py")],
        input=json.dumps(fake_payload),
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT)
    )
    assert hook_proc.returncode == 0, f"Validator hook failed: {hook_proc.stderr}"
    hook_res = json.loads(hook_proc.stdout)
    assert hook_res["decision"] == "allow"

    # Check that audit.jsonl recorded the session_id
    audit_file = WORKSPACE_ROOT / "evidence" / "security" / "audit.jsonl"
    assert audit_file.is_file()
    with open(audit_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    matching_audit = [l for l in lines if l.get("stepIdx") == 77777 and l.get("session_id") == sid]
    assert len(matching_audit) >= 1, "F-Shield audit.jsonl did not capture active session_id!"
    print(f"[PASS] EXP-26.1.3: F-Shield audit correlated with session_id ({matching_audit[0]['decision']})")

    # 4. Verify EvidenceRecorder correlation
    recorder = EvidenceRecorder(root_dir=WORKSPACE_ROOT / "evidence")
    test_evidence_data = {
        "what": "Ejecución de acción correlacionada F26.1",
        "why": "Demostrar trazabilidad entre session_id y evidencia registrada",
        "files_changed": [],
        "command_executed": "python -c 'print(1)'",
        "result": "PASS",
        "tests_passed": ["test_sample"],
        "tests_failed": []
    }
    rec_path = recorder.record("tests", test_evidence_data, title="Correlation Probe Run")
    assert rec_path.is_file()
    with open(rec_path, "r", encoding="utf-8") as f:
        saved_ev = json.load(f)
    assert saved_ev.get("session_id") == sid, f"EvidenceRecorder failed to attach session_id: {saved_ev}"
    print(f"[PASS] EXP-26.1.4: EvidenceRecorder correlated with session_id ({rec_path.name})")

    # 5. Record a custom session event with sanitized command hash
    evt = SessionTracker.record_session_event("action_executed", {
        "command": "python tests/core/test_token_counter.py",
        "exit_code": 0
    })
    assert "command_hash" in evt["data"]
    assert evt["session_id"] == sid
    print(f"[PASS] EXP-26.1.5: Session event recorded with command_hash ({evt['event_id']})")

    # 6. Close session and verify manifest
    manifest = SessionTracker.close_session(session_id=sid, final_status="PASS")

    assert manifest["session_id"] == sid
    assert manifest["intent"] == intent_desc
    assert manifest["final_status"] == "PASS"

    # Git checks
    assert manifest["git"]["commit"] != "UNKNOWN" and len(manifest["git"]["commit"]) == 40
    print(f"[PASS] EXP-26.1.6: Git commit captured at close ({manifest['git']['commit'][:8]}...)")

    # Vault checks
    assert manifest["vault"]["protection_status"] == "PASS"
    assert manifest["vault"]["drift_detected"] is False
    assert manifest["vault"]["canary_sha256"] == "0469606ef2fd9aca3debabc5931d56a8cb480fed3b826d22a99d6cc6591891f2"
    print(f"[PASS] EXP-26.1.7: Vault state captured at close (protection=PASS, drift=False)")

    # Correlated events checks
    assert len(manifest["f_shield_events"]) >= 1
    assert len(manifest["evidence_records"]) >= 1
    assert not ACTIVE_SESSION_FILE.is_file(), "Active session file should be cleaned up"
    print(f"[PASS] EXP-26.1.8: Session sealed in evidence/session/{sid}.json")

def test_missing_data_returns_unknown_or_null():
    print("\nTEST EXP-26.1: UNKNOWN / NULL ENFORCEMENT")
    dummy_sid = f"dummy-{uuid.uuid4()}"
    manifest = SessionTracker.close_session(session_id=dummy_sid, final_status="INCOMPLETE")

    # Check strict adherence to UNKNOWN / null
    assert manifest["intent"] == "UNKNOWN"
    assert manifest["started_at"] == "UNKNOWN"
    assert manifest["process"]["pid"] is None

    # Clean up dummy test file
    dummy_file = SESSION_DIR / f"{dummy_sid}.json"
    if dummy_file.is_file():
        dummy_file.unlink()

    print("[PASS] Absence of prior session data strictly yields UNKNOWN / null (no fabrication).")

if __name__ == "__main__":
    test_session_lifecycle_and_correlation()
    test_missing_data_returns_unknown_or_null()
    print("\n=== EXP-26.1: ALL CORRELATION TESTS PASSED ===")
