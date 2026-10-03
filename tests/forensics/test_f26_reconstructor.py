#!/usr/bin/env python3
"""
Test Suite for Phase 26: Forensic Reconstructor (EXP-26.2)
Verifies:
1. EXP-26.2-A: Reconstruction of real persisted session without hallucination
2. EXP-26.2-B: Strict detection of evidence gaps (UNKNOWN preservation)
3. EXP-26.2-C: Determinism across multiple reconstruction runs (A == B)
"""

import sys
import os
import json
import uuid
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.forensics.reconstruct_session import SessionReconstructor, SESSION_DIR

KNOWN_SESSION_ID = "136c9cbe-17e1-476b-90bd-80785ca1f41b"

def test_exp_26_2_a_known_session_reconstruction():
    print("=" * 60)
    print("TEST EXP-26.2-A: KNOWN SESSION FORENSIC RECONSTRUCTION")
    print("=" * 60)

    recon = SessionReconstructor.reconstruct(KNOWN_SESSION_ID)

    # 1. Identity & Intent
    assert recon["identity"]["session_id"]["value"] == KNOWN_SESSION_ID
    assert recon["identity"]["final_status"]["value"] == "PASS"
    assert recon["intent"]["status"] == "KNOWN"
    assert recon["intent"]["value"] == "EXP-26.1 Controlled Verification Session"
    print(f"[PASS] Identity & Intent verified: {recon['intent']['value']}")

    # 2. Process
    assert recon["process"]["status"] == "KNOWN"
    assert recon["process"]["pid"]["value"] == 4708
    assert recon["process"]["parent_pid"]["value"] == 2684
    print(f"[PASS] Process PIDs verified: PID={recon['process']['pid']['value']}, PPID={recon['process']['parent_pid']['value']}")

    # 3. F-Shield
    assert recon["f_shield"]["status"] == "KNOWN"
    assert recon["f_shield"]["events_count"] >= 1
    ev0 = recon["f_shield"]["events"][0]
    assert ev0["decision"] == "allow"
    assert ev0["level"] == 1
    print(f"[PASS] F-Shield decision verified: {ev0['decision']} (level {ev0['level']})")

    # 4. Commands & Actions
    assert recon["commands"]["status"] == "KNOWN"
    cmd0 = recon["commands"]["events"][0]
    assert cmd0["data"]["command_hash"] == "511698a1d5204d8b5d7792cc5062983548fbdcbeb8b26d692182e3107482733f"
    assert cmd0["data"]["exit_code"] == 0
    print(f"[PASS] Command hash verified: {cmd0['data']['command_hash'][:16]}... (exit 0)")

    # 5. Tests
    assert recon["tests"]["status"] == "KNOWN"
    rec0 = recon["tests"]["records"][0]["record"]
    assert rec0["result"] == "PASS"
    print(f"[PASS] Tests record verified: {rec0['title']} -> {rec0['result']}")

    # 6. Vault State
    assert recon["vault"]["status"] == "KNOWN"
    assert recon["vault"]["protection_status"] == "PASS"
    assert recon["vault"]["drift_detected"] is False
    assert recon["vault"]["canary_sha256"] == "0469606ef2fd9aca3debabc5931d56a8cb480fed3b826d22a99d6cc6591891f2"
    print(f"[PASS] Vault state verified: protection={recon['vault']['protection_status']}, drift={recon['vault']['drift_detected']}")

    # 7. Git Metadata
    assert recon["git"]["status"] == "KNOWN"
    assert len(recon["git"]["commit"]) == 40
    assert recon["git"]["branch"] == "main"
    print(f"[PASS] Git state verified: commit={recon['git']['commit'][:8]}..., branch={recon['git']['branch']}")

    # 8. Strict UNKNOWN verification
    assert recon["filesystem"]["status"] == "UNKNOWN"
    assert "No existe evidencia estructurada" in recon["filesystem"]["reason"]
    assert recon["recovery"]["status"] == "UNKNOWN"
    assert "No existe evento de recuperación" in recon["recovery"]["reason"]
    print("[PASS] Strict UNKNOWN asserted for filesystem and recovery gaps (no guessing).")

    # 9. Conclusion
    assert "filesystem" in recon["forensic_conclusion"]["unknown_aspects"]
    assert "recovery" in recon["forensic_conclusion"]["unknown_aspects"]
    assert recon["forensic_conclusion"]["fully_reconstructed"] is False
    print("[PASS] Forensic conclusion accurately reports partial coverage with identified gaps.")

def test_exp_26_2_b_gap_detection():
    print("\n" + "=" * 60)
    print("TEST EXP-26.2-B: EVIDENCE GAP DETECTION")
    print("=" * 60)

    gap_sid = f"gap-{uuid.uuid4()}"
    gap_file = SESSION_DIR / f"{gap_sid}.json"

    # Intentionally incomplete manifest (no process, no git, no vault, no intent)
    gap_manifest = {
        "schema_version": 1,
        "session_id": gap_sid,
        "intent": "UNKNOWN",
        "started_at": "UNKNOWN",
        "closed_at": "UNKNOWN",
        "process": {"pid": None, "parent_pid": None},
        "git": {"commit": "UNKNOWN", "branch": "UNKNOWN", "dirty": "UNKNOWN"},
        "vault": {"protection_status": "UNKNOWN"},
        "events": [],
        "f_shield_events": [],
        "evidence_records": [],
        "final_status": "INCOMPLETE"
    }

    try:
        with open(gap_file, "w", encoding="utf-8") as f:
            json.dump(gap_manifest, f)

        recon = SessionReconstructor.reconstruct(gap_sid)

        assert recon["intent"]["status"] == "UNKNOWN"
        assert recon["process"]["status"] == "UNKNOWN"
        assert recon["f_shield"]["status"] == "UNKNOWN"
        assert recon["commands"]["status"] == "UNKNOWN"
        assert recon["filesystem"]["status"] == "UNKNOWN"
        assert recon["tests"]["status"] == "UNKNOWN"
        assert recon["recovery"]["status"] == "UNKNOWN"
        assert recon["vault"]["status"] == "UNKNOWN"
        assert recon["git"]["status"] == "UNKNOWN"

        assert len(recon["forensic_conclusion"]["known_aspects"]) == 0
        assert len(recon["forensic_conclusion"]["unknown_aspects"]) == 9
        print(f"[PASS] All 9 gap aspects recognized as UNKNOWN without hallucination.")
    finally:
        if gap_file.is_file():
            gap_file.unlink()

def test_exp_26_2_c_determinism():
    print("\n" + "=" * 60)
    print("TEST EXP-26.2-C: RECONSTRUCTION DETERMINISM (A == B)")
    print("=" * 60)

    recon_a = SessionReconstructor.reconstruct(KNOWN_SESSION_ID)
    recon_b = SessionReconstructor.reconstruct(KNOWN_SESSION_ID)

    assert recon_a == recon_b, "Reconstruction must be strictly deterministic!"
    print("[PASS] Determinism verified: SessionReconstructor(S) produces identical results across runs.")

if __name__ == "__main__":
    test_exp_26_2_a_known_session_reconstruction()
    test_exp_26_2_b_gap_detection()
    test_exp_26_2_c_determinism()
    print("\n=== EXP-26.2: ALL FORENSIC RECONSTRUCTOR TESTS PASSED ===")
