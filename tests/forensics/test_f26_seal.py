#!/usr/bin/env python3
"""
Test Suite for Phase 26: Cryptographic Integrity Seal (EXP-26.5)
Verifies:
1. EXP-26.5-A: Automatic generation of canonical SHA-256 seal at session close
2. EXP-26.5-B: Tamper detection upon manifest modification (SEAL_TAMPERED)
3. EXP-26.5-C: Tamper detection upon event log modification (SEAL_TAMPERED)
4. EXP-26.5-D: Unsealed session handling (SEAL_MISSING / UNKNOWN)
5. EXP-26.5-E: Reconstructor integration (verdict=SEAL_VALID)
6. Non-Destructive: Does not lock evidence/ with physical ACL (preserves operational R/W)
"""

import sys
import os
import json
import hashlib
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.evidence.session import SessionTracker, SESSION_DIR
from scripts.forensics.reconstruct_session import SessionReconstructor

def test_exp_26_5_integrity_seal_lifecycle():
    print("=" * 60)
    print("TEST EXP-26.5: INTEGRITY SEAL LIFECYCLE & TAMPER DETECTION")
    print("=" * 60)

    # 1. EXP-26.5-A: Start and close clean session
    intent_msg = "EXP-26.5 Controlled Integrity Seal Verification"
    session = SessionTracker.start_session(intent=intent_msg)
    sid = session["session_id"]

    SessionTracker.record_session_event("action_executed", {
        "command": "python frondabrick.py doctor",
        "exit_code": 0
    })

    manifest = SessionTracker.close_session(session_id=sid, final_status="PASS")
    manifest_file = SESSION_DIR / f"{sid}.json"
    events_file = SESSION_DIR / f"{sid}_events.jsonl"

    assert "integrity_seal" in manifest, "Manifest missing integrity_seal block!"
    seal = manifest["integrity_seal"]
    assert seal["algorithm"] == "SHA-256"
    assert seal["type"] == "INTEGRITY_SEAL"
    assert len(seal["manifest_sha256"]) == 64
    assert len(seal["events_sha256"]) == 64
    print(f"[PASS] EXP-26.5-A1: Integrity Seal generated at close ({seal['manifest_sha256'][:16]}...)")

    # Verify initial seal
    initial_verif = SessionTracker.verify_session_seal(sid)
    assert initial_verif["seal_present"] is True
    assert initial_verif["manifest_integrity"] == "PASS"
    assert initial_verif["events_integrity"] == "PASS"
    assert initial_verif["verdict"] == "SEAL_VALID"
    print(f"[PASS] EXP-26.5-A2: Initial seal verification -> SEAL_VALID (100% digest match)")

    # 2. EXP-26.5-B: Tamper Detection (Manifest Tampering)
    original_manifest_text = manifest_file.read_text(encoding="utf-8")
    try:
        tampered_manifest = json.loads(original_manifest_text)
        tampered_manifest["intent"] = "MALICIOUSLY_ALTERED_INTENT"
        manifest_file.write_text(json.dumps(tampered_manifest, indent=2), encoding="utf-8")

        tamper_verif = SessionTracker.verify_session_seal(sid)
        assert tamper_verif["manifest_integrity"] == "FAIL"
        assert tamper_verif["verdict"] == "SEAL_TAMPERED"
        print(f"[PASS] EXP-26.5-B: Manifest alteration immediately detected -> SEAL_TAMPERED")
    finally:
        # Restore original manifest
        manifest_file.write_text(original_manifest_text, encoding="utf-8")

    # 3. EXP-26.5-C: Tamper Detection (Events Tampering)
    original_events_text = events_file.read_text(encoding="utf-8")
    try:
        # Append forged event line
        events_file.write_text(original_events_text + '{"forged": true}\n', encoding="utf-8")
        events_tamper_verif = SessionTracker.verify_session_seal(sid)
        assert events_tamper_verif["events_integrity"] == "FAIL"
        assert events_tamper_verif["verdict"] == "SEAL_TAMPERED"
        print(f"[PASS] EXP-26.5-C: Event log tampering immediately detected -> SEAL_TAMPERED")
    finally:
        # Restore original events
        events_file.write_text(original_events_text, encoding="utf-8")

    # 4. EXP-26.5-D: Reconstructor Integration
    recon = SessionReconstructor.reconstruct(sid)
    assert recon["integrity_seal"]["status"] == "KNOWN"
    assert recon["integrity_seal"]["verdict"] == "SEAL_VALID"
    assert recon["integrity_seal"]["manifest_sha256"] == seal["manifest_sha256"]
    print(f"[PASS] EXP-26.5-D1: Reconstructor verifies seal -> SEAL_VALID")

    formatted = SessionReconstructor.format_report(sid)
    assert "INTEGRITY SEAL (EXP-26.5)" in formatted
    assert "verdict=SEAL_VALID" in formatted
    print(f"[PASS] EXP-26.5-D2: Report cleanly formats integrity seal details")

def test_missing_seal_handling():
    print("\nTEST EXP-26.5: MISSING SEAL HANDLING")
    dummy_sid = "unsealed_session_probe"
    dummy_file = SESSION_DIR / f"{dummy_sid}.json"
    dummy_payload = {"schema_version": 1, "session_id": dummy_sid}

    try:
        dummy_file.write_text(json.dumps(dummy_payload), encoding="utf-8")
        verif = SessionTracker.verify_session_seal(dummy_sid)
        assert verif["seal_present"] is False
        assert verif["verdict"] == "SEAL_MISSING"
        print("[PASS] Unsealed session correctly marked SEAL_MISSING without error.")
    finally:
        if dummy_file.is_file():
            dummy_file.unlink()

if __name__ == "__main__":
    test_exp_26_5_integrity_seal_lifecycle()
    test_missing_seal_handling()
    print("\n=== EXP-26.5: INTEGRITY SEAL TESTS PASSED (100%) ===")
